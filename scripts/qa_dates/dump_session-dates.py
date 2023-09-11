#!/usr/bin/env python3
"""
Generate a CSV file for a parliament session dates unit test.
"""
from lxml import etree
from pyriksdagen.utils import protocol_iterators, get_doc_dates
from tqdm import tqdm
import argparse
import pandas as pd




def main(args):
    problem_protocols = []
    rows = []
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))

    for protocol in tqdm(protocols, total=len(protocols)):
        E, dates = get_doc_dates(protocol)
        if E:
            problem_protocols.append(protocol)
        for d in dates:
            rows.append([protocol, d])
    if len(problem_protocols) > 0:
        print("\n\nThere are some issues with dates not matching: docDate when attr vs text in:\n\n")
        [print(p) for p in problem_protocols]
        print("\n\nFix that!\n\n")
    else:
        print("lookin' good...")
        df = pd.DataFrame(rows, columns=['protocol', 'date'])
        df.to_csv("corpus/quality_assessment/session-dates/session-dates.csv", sep=';', index=False)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=1867, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    args = parser.parse_args()
    main(args)
