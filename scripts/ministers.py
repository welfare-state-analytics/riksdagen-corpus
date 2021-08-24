import pandas as pd
from pathlib import Path

def main():
    ministers = Path(".") / "input" / "ministers"

    dfs = []

    for i, x in enumerate(ministers.iterdir()):
        print(x)
        df = pd.read_csv(x.absolute())
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    print(df.columns)


    df["Namn"] = df["Namn"].fillna(df["Namn.1"])
    df["Namn"] = df["Namn"].fillna(df["Minister"])
    df["Namn"] = df["Namn"].fillna(df["Minister.1"])

    df["Titel"] = df["Titel"].fillna(df["Befattning"])
    df["Titel"] = df["Titel"].fillna(df["Ämbete"])

    df["name"] = df["Namn"]
    df["title"] = df["Titel"]
    df["start"] = df["Tillträdde"]
    df["end"] = df["Avgick"]

    df = df[["name", "title", "start", "end"]]
    
    ref_pattern = r'\[[a-zA-ZÀ-ÿ0-9 ]+\]'
    df["end"] = df["end"].replace(ref_pattern, "", regex=True)
    df["start"] = df["start"].replace(ref_pattern, "", regex=True)

    bracket_pattern = r' ?\([a-zA-ZÀ-ÿ0-9\. ]+\)'
    df["name"] = df["name"].replace(bracket_pattern, "", regex=True)

    # Remove special characters
    df["name"] = df["name"].replace(r'[^A-Za-zÀ-ÿ /-]+', "", regex=True)
    df["title"] = df["title"].replace(r'[^A-Za-zÀ-ÿ /-]+', "", regex=True)
    df["start"] = df["start"].replace(r'[^A-Za-zÀ-ÿ0-9 /-]+', "", regex=True)
    df["end"] = df["end"].replace(r'[^A-Za-zÀ-ÿ0-9 /-]+', "", regex=True)

    print(df)
    df.to_csv("corpus/ministers.csv", index=False)
    
if __name__ == '__main__':
    main()