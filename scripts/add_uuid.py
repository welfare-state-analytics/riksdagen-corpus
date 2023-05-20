"""
Add a randomly generated UUID to all elements in the XML ID field that are currently missing one.
"""
from lxml import etree
import pandas as pd
import json, math
import os, argparse
from datetime import datetime
from pyparlaclarin.refine import (
    format_texts,
)

from pyriksdagen.db import filter_db, load_patterns, load_metadata
from pyriksdagen.refine import (
    redetect_protocol,
    detect_mps,
    find_introductions,
    update_ids,
)
from pyriksdagen.utils import infer_metadata, parse_date, elem_iter, protocol_iterators, get_formatted_uuid
from pyriksdagen.match_mp import clean_names, multiple_replace
from tqdm import tqdm
import multiprocessing
import uuid
import base58

def add_protocol_id(protocol):
    ids = set()
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()
    
    tei = root.find(f"{tei_ns}TEI")
    tei.attrib[f"{xml_ns}id"] = protocol.split("/")[-1][:-4]

    num_ids = 0
    for tag, elem in elem_iter(root):
        if tag == "u":
            for subelem in elem:
                x = subelem.attrib.get(f'{xml_ns}id', get_formatted_uuid())
                subelem.attrib[f'{xml_ns}id'] = x
                ids.add(x)
                num_ids += 1
            x = elem.attrib.get(f'{xml_ns}id', get_formatted_uuid())
            elem.attrib[f'{xml_ns}id'] = x
            ids.add(x)
            num_ids += 1
                
        elif tag in ["note"]:
            x = elem.attrib.get(f'{xml_ns}id', get_formatted_uuid())
            elem.attrib[f'{xml_ns}id'] = x
            ids.add(x)
            num_ids += 1

    b = etree.tostring(
        root, pretty_print=True, encoding="utf-8", xml_declaration=True
    )
    f = open(protocol, "wb")
    f.write(b)

    assert len(ids) == num_ids
    return ids, num_ids


def main(args):
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
    num_ids = 0
    ids = []
    with multiprocessing.Pool() as pool:
        for i, n in tqdm(pool.imap(add_protocol_id, protocols), total=len(protocols)):
            ids += i
            num_ids += n

        assert len(set(ids)) == num_ids


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=1920, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    args = parser.parse_args()
    main(args)
