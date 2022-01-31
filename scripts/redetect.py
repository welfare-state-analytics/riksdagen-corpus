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

def main(args):
    start_year = args.start
    end_year = args.end
    root = ""  # "../"
    pc_folder = root + "corpus/"
    folders = os.listdir(pc_folder)
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
    observation = pd.read_csv('corpus/wiki-data/observation.csv')
    individual = pd.read_csv('corpus/wiki-data/individual.csv')
    party = pd.read_csv('corpus/wiki-data/party.csv')

    # Impute missing party values with unique individual level values
    idx = observation["party_abbrev"].isnull()
    missing = observation.loc[idx]
    missing = missing.reset_index().merge(party, on='wiki_id', how='left').set_index('index')
    missing.rename(columns={'party_abbrev_y':'party_abbrev'}, inplace=True)
    missing = missing.drop(["party_abbrev_x"], axis=1)
    observation.loc[idx, "party_abbrev"] = missing["party_abbrev"]

    # Remove 1. dots, 2. (text), 3. j:r, 4. specifier, 5. make lowercase
    observation["name"] = observation["name"].str.replace('.', '', regex=False)
    observation["name"] = observation["name"].str.replace(r" \((.+)\)", '', regex=True)
    observation["name"] = observation["name"].str.replace(r" [a-zA-ZÀ-ÿ]:[a-zA-ZÀ-ÿ]", '', regex=True)
    observation["name"] = observation["name"].str.replace(r"i [a-zA-ZÀ-ÿ]+", '', regex=True)
    observation["name"] = observation["name"].str.lower()

    # Add end date to observations currently in office
    idx = observation["end"].isna()
    if sum(idx) != 349: print(f'Warning: {sum(idx)} observations currently in office.')
    observation.loc[idx, "end"] = '2022-12-31' 
    observation["start"] = observation["start"].str[:4].astype(int)
    observation["end"] = observation["end"].str[:4].astype(int)

    # Add gender
    observation = observation.reset_index().merge(individual[["wiki_id", "gender"]], on='wiki_id', how='left').set_index('index')
    if len(set(observation["gender"])) != 2:
        print('More than 2 genders or missing values.')

    # Test, change id column name
    observation["id"] = observation["wiki_id"]

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
                        wiki_db=observation,
                        mp_db=year_mp_db,
                        minister_db=year_ministers,
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
