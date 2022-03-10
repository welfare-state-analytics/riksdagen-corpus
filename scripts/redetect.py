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

def filter_db(db, date, *args):
    '''Filters db with start-end dates containing at least 1 date'''
    date = [date]
    for d in args:
        date.append(d)
    indices = pd.Series([False]*len(db))
    for d in date:
        indices += (db["start"] <= d) & (db["end"] >= d)    
    return db[indices]

def main(args):
    start_year = args.start
    end_year = args.end
    root = ""  # "../"
    pc_folder = root + "corpus/protocols/"
    folders = [f for f in os.listdir(pc_folder) if f.isnumeric()]
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"

    party_mapping = pd.read_csv('corpus/metadata/party_abbreviation.csv')
    mp_db = pd.read_csv('input/matching/member_of_parliament.csv')
    minister_db = pd.read_csv('input/matching/minister.csv')
    speaker_db = pd.read_csv('input/matching/speaker.csv')

    ### Temporary colname changes
    mp_db["specifier"] = mp_db["location"]
    mp_db = mp_db.rename(columns={'person_id':'id'})
    minister_db = minister_db.rename(columns={'person_id':'id'})
    speaker_db = speaker_db.rename(columns={'person_id':'id'})

    # Datetime format
    mp_db[["start", "end"]] = mp_db[["start", "end"]].apply(pd.to_datetime, errors="coerce")
    minister_db[["start", "end"]] = minister_db[["start", "end"]].apply(pd.to_datetime, errors="coerce")
    speaker_db[["start", "end"]] = speaker_db[["start", "end"]].apply(pd.to_datetime, errors="coerce")

    unknown_variables = ["gender", "party", "other"]
    unknowns = []
    parser = etree.XMLParser(remove_blank_text=True)

    for outfolder in sorted(folders):
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
                    
                    dates = [
                        parse_date(elem.attrib.get("when"))
                        for elem in root.findall(tei_ns + "docDate")
                    ]
                    
                    # Dates from xml is wrong for digitized era
                    start_date, end_date = min(dates), max(dates)           
                    
                    year_mp_db = filter_db(mp_db, start_date, end_date)
                    year_minister_db = filter_db(minister_db, start_date, end_date)
                    year_speaker_db = filter_db(speaker_db, start_date, end_date)

                    # Introduction patterns
                    pattern_db = load_patterns()
                    pattern_db = pattern_db[
                        (pattern_db["start"] <= year) & (pattern_db["end"] >= year)
                    ]

                    root, unk = detect_mps(
                        root,
                        None,
                        pattern_db,
                        mp_db=year_mp_db,
                        minister_db=year_minister_db,
                        speaker_db=year_speaker_db,
                        metadata=metadata,
                        party_map=party_mapping,
                        protocol_id=protocol_id,
                        unknown_variables=unknown_variables,
                    )

                    unknowns.extend(unk)
    
                    root = update_hashes(root, protocol_id)
                    b = etree.tostring(
                        root, pretty_print=True, encoding="utf-8", xml_declaration=True
                    )

                    f = open(filename, "wb")
                    f.write(b)
                    f.close()
    unknowns = pd.DataFrame(unknowns, columns=['protocol_id', 'hash']+unknown_variables)
    print('Proportion of metadata identified for unknowns:')
    print((unknowns[["gender", "party", "other"]] != '').sum() / len(unknowns))
    unknowns.drop_duplicates().to_csv('input/matching/unknowns.csv', index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
