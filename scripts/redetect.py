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
from pyriksdagen.utils import infer_metadata, parse_date
from pyriksdagen.match_mp import clean_names

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

    ### Wikidata
    # Ministers
    wiki_minister_db = pd.read_csv('corpus/ministers_w.csv')
    wiki_minister_db["start"] = pd.to_datetime(wiki_minister_db["start"], errors="coerce")
    wiki_minister_db["end"] = pd.to_datetime(wiki_minister_db["end"], errors="coerce")

    # Speakers
    wiki_speaker_db = pd.read_csv(root + "corpus/speakers_w.csv")
    wiki_speaker_db["start"] = pd.to_datetime(wiki_speaker_db["start"], errors="coerce")
    wiki_speaker_db["end"] = pd.to_datetime(wiki_speaker_db["end"], errors="coerce")

    # Members
    wiki_db = pd.read_csv('corpus/members_of_parliament_w.csv')
    wiki_db["start"] = pd.to_datetime(wiki_db["start"], errors="coerce")
    wiki_db["end"] = pd.to_datetime(wiki_db["end"], errors="coerce")

    # Remove 1. dots, 2. (text), 3. j:r, 4. specifier, 5. make lowercase
    wiki_db["name"] = wiki_db["name"].str.replace('.', '', regex=False)
    wiki_db["name"] = wiki_db["name"].str.replace(r" \((.+)\)", '', regex=True)
    wiki_db["name"] = wiki_db["name"].str.replace(r" [a-zA-ZÀ-ÿ]:[a-zA-ZÀ-ÿ]", '', regex=True)
    wiki_db["name"] = wiki_db["name"].str.replace(r"i [a-zA-ZÀ-ÿ]+", '', regex=True)
    wiki_db["name"] = wiki_db["name"].str.lower()

    # Drop wiki_db entries with no startdate
    wiki_db = wiki_db.loc[~wiki_db["start"].isna()].reset_index(drop=True)

    # Add end date to wiki_dbs currently in office
    idx = wiki_db["end"].isna()
    idy = wiki_db["start"] > datetime.strptime('2014-01-01', '%Y-%m-%d')
    idx = [i for i in idx if i in idy]
    if len(set((wiki_db.loc[idx, "wiki_id"]))) != 349: print(f'Warning: {sum(idx)} observations currently in office.')
    wiki_db.loc[idx, "end"] = '2022-12-31' 
    wiki_db = wiki_db.loc[~wiki_db["end"].isna()].reset_index(drop=True)

    # Could probably keep datetime format
    wiki_db["start"] = pd.DatetimeIndex(wiki_db['start']).year.astype(int)
    wiki_db["end"] = pd.DatetimeIndex(wiki_db['end']).year.astype(int)

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
