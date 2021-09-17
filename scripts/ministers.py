import pandas as pd
from pathlib import Path
import dateparser
import datetime
import unidecode


def main():
    # Read in all data files
    ministers = Path(".") / "input" / "ministers"
    dfs = []
    for i, x in enumerate(ministers.iterdir()):
        print(x)
        df = pd.read_csv(x.absolute())
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    print(df.columns)

    # Combine columns with different names
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

    # Remove parenthesis
    ref_pattern = r"\[[a-zA-ZÀ-ÿ0-9 ]+\]"
    df["end"] = df["end"].replace(ref_pattern, "", regex=True)
    df["start"] = df["start"].replace(ref_pattern, "", regex=True)

    bracket_pattern = r" ?\([a-zA-ZÀ-ÿ0-9\. ]+\)"
    df["name"] = df["name"].replace(bracket_pattern, "", regex=True)

    # Remove special characters
    df["name"] = df["name"].replace(r"[^A-Za-zÀ-ÿ /-]+", "", regex=True)
    df["title"] = df["title"].replace(r"[^A-Za-zÀ-ÿ /-]+", "", regex=True)
    df["start"] = df["start"].replace(r"[^A-Za-zÀ-ÿ0-9 /-]+", "", regex=True)
    df["end"] = df["end"].replace(r"[^A-Za-zÀ-ÿ0-9 /-]+", "", regex=True)

    # Convert dates to standard format
    def parse_date(s):
        if type(s) != str:
            if type(s) == int:
                if s > 1500 and s < 2200:
                    return datetime.datetime(s, 1, 1)
            return None
        else:
            date = dateparser.parse(s)
            print(date, type(date))
            return date

    df["start"] = df["start"].apply(lambda s: parse_date(s))
    df["end"] = df["end"].apply(lambda s: parse_date(s))

    # Generate id
    df["id"] = df["title"].apply(lambda x: unidecode.unidecode(x).lower())
    df["id"] = df["id"].str[:12]
    df["id"] = (
        df["name"].apply(lambda x: unidecode.unidecode(x).lower()).str.strip()
        + " "
        + df["id"]
    )
    df["id"] = df["id"].str.replace("-", " ")
    df["id"] = df["id"].str.replace(" ", "_")
    df["id"] = df["id"].str.replace("__", "_")
    df["id"] = df["id"].str.lower()
    df["id"] = df["id"]

    # Print and write to file
    print(df)
    df.to_csv("corpus/ministers.csv", index=False)


if __name__ == "__main__":
    main()
