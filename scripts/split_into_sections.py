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

TEI_NS = "{http://www.tei-c.org/ns/1.0}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"

def create_divs(root, metadata):
    bodies = root.findall(f".//{TEI_NS}body")
    assert len(bodies) == 1
    body = bodies[0]

    if metadata["chamber"] == "Första kammaren":
        div = body[0]
        div.attrib["type"] = "debateSection"
        return root

    old_divs = body.findall(f".//{TEI_NS}div")
    current_div = etree.SubElement(body, "div")
    for div in old_divs:
        for elem in div:
            if elem.text is not None:
                beginning = elem.text.strip()[:4]
                if "§" in beginning:
                    current_div = etree.SubElement(body, "div")

            current_div.append(elem)

    for div in list(body.findall(f".//{TEI_NS}div")) + list(body.findall(".//div")):
        if len(div) == 0:
            parent = div.getparent()
            parent.remove(div)
        else:
            notes = div.findall(f".//{TEI_NS}note")
            intros = [n for n in notes if n.attrib.get("type") == "speaker"]
            if len(intros) >= 1:
                div.attrib["type"] = "debateSection"
            else:
                div.attrib["type"] = "commentSection"
    return root

def convert_u_heuristic(root):
    rows = []
    for div in list(root.findall(f".//{TEI_NS}div")) + list(root.findall(".//div")):
        for elem in div:
            if elem.attrib.get("type") == "speaker":
                break

            if elem.tag == f"{TEI_NS}u":
                protocol_id = root.findall(f".//{TEI_NS}text")[0].findall(f".//{TEI_NS}head")[0].text
                print(protocol_id, "utterance before intro", elem.attrib[f"{XML_NS}id"])
                for seg in elem:
                    rows.append([seg.attrib[f"{XML_NS}id"], "note"])
    return rows

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)
    protocols = list(protocol_iterators("corpus/", start=args.start, end=args.end))
    rows = []

    for protocol in tqdm(protocols):
        root = etree.parse(protocol, parser).getroot()
        
        metadata = infer_metadata(protocol)
        try:
            root = create_divs(root, metadata)
            protocol_rows = convert_u_heuristic(root)
            rows = rows + protocol_rows
            b = etree.tostring(
                root, pretty_print=True, encoding="utf-8", xml_declaration=True
            )
            with open(protocol, "wb") as f:
                f.write(b)
        except Exception:
            print(f"Problem with {protocol} ... Skipping ...")

    df = pd.DataFrame(rows, columns=["id", "preds"])
    df.to_csv("input/segmentation/section_heuristic_preds.csv", index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=1920, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    args = parser.parse_args()
    main(args)
