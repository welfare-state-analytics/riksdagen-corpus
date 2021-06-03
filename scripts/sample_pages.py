import pandas as pd
import os
import argparse
def generate_sample(args):
    train = args.train
    head_len = args.head
    decades = range(args.start, args.end, 10)
    pages_path = "input/protocols/pages.csv"

    pages = pd.read_csv(pages_path)
    pages = pages.drop("Unnamed: 0", axis=1)
    print(pages)
    dfs = []
    for decade in decades:
        print("Sample for decade", decade)
        decade_upper = decade + 10

        decade_pages = pages[(pages["year"] >= decade) & (pages["year"] < decade_upper)]
        decade_pages = decade_pages.sort_values("ordinal")
        
        tail = decade_pages.tail(args.skip * 2)
        head = tail.head(head_len * 2)
        if train:
            head = head.iloc[::2, :]
        else:
            head = head.iloc[1::2, :]

        dfs.append(head.reset_index(drop=True))

    df = pd.concat(dfs)
    df = df.reset_index(drop=True)
    return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a random sample of pages in the parliamentary corpus.')
    parser.add_argument('--out', type=str, default="sample.csv")
    parser.add_argument('--train', type=bool, default=True, help="Whether to generate a train or a test set. Boolean.")
    parser.add_argument('--head', type=int, default=25, help="How many pages are sampled by decade")
    parser.add_argument('--skip', type=int, default=0, help="How many pages are skipped in the beginning")
    parser.add_argument('--start', type=int, default=1920, help="Start decade")
    parser.add_argument('--end', type=int, default=1930, help="End decade")
    args = parser.parse_args()

    df = generate_sample(args)
    print(df)

    df.to_csv(args.out, index=False)
