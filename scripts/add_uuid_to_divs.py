#!/usr/bin/env python3
"""
adds uuid elem to any <div> that doesn't already have one.
"""
from lxml import etree
from pyriksdagen.utils import (
    protocol_iterators,
    get_formatted_uuid,
)
from tqdm import tqdm
import argparse, multiprocessing
from pathlib import Path



def add_div_ids(protocol):
    ids = set()
    num_ids = 0
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()

    body = root.find(f"{tei_ns}body")
    if body is None:
        print(protocol)
    else:
        divs = body.findall(f"{tei_ns}div")
        #print(len(divs), protocol)
        for div in divs:
            protocol_id = Path(protocol).stem
            seed_str = f"{protocol_id}\n{' '.join(div.itertext())}"
            x = div.attrib.get(f"{xml_ns}id", get_formatted_uuid(seed_str))
            div.attrib[f"{xml_ns}id"] = x
            num_ids += 1
            ids.add(x)

    b = etree.tostring(
        root, pretty_print=True, encoding="utf-8", xml_declaration=True
    )
    f = open(protocol, "wb")
    f.write(b)

    assert len(ids) == num_ids
    return ids, num_ids




def main(args):
    if args.protocol:
        protocols = [args.protocol]
    else:
        protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
    num_ids = 0
    ids = []
    for p in tqdm(protocols, total=len(protocols)):
        i, n = add_div_ids(p)
        ids += i
        num_ids += n

    assert len(set(ids)) == num_ids




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=1971, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    parser.add_argument("-p", "--protocol",
                        type=str,
                        default=None,
                        help="operate on a single protocol")
    args = parser.parse_args()
    main(args)
