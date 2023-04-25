"""
Calculate an upper bound for segment classification accuracy.
Based on the gold standard annotations.
"""
from pyriksdagen.utils import protocol_iterators, elem_iter, infer_metadata
from lxml import etree
import numpy as np
import pandas as pd
from tqdm import tqdm
import argparse
from multiprocessing import Pool
from pathlib import Path
import warnings
import progressbar
from scipy.stats import beta
import seaborn as sns
from matplotlib import pyplot as plt

XML_NS = "{http://www.w3.org/XML/1998/namespace}"

def match_elem(elem, df):
    elem_id = elem.attrib.get(f'{XML_NS}id', None)
    df_elem = df[df["elem_id"] == elem_id]
    assert len(df_elem) == 1

    annotated_tag = list(df_elem["segmentation"])[0]

    elem_tag = elem.tag.split("}")[-1]
    if elem_tag == "seg":
        elem_tag = "u"
    if elem.attrib.get("type") == "speaker":
        elem_tag = "intro"
    if annotated_tag in ["title", "margin"]:
        annotated_tag = "note"
    

    if type(annotated_tag) == float or annotated_tag not in ["intro", "u", "note"]:
        print("Invalid annotation:", annotated_tag)
        return 0,0

    if annotated_tag == elem_tag:
        return 1,0
    else:
        print("Error:", annotated_tag, elem_tag)
        return 0,1

# Fix parallellization
def estimate_accuracy(protocol, df):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()
    correct, incorrect = 0, 0
    ids = set(df["elem_id"])
    for tag, elem in elem_iter(root):
        if tag == "u":
            x = None
            for subelem in elem:
                x = subelem.attrib.get(f'{XML_NS}id', None)
                if x in ids:
                    subelem_text = " ".join(subelem.text.split())
                    results = match_elem(subelem, df)
                    correct += results[0]
                    incorrect += results[1]

        elif tag in ["note"]:
            x = elem.attrib.get(f'{XML_NS}id', None)
            if x in ids:
                elem_text = " ".join(elem.text.split())
                results = match_elem(elem, df)
                correct += results[0]
                incorrect += results[1]

    return correct, incorrect

def main(args):
    protocols = list(protocol_iterators("corpus/", start=args.start, end=args.end))
    df = pd.read_csv(args.path_goldstandard)

    rows = []
    correct, incorrect = 0, 0
    for p in progressbar.progressbar(protocols):
        path = Path(p)
        protocol_id = path.stem
        
        #print(p, protocol_id)
        df_p = df[df["protocol_id"] == protocol_id]
        if len(df_p) >= 1:
            metadata = infer_metadata(p)

            acc = estimate_accuracy(path, df_p)
            correct += acc[0]
            incorrect += acc[1]

            if acc[1] + acc[0] > 0:
                rows.append([acc[0], acc[1], acc[0] / (acc[0] + acc[1]), metadata["year"], metadata["chamber"]])
            #else:
            #    rows.append([acc[0], acc[1], acc[0] / (acc[0] + acc[1]), metadata["year"], metadata["chamber"]])

    accuracy = correct / (correct + incorrect)
    lower = beta.ppf(0.05, correct + 1, incorrect + 1)
    upper = beta.ppf(0.95, correct + 1, incorrect + 1)
    print(f"ACC: {100 * accuracy:.2f}% [{100* lower:.2f}% – {100* upper:.2f}%]")

    print(correct, incorrect)

    df = pd.DataFrame(rows, columns=["correct", "incorrect", "accuracy", "year", "chamber"])
    df["decade"] = (df["year"] // 10) * 10
    print(df)

    byyear_sum = df[["correct", "incorrect"]].groupby(df['decade']).sum()
    byyear_sum["lower"] = [beta.ppf(0.05, c + 1, i + 1) for c, i in zip(byyear_sum["correct"], byyear_sum["incorrect"])]
    byyear_sum["upper"] = [beta.ppf(0.95, c + 1, i + 1) for c, i in zip(byyear_sum["correct"], byyear_sum["incorrect"])]
    byyear = df['accuracy'].groupby(df['decade'])
    byyear_sum = byyear_sum.merge(byyear.mean(), on="decade").reset_index()
    print(byyear_sum)
    byyear_sum.to_csv("results.csv", index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1867)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--path_goldstandard", type=str, default="corpus/quality_assesment/segment_classification/prot-segment-classification.csv")
    args = parser.parse_args()
    df = main(args)

    print(df)
