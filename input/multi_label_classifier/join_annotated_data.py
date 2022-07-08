import pandas as pd
from collections import Counter
from pathlib import Path


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
    df = df.applymap(lambda x: x.strip('"'))  # remove csv artifact quotes
    return df


p = Path()
tags = ["seg", "intro", 'note']

for tag in tags:
    
    right = pd.concat(
        [read_messy_csv(f) for f in p.glob(f'input/multi_label_classifier/{tag}/*.csv')])\
        .reset_index(drop=True
    )

    right[tag] = 1

    if tag == tags[0]:
        left = right
    else:  # left join multilabel observations, concatenate others
        left = left.merge(right[["id", tag]], on="id", how="left")
        ids = left.loc[left[tag].notna(), "id"].tolist()
        left = pd.concat([left, right[right["id"].isin(ids)]])

df = left[left["id"].duplicated()].sort_values(by="id")
df[tags] = df[tags].fillna(0).astype(int)
df.to_csv('input/multi_label_classifier/training_data.csv', index=False)

