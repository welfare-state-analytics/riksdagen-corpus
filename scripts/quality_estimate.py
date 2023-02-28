"""
Calculate an upper bound for person mapping accuracy
"""
from pyriksdagen.utils import protocol_iterators
from lxml import etree
import numpy as np
import pandas as pd
from tqdm import tqdm
import argparse
from pyriksdagen.utils import infer_metadata

TEI_NS = "{http://www.tei-c.org/ns/1.0}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"

def check_elem(elem, df):
    elem_id = elem.attrib.get(f"{XML_NS}id")
    df_elem = df[df["elem_id"] == elem_id]
    if len(df_elem) == 0:
        return None
    else:
        tag = elem.tag
        current_row = df_elem.to_dict(orient='index')
        current_row = current_row[list(current_row.keys())[0]]
        correct_tag = current_row["segmentation"]
        if "," in correct_tag or ";" in correct_tag:
            return None
        tag = tag.split("}")[-1]
        if tag == "seg":
            tag = "u"
        if correct_tag == "utterance":
            correct_tag = "u"
        if tag.split("}")[-1] == correct_tag:
            return 1, 0
        else:
            return 0, 1

def accuracy(protocol, df):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()
    correct, incorrect = 0, 0
    for body in root.findall(f".//{TEI_NS}body"):
        for div in body.findall(f".//{TEI_NS}div"):
            for elem in div:
                pair = check_elem(elem, df)
                if pair is not None:
                    correct, incorrect = correct + pair[0], incorrect + pair[1]

                for subelem in elem:
                    pair = check_elem(subelem, df)
                    if pair is not None:
                        correct, incorrect = correct + pair[0], incorrect + pair[1]

    return correct, incorrect

def main(args):
    protocols = list(protocol_iterators("corpus/", start=args.start, end=args.end))
    df = pd.read_csv(args.df)
    correct, incorrect = 0, 0

    for p in tqdm(protocols):
        metadata = infer_metadata(p)
        protocol_id = metadata["protocol"].replace("_", "-")
        current = df[df.protocol_id == protocol_id]
        if len(current) > 0:
            correct_p, incorrect_p = accuracy(p, current)
            correct, incorrect = correct + correct_p, incorrect + incorrect_p

    print(correct, incorrect)
    print(correct /(correct+ incorrect))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1867)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--df", type=str, required=True)
    args = parser.parse_args()
    result = main(args)
