"""
Calculate an upper bound for person mapping accuracy
"""
from pyriksdagen.utils import protocol_iterators
from lxml import etree
import numpy as np
import pandas as pd
from progressbar import progressbar
import argparse

def get_date(root):
    for docDate in root.findall(".//{http://www.tei-c.org/ns/1.0}docDate"):
        date_string = docDate.text
        break
    return date_string


def main(args):
    parser = etree.XMLParser(remove_blank_text=True)

    accuracy = {}
    for protocol in progressbar(list(protocol_iterators("corpus/", start=args.start, end=args.end))):
        root = etree.parse(protocol, parser).getroot()
        year = int(get_date(root).split("-")[0])
        for div in root.findall(".//{http://www.tei-c.org/ns/1.0}div"):
            for elem in div:
                if "who" in elem.attrib:
                    if year not in accuracy:
                        accuracy[year] = {}

                    who = elem.attrib["who"]
                    if who == "unknown":
                        accuracy[year]["unknown"] = accuracy[year].get("unknown",0) + 1
                    elif who[-1] == "w":
                        accuracy[year]["wikidata"] = accuracy[year].get("wikidata",0) + 1
                    else:
                        accuracy[year]["known"] = accuracy[year].get("known",0) + 1

    return accuracy

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()

    accuracy = main(args)
    rows = []
    for year, y_acc in accuracy.items():
        row = [year, y_acc.get("wikidata",0),  y_acc.get("known",0), y_acc.get("unknown",0)]
        rows.append(row)

    df = pd.DataFrame(rows, columns=["year", "wikidata", "known", "unknown"])

    df["accuracy upper bound"] = (df["wikidata"] + df["known"]) / (df["wikidata"] + df["known"] + df["unknown"])
    df["wikidata upper bound"] = (df["wikidata"]) / (df["wikidata"] + df["known"] + df["unknown"])
    print(df)

    print("Average:", df.mean())
    #print("Weighted average:", df["known"].sum() / (df["known"] + df["unknown"]).sum())
    df.to_csv("accuracy_upper_bound.csv", index=False)