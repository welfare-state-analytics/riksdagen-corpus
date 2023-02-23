"""
Calculate an upper bound for person mapping accuracy
"""
from pyriksdagen.utils import protocol_iterators, infer_metadata
from lxml import etree
import numpy as np
import pandas as pd
from tqdm import tqdm
import argparse
from multiprocessing import Pool

def create_divs(root):
    bodies = root.findall(".//{http://www.tei-c.org/ns/1.0}body")
    assert len(bodies) == 1
    body = bodies[0]
    old_divs = body.findall(".//{http://www.tei-c.org/ns/1.0}div")
    current_div = etree.SubElement(body, "div")
    for div in old_divs:
        for elem in div:
            if elem.text is not None:
                beginning = elem.text.strip()[:4]
                if "§" in beginning:
                    current_div = etree.SubElement(body, "div")

            current_div.append(elem)

    for div in list(body.findall(".//{http://www.tei-c.org/ns/1.0}div")) + list(body.findall(".//div")):
        if len(div) == 0:
            parent = div.getparent()
            parent.remove(div)
        else:
            notes = div.findall(".//{http://www.tei-c.org/ns/1.0}note")
            intros = [n for n in notes if n.attrib.get("type") == "speaker"]
            if len(intros) >= 1:
                div.attrib["type"] = "debateSection"
            else:
                div.attrib["type"] = "commentSection"
    return root

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
    for protocol in tqdm(protocols):
        root = etree.parse(protocol, parser).getroot()
        root = create_divs(root)
        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )
        with open(protocol, "wb") as f:
            f.write(b)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    args = parser.parse_args()
    main(args)
