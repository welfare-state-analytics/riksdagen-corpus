"""
Connect introductions to the speaker in the metadata.
"""
from lxml import etree
import pandas as pd
import os, progressbar, argparse
from datetime import datetime
from pyparlaclarin.read import (
    paragraph_iterator
)
from pyparlaclarin.refine import (
    format_texts,
)

from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.segmentation import (
    detect_mp_new
)
from pyriksdagen.refine import (
    detect_mps,
    find_introductions,
    update_ids,
    update_hashes,
)
from pyriksdagen.utils import infer_metadata, protocol_iterators
import numpy as np
import re

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
    found = {}
    start_year = args.start
    end_year = args.end
    tei_ns = "{http://www.tei-c.org/ns/1.0}"
    patterns = pd.read_json("input/segmentation/detection.json", orient="records", lines=True)
    expressions = []

    for _, pattern in patterns.iterrows():
        exp, t = pattern["pattern"], pattern["type"]
        print(exp, t)
        exp = re.compile(exp)
        expressions.append((exp, t))

        print(exp.findall("Herr GUSTAFSSON i Skellefteå (fp):"))
        print(exp.match("Herr GUSTAFSSON i Skellefteå (fp):"))
        print(exp)

    parser = etree.XMLParser(remove_blank_text=True)
    for protocol in progressbar.progressbar(list(protocol_iterators("corpus/", start=args.start, end=args.end))):
        metadata = infer_metadata(protocol)
        protocol_id = metadata["protocol"]
        root = etree.parse(protocol, parser).getroot()

        years = [
            int(elem.attrib.get("when").split("-")[0])
            for elem in root.findall(".//" + tei_ns + "docDate")
        ]

        dates = [
            parse_date(elem.attrib.get("when"))
            for elem in root.findall(".//" + tei_ns + "docDate")
        ]
        start_date, end_date = min(dates), max(dates)

        for elem in paragraph_iterator(root, output="lxml"):
            if elem.tag == tei_ns + "note":
                note = elem
                if note.attrib.get("type") == "speaker":
                    note_text = note.text
                    row = detect_mp_new(note_text, expressions)
                    if len(row) >= 1:
                        print(note_text.strip())
                        print(row)
                        print()
                    if "name" in row:
                        found["name"] = found.get("name", np.zeros(2)) + np.array([1,0])
                    else:
                        found["name"] = found.get("name", np.zeros(2)) + np.array([0,1])
    print(found["name"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
