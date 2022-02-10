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

from pyriksdagen.db import load_patterns
from pyriksdagen.refine import (
    detect_mps,
    find_introductions,
    update_ids,
    update_hashes,
)
from pyriksdagen.utils import infer_metadata, parse_date
from pyriksdagen.match_mp import clean_names

# New filter db function
def filter_db(db, start_date, end_date):
    idx = (db["start"] <= start_date) & (db["end"] >= start_date)
    idy = (db["start"] <= end_date) & (db["end"] >= end_date)
    return db[idx+idy]

def main(args):
    start_year = args.start
    end_year = args.end
    root = ""  # "../"
    pc_folder = root + "corpus/"
    folders = [f for f in os.listdir(pc_folder) if f.isnumeric()]
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"

    with open("corpus/party_mapping.json") as f:
        party_map = json.load(f)
    mp_db = pd.read_csv('input/matching/member.csv')
    minister_db = pd.read_csv('input/matching/minister.csv')
    speaker_db = pd.read_csv('input/matching/speaker.csv')

    # Clean names
    mp_db["name"] = mp_db["name"].apply(clean_names)
    minister_db["name"] = minister_db["name"].apply(clean_names)
    speaker_db["name"] = speaker_db["name"].apply(clean_names)

    # Datetime format
    mp_db[["start", "end"]] = mp_db[["start", "end"]].apply(pd.to_datetime, errors="coerce")
    minister_db[["start", "end"]] = minister_db[["start", "end"]].apply(pd.to_datetime, errors="coerce")
    speaker_db[["start", "end"]] = speaker_db[["start", "end"]].apply(pd.to_datetime, errors="coerce")

    # Map party_abbrev and chamber
    mp_db["party_abbrev"] = mp_db["party"].map(party_map)
    mp_db["chamber"] = mp_db["role"].map({'ledamot':'Enkammarriksdagen',
                                             'förstakammarledamot':'Första kammaren',
                                             'andrakammarledamot':'Andra kammaren'})

    ### Temporary
    # Use wiki_id for id for now
    mp_db["id"] = mp_db["wiki_id"]
    minister_db["id"] = minister_db["wiki_id"]
    speaker_db["id"] = speaker_db["wiki_id"]
    mp_db["specifier"] = mp_db["location"]

    # Potentially use government for filtering ministers
    #government = pd.read_csv('corpus/government.csv')
    #government[["start", "end"]] = government[["start", "end"]].apply(pd.to_datetime, errors="coerce")
    #government.loc[government["start"] == max(government["start"]), "end"] = datetime.strptime('2022-12-31', '%Y-%m-%d')

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

                    # What is this for?
                    #if not year in years:
                    #    year = years[0]
                    #    print("Year", year)
                    #if str(year) not in protocol_id:
                    #    print(protocol_id, year)
                    
                    dates = [
                        parse_date(elem.attrib.get("when"))
                        for elem in root.findall(tei_ns + "docDate")
                    ]
                    start_date, end_date = min(dates), max(dates)

                    # Convert start and end dates into datetimes
                    # Fails for pre-1600s and post-2200s dates
                    try:
                        year_mp_db = filter_db(mp_db, start_date, end_date)
                        year_minister_db = filter_db(minister_db, start_date, end_date)
                        year_speaker_db = filter_db(speaker_db, start_date, end_date)

                    except pd.errors.OutOfBoundsDatetime:
                        print("Unreasonable date in:", protocol_id)
                        print(start_date)
                        print(end_date)

                    metadata["start_date", "end_date"] = start_date, end_date

                    # Introduction patterns
                    pattern_db = load_patterns()
                    pattern_db = pattern_db[
                        (pattern_db["start"] <= year) & (pattern_db["end"] >= year)
                    ]

                    root = detect_mps(
                        root,
                        None,
                        pattern_db,
                        mp_db=year_mp_db,
                        minister_db=year_minister_db,
                        speaker_db=year_speaker_db,
                        metadata=metadata,
                        party_map=party_map,
                    )
#                    root = update_hashes(root, protocol_id)
#                    b = etree.tostring(
#                        root, pretty_print=True, encoding="utf-8", xml_declaration=True
#                    )
#
#                    f = open(filename, "wb")
#                    f.write(b)
#                    f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
