"""
Calculate an upper bound for person mapping accuracy
"""
from pyriksdagen.utils import protocol_iterators
from lxml import etree
import numpy as np
import pandas as pd
from tqdm import tqdm
import argparse
from multiprocessing import Pool

def get_date(root):
    for docDate in root.findall(".//{http://www.tei-c.org/ns/1.0}docDate"):
        date_string = docDate.text
        break
    return date_string

# Fix parallellization
def accuracy(protocol):
    root = etree.parse(protocol, parser).getroot()
    year = int(get_date(root).split("-")[0])
    known, unknown = 0, 0
    for div in root.findall(".//{http://www.tei-c.org/ns/1.0}div"):
        for elem in div:
            if "who" in elem.attrib:
                who = elem.attrib["who"]
                if who == "unknown":
                    unknown += 1
                else:
                    known += 1
    return year, known, unknown

parser = etree.XMLParser(remove_blank_text=True)
def main(args):
    protocols = list(protocol_iterators("corpus/", start=args.start, end=args.end))
    years = sorted(set([int(p.split('/')[2][:4]) for p in protocols]))
    df = pd.DataFrame(np.zeros((len(years), 2), dtype=int), index=years, columns=['known', 'unknown'])
    pool = Pool()
    for year, known, unknown in tqdm(pool.imap(accuracy, protocols), total=len(protocols)):
        df.loc[year, 'known'] += known
        df.loc[year, 'unknown'] += unknown
    df['accuracy_upper_bound'] = df.div(df.sum(axis=1), axis=0)['known']
    return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    df = main(args)

    print(df)
    print("Average:", df.mean())
    print("Weighted average:", df["known"].sum() / (df["known"] + df["unknown"]).sum())
    df.to_csv("input/accuracy_upper_bound.csv", index_label='year')