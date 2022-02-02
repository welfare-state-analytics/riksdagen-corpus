"""
Connect introductions to the speaker in the metadata.
"""
from lxml import etree
import pandas as pd
import json
import os, progressbar, argparse
from datetime import datetime
from pyparlaclarin.refine import (
    format_texts,
)

from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.refine import (
    detect_mps,
    find_introductions,
    update_ids,
    update_hashes,
)
from pyriksdagen.utils import infer_metadata
from pyriksdagen.match_mp import clean_names

def parse_date(s):
    """
    Parse datetimes with special error handling
    """
    try:
        return datetime.strptime(s, "%Y-%m-%d")

    except ValueError:
        if len(s) == 4:
            if int(s) > 1689 and int(s) < 2261:
                return datetime(int(s), 6, 15)
            else:
                return None
        else:
            return None

def load_ministers(path):
    '''Unpacks very nested minister.json file to a df.'''
    with open('corpus/wiki-data/minister.json', 'r') as f:
        minister = json.load(f)

    data = []
    for gov in minister:
        g = gov["government"]
        for member in gov["cabinet"]:
            Q = member["wiki_id"]
            n = member["name"]
            for pos in member["positions"]:
                r = pos["role"]
                s = pos["start"]
                e = pos["end"]
                data.append([g, Q, n, r, s, e])
    minister = pd.DataFrame(data, columns=["government", "wiki_id", "name", "role", "start", "end"])
    return minister

