"""
Download alto XMLs from KB, convert them to parlaclarin. Saves raw data
on disk if you want to rerun the script. 
"""
import pandas as pd
import progressbar
from lxml import etree
import argparse
from pyparlaclarin.refine import (
    format_texts,
)

from pyriksdagen.download import LazyArchive
from pyriksdagen.export import parlaclarin_workflow_individual
from pyriksdagen.db import load_patterns
from pyriksdagen.refine import (
    detect_mps,
    find_introductions,
    update_ids,
    update_hashes,
    detect_date,
)
from pyriksdagen.utils import (
    protocol_iterators,
    infer_metadata,
)


def main(args):
    file_dbs = []
    file_dbs.append(pd.read_csv("input/protocols/scanned.csv"))
    file_dbs.append(pd.read_csv("input/protocols/digital_originals.csv"))
    file_db = pd.concat(file_dbs)

    start_year = args.start
    end_year = args.end

    print("Process files from", start_year, "to", end_year)

    file_db = file_db[file_db["year"] >= start_year]
    file_db = file_db[file_db["year"] <= end_year]
    print(file_db)

    mp_db = pd.read_csv("corpus/members_of_parliament.csv")
    archive = LazyArchive()

    # Create parla-clarin files
    parlaclarin_workflow_individual(
        file_db, archive
    )

    # Run additional steps:
    # 1
    parser = etree.XMLParser(remove_blank_text=True)
    for protocol_path in protocol_iterators("corpus/", start=args.start, end=args.end):
        protocol_path = str(protocol_path)
        metadata = infer_metadata(protocol_path)
        root = etree.parse(protocol_path, parser).getroot()
        root, _ = detect_date(root, metadata)
        root = format_texts(root)
        root = update_hashes(root, metadata["protocol"])
        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )

        f = open(protocol_path, "wb")
        f.write(b)
        f.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
