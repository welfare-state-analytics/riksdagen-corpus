"""
Run the classification into utterances and notes.
"""
from pyparlaclarin.refine import reclassify, format_texts, random_classifier

from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.utils import infer_metadata, protocol_iterators
from lxml import etree
import pandas as pd
import os, progressbar, sys
import argparse

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)

    for protocol_path in progressbar.progressbar(list(protocol_iterators("corpus/", start=args.start, end=args.end))):
        metadata = infer_metadata(protocol_path)
        root = etree.parse(protocol_path, parser).getroot()

        root = reclassify(root, random_classifier, exclude=["date", "speaker"])
        root = format_texts(root)
        b = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        f = open(protocol_path, "wb")
        f.write(b)
        f.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