def main(args):
    start_year = args.start
    end_year = args.end
    root = ""  # "../"
    pc_folder = root + "corpus/"
    folders = [f for f in os.listdir(pc_folder) if f.isnumeric()]
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"

    with open("corpus/party_mapping.json") as f:
        party_map = json.load(f)

    mp_db = pd.read_csv(root + "corpus/members_of_parliament.csv")
    mp_db["name"] = clean_names(mp_db["name"])
    sk_db = pd.read_csv(root + "corpus/members_of_parliament_sk.csv")
    sk_db["name"] = clean_names(sk_db["name"])
    minister_db = pd.read_csv(root + "corpus/ministers.csv", parse_dates=True)
    minister_db["start"] = pd.to_datetime(minister_db["start"], errors="coerce")
    minister_db["end"] = pd.to_datetime(minister_db["end"], errors="coerce")
    talman_db = pd.read_csv(root + "corpus/talman.csv")
    talman_db["start"] = pd.to_datetime(talman_db["start"], errors="coerce")
    talman_db["end"] = pd.to_datetime(talman_db["end"], errors="coerce")

    ### Preprocess observation level wiki dataset
    wiki_db = pd.read_csv('corpus/wiki-data/observation.csv')
    individual = pd.read_csv('corpus/wiki-data/individual.csv')
    party = pd.read_csv('corpus/wiki-data/party.csv')
    with open('corpus/wiki-data/name.json', 'r') as f:
        name = json.load(f)

    # Test replacing previous minister file
    wiki_minister_db = load_ministers('corpus/wiki-data/minister.json')
    wiki_minister_db["start"] = pd.to_datetime(wiki_minister_db["start"], errors="coerce")
    wiki_minister_db["end"] = pd.to_datetime(wiki_minister_db["end"], errors="coerce")
    wiki_minister_db["id"] = wiki_minister_db["wiki_id"]

    # Impute missing party values with unique individual level values
    idx = wiki_db["party_abbrev"].isnull()
    missing = wiki_db.loc[idx]
    missing = missing.reset_index().merge(party, on='wiki_id', how='left').set_index('index')
    missing.rename(columns={'party_abbrev_y':'party_abbrev'}, inplace=True)
    missing = missing.drop(["party_abbrev_x"], axis=1)
    wiki_db.loc[idx, "party_abbrev"] = missing["party_abbrev"]

    # Remove 1. dots, 2. (text), 3. j:r, 4. specifier, 5. make lowercase
    wiki_db["name"] = wiki_db["name"].str.replace('.', '', regex=False)
    wiki_db["name"] = wiki_db["name"].str.replace(r" \((.+)\)", '', regex=True)
    wiki_db["name"] = wiki_db["name"].str.replace(r" [a-zA-ZÀ-ÿ]:[a-zA-ZÀ-ÿ]", '', regex=True)
    wiki_db["name"] = wiki_db["name"].str.replace(r"i [a-zA-ZÀ-ÿ]+", '', regex=True)
    wiki_db["name"] = wiki_db["name"].str.lower()

    # Add end date to wiki_dbs currently in office
    idx = wiki_db["end"].isna()
    if sum(idx) != 349: print(f'Warning: {sum(idx)} observations currently in office.')
    wiki_db.loc[idx, "end"] = '2022-12-31' 
    wiki_db["start"] = wiki_db["start"].str[:4].astype(int)
    wiki_db["end"] = wiki_db["end"].str[:4].astype(int)

    # Add gender
    wiki_db = wiki_db.reset_index().merge(individual[["wiki_id", "gender"]], on='wiki_id', how='left').set_index('index')
    if len(set(wiki_db["gender"])) != 2:
        print('More than 2 genders or missing values.')

    # Add specifier
    wiki_db["specifier"] = pd.Series(str)
    for key, values in name.items():
        if key in wiki_db["wiki_id"].tolist():
            for value in values:
                if ' i ' in value:
                    wiki_db.loc[wiki_db["wiki_id"] == key, "specifier"] = value.split(' i ')[-1]
                    break

    # Test, change id column name
    wiki_db["id"] = wiki_db["wiki_id"]

    parser = etree.XMLParser(remove_blank_text=True)

    for outfolder in progressbar.progressbar(sorted(folders)):
        if os.path.isdir(pc_folder + outfolder):
            outfolder = outfolder + "/"
            protocol_ids = os.listdir(pc_folder + outfolder)
            protocol_ids = [
                protocol_id.replace(".xml", "")
                for protocol_id in protocol_ids
                if protocol_id.split(".")[-1] == "xml"
            ]

            first_protocol_id = protocol_ids[0]
            metadata = infer_metadata(first_protocol_id)
            year = metadata["year"]
            if year >= start_year and year <= end_year:
                for protocol_id in progressbar.progressbar(protocol_ids):
                    metadata = infer_metadata(protocol_id)
                    filename = pc_folder + outfolder + protocol_id + ".xml"
                    root = etree.parse(filename, parser).getroot()

                    years = [
                        int(elem.attrib.get("when").split("-")[0])
                        for elem in root.findall(tei_ns + "docDate")
                    ]

                    if not year in years:
                        year = years[0]
                    print("Year", year)
                    if str(year) not in protocol_id:
                        print(protocol_id, year)
                    year_mp_db = filter_db(mp_db, year=year)
                    year_sk_db = sk_db[sk_db["year"] == year]
                    year_obs_db = filter_db(wiki_db, year=year)
                    
                    dates = [
                        parse_date(elem.attrib.get("when"))
                        for elem in root.findall(tei_ns + "docDate")
                    ]
                    start_date, end_date = min(dates), max(dates)

                    # Convert start and end dates into datetimes
                    # Fails for pre-1600s and post-2200s dates
                    try:
                        year_ministers = minister_db[minister_db["start"] < start_date]
                        year_ministers = year_ministers[
                            year_ministers["end"] > end_date
                        ]
                    except pd.errors.OutOfBoundsDatetime:
                        print("Unreasonable date in:", protocol_id)
                        print(start_date)
                        print(end_date)
                        year_ministers = minister_db[minister_db.columns]

                    # Switch minister year filtering to be based on government periods
                    try:
                        year_wiki_minister = wiki_minister_db[wiki_minister_db["start"] < start_date]
                        year_wiki_minister = year_wiki_minister[
                            year_wiki_minister["end"] > end_date
                        ]
                    except pd.errors.OutOfBoundsDatetime:
                        print("Unreasonable date in:", protocol_id)
                        print(start_date)
                        print(end_date)
                        year_wiki_minister = wiki_minister_db[wiki_minister_db.columns]

                    metadata["start_date"] = start_date
                    metadata["end_date"] = end_date

                    pattern_db = load_patterns()
                    pattern_db = pattern_db[
                        (pattern_db["start"] <= year) & (pattern_db["end"] >= year)
                    ]
                    #print(year_mp_db)
                    root = detect_mps(
                        root,
                        None,
                        pattern_db,
                        wiki_db=year_obs_db,
                        mp_db=year_mp_db,
                        minister_db=year_ministers,
                        wiki_minister_db=year_wiki_minister,
                        speaker_db=talman_db,
                        sk_db=year_sk_db,
                        metadata=metadata,
                        party_map=party_map,
                    )
                    root = update_hashes(root, protocol_id)
                    b = etree.tostring(
                        root, pretty_print=True, encoding="utf-8", xml_declaration=True
                    )

                    f = open(filename, "wb")
                    f.write(b)
                    f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
