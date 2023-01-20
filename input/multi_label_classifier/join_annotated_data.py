import numpy as np
import pandas as pd
from collections import Counter
from pathlib import Path
import argparse


def read_messy_csv(filepath):
    with open(filepath, "r") as f:
        first_row = True
        data = []
        for line in f:
            if first_row:
                first_row = False
                continue
            id, type, tag, x, y, w, h, *content = line.split(",")
            content = ",".join(content)
            data.append([id, type, tag, x, y, w, h, content])

    df = pd.DataFrame(
        data, columns=["id", "type", "tag", "x", "y", "w", "h", "content"]
    )
    df = df.applymap(lambda x: x.strip('"')) # remove csv artifact quotes
    return df


def main(args):
    p = Path()
    tags = args.tags
    for tag in tags:
        right = pd.concat(
            [read_messy_csv(f) for f in p.glob(f'input/multi_label_classifier/{tag}/*.csv')])\
            .reset_index(drop=True
        )
        right[tag] = 1
        right = right.drop('tag', axis=1)

        if tag == tags[0]:
            left = right 
        else:
            left = left.merge(right[["id", tag]], on="id", how="left")
            ids = [i for i, row in right.iterrows() if row['id'] not in set(left['id'])]
            left = pd.concat([left, right.loc[ids]])
            
    left[tags] = left[tags].fillna(0).astype(int)
    left = left.sort_values('id')
    left.to_csv('input/multi_label_classifier/training_data.csv', index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-t', '--tags', nargs='+', default=["seg", "intro", 'note'])
    args = parser.parse_args()
    main(args)
