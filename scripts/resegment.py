"""
Find undetected introductions in the protocols. After finding an intro,
tag the next paragraph as an utterance.
"""
from pyparlaclarin.refine import format_texts
from pyriksdagen.db import load_patterns
from pyriksdagen.refine import (
    detect_mps,
    find_introductions,
    update_ids,
    update_hashes,
)
from pyriksdagen.utils import infer_metadata
from pyriksdagen.utils import protocol_iterators

from lxml import etree
import pandas as pd
import os, progressbar, argparse

def main(args):
    start_year = args.start
    end_year = args.end

    parser = etree.XMLParser(remove_blank_text=True)
    for protocol in progressbar.progressbar(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end))):
        metadata = infer_metadata(protocol)
        protocol_id = protocol.split("/")[-1]
        year = metadata["year"]
        root = etree.parse(protocol, parser).getroot()

        years = [
            int(elem.attrib.get("when").split("-")[0])
            for elem in root.findall(
                ".//{http://www.tei-c.org/ns/1.0}docDate"
            )
        ]

        if not year in years:
            year = years[0]
        
        pattern_db = load_patterns()
        pattern_db = pattern_db[
            (pattern_db["start"] <= year) & (pattern_db["end"] >= year)
        ]
        root = find_introductions(root, pattern_db, names_ids=None, minister_db=None)
        root = update_ids(root, protocol_id)
        root = format_texts(root)
        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )

        f = open(protocol, "wb")
        f.write(b)
        f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
