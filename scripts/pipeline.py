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
    detect_date,
)
from pyriksdagen.utils import (
    protocol_iterators,
    infer_metadata,
)


def main(args):
    file_dbs = []
    if args.scanned:
        file_dbs.append(pd.read_csv("input/protocols/scanned.csv"))
    if args.digital_originals:
        file_dbs.append(pd.read_csv("input/protocols/digital_originals.csv"))
    file_db = pd.concat(file_dbs)
    file_db = file_db[file_db["year"] >= args.start]
    file_db = file_db[file_db["year"] <= args.end]

    print(file_db)

    archive = LazyArchive()

    # Create parla-clarin files
    parlaclarin_workflow_individual(
        file_db, archive
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--scanned", action="store_true", help="Set this flag for protocols that were scanned.")
    parser.add_argument("-d", "--digital_originals", action="store_true", help="Set this flag for born-digital protocols.")
    parser.add_argument("-s", "--start", type=int, default=1920, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    args = parser.parse_args()
    if args.scanned == args.digital_originals:
        print("\nSet either -i or -d, but not both.\n")
        parser.print_help()
    else:
        main(args)
