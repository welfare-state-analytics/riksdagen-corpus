"""
Connect introductions to the speaker in the metadata.
"""
from lxml import etree
import pandas as pd
import json, math
import os, progressbar, argparse
from datetime import datetime
from pyparlaclarin.refine import (
    format_texts,
)

from pyriksdagen.db import filter_db, load_patterns, load_metadata
from pyriksdagen.refine import (
    detect_mps,
    find_introductions,
    update_ids,
    update_hashes,
)
from pyriksdagen.utils import infer_metadata, parse_date
from pyriksdagen.utils import protocol_iterators
from pyriksdagen.match_mp import clean_names

def main(args):
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
    party_mapping, mp_db, minister_db, speaker_db = load_metadata()

    unknown_variables = ["gender", "party", "other"]
    unknowns = []
    parser = etree.XMLParser(remove_blank_text=True)

    for protocol in progressbar.progressbar(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end))):
        protocol_id = protocol.split("/")[-1]
        metadata = infer_metadata(protocol)
        root = etree.parse(protocol, parser).getroot()
        
        # Year from the folder name
        year = metadata["year"]
        # Take into account folders such as 198889
        secondary_year = metadata.get("secondary_year", year)

        dates = [
            parse_date(elem.attrib.get("when"))
            for elem in root.findall(tei_ns + "docDate")
            if parse_date(elem.attrib.get("when")).year in [year, secondary_year]
        ]
        
        # Dates from xml is wrong for digitized era
        if len(dates) > 0:
            start_date, end_date = min(dates), max(dates)           
        else:
            start_date = datetime(year,1,1)
            end_date = datetime(secondary_year,12,31)
        
        year_mp_db = filter_db(mp_db, start_date=start_date, end_date=end_date)
        year_minister_db = filter_db(minister_db, start_date=start_date, end_date=end_date)
        year_speaker_db = filter_db(speaker_db, start_date=start_date, end_date=end_date)
        
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
        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )

        f = open(protocol, "wb")
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
