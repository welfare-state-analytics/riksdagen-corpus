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
        tail = decade_pages.tail(len(decade_pages)-args.skip * 2)
        head = tail.head(head_len * 2)
        if train:
            head = head.iloc[::2, :]
        else:
            head = head.iloc[1::2, :]

        head = head.reset_index(drop=True)

        head["curator"] = head.index
        userlen = head_len // 5
        head["curator"] = head["curator"].apply(lambda x: x // userlen) 

        dfs.append(head)

    df = pd.concat(dfs)
    df = df.reset_index(drop=True)

    df = df[["package_id", "year", "pagenumber", "curator"]]
    #df["path"] = df["package_id"].str.replace("-", "_")
    years = df["package_id"].astype(str).str.split("-").str[1]
    df["path"] = "corpus/" + years + "/"+  df["package_id"] + ".xml"

    df["url"] = df["package_id"]  + ".xml"# + df["url"]
    years = df["package_id"].str.split("-").str[1] + "/"
    df["url"] = "https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/" + years + df["url"]
    return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a random sample of pages in the parliamentary corpus.')
    parser.add_argument('--out', type=str, help="Outfile location" ,default="sample.csv")
    parser.add_argument('--cur', type=str, help="Split to curators" ,default=False)
    parser.add_argument('--train', type=bool, default=True,
        help="Whether to generate a train or a test set. Boolean.")
    parser.add_argument('--head', type=int, default=25, help="How many pages are sampled by decade")
    parser.add_argument('--skip', type=int, default=0, help="How many pages are skipped in the beginning")
    parser.add_argument('--start', type=int, default=1920, help="Start decade")
    parser.add_argument('--end', type=int, default=1930, help="End decade")
    args = parser.parse_args()

    df = generate_sample(args)
    print(df)

    def ix_to_curator(x):
        if x < 2:
            return "F"
        elif x < 4:
            return "J"
        else:
            return "V"

    df["curator"] = df["curator"].apply(lambda x: ix_to_curator(x))

    if args.cur:
        print("Write to curator files...")
        df = df[["package_id", "pagenumber", "url", "curator"]]

        print(args.out)
        for curator in set(df["curator"]):
            df_curator = df[df["curator"] == curator]
            df_curator = df_curator[["package_id", "pagenumber", "url"]]
            fname = args.out.replace(".csv", "_" + curator + ".csv")
            print(df_curator)
            df_curator.to_csv(fname, index=False)
    else:
        print("Write to file...")
        df = df[["package_id", "pagenumber", "url"]]

        df.to_csv(args.out, index=False)
