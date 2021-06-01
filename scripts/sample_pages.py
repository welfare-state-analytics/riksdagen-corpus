import pandas as pd
import os
import argparse
def main(args, decades=[1920,1930]):
    train = args.train
    head_len = args.head
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

        head = decade_pages.head(head_len * 2)
        if train:
            head = head.iloc[::2, :]
        else:
            head = head.iloc[1::2, :]

        dfs.append(head.reset_index(drop=True))

    df = pd.concat(dfs)
    df = df.reset_index(drop=True)
    return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--out', type=str, default="sample.csv")
    parser.add_argument('--train', type=bool, default=True)
    parser.add_argument('--head', type=int, default=25)
    args = parser.parse_args()

    decades = range(1920, 1990, 10)
    df = main(args, decades=decades)

    print(df)

    df.to_csv(args.out, index=False)
