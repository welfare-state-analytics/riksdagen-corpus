"""
Find margin notes with a date in protocols and include them as metadata.
"""
from lxml import etree
import pandas as pd
import os
import progressbar
import argparse

from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.refine import detect_date
from pyriksdagen.utils import infer_metadata, protocol_iterators

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)
    for protocol_path in progressbar.progressbar(list(protocol_iterators("corpus/", start=args.start, end=args.end))):
        metadata = infer_metadata(protocol_path)
        root = etree.parse(protocol_path, parser)
        root, dates = detect_date(root, metadata)
        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )

        f = open(protocol_path, "wb")
        f.write(b)
        f.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=1920, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    args = parser.parse_args()
    main(args)
