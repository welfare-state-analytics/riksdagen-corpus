"""
Replace dates
"""
from pyparlaclarin.refine import format_texts
from pyriksdagen.db import load_patterns
from pyriksdagen.refine import (
    detect_mps,
    find_introductions,
    update_ids,
)
from pyriksdagen.utils import infer_metadata
from pyriksdagen.utils import protocol_iterators

from lxml import etree
import pandas as pd
import os, progressbar, argparse, re

def main(args):
    df = pd.read_csv(args.df)
    df["protocol_id"] = df["year"].str.replace("/", "") + "--"
    df["protocol_id"] = df["protocol_id"] + df["id"].astype(str)
    df["protocol_id"] = "prot-" + df["protocol_id"]
    df["protocol_id"] = df["protocol_id"].str.replace("-", "_")
    df["date"] = df["date"].str.split(' ', expand = True)[0]
    print(df)
    start_year = args.start
    end_year = args.end
    for protocol in progressbar.progressbar(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end))):
        metadata = infer_metadata(protocol)
        #print(metadata)
        protocol_id = protocol.split("/")[-1]
        year = metadata["year"]

        current_df = df[df["protocol_id"] == metadata["protocol"]]
        print(current_df)


        year_str = current_df.iloc[0]["date"]
        s = open(protocol, "r").read()
        
        date_regex = "[0-9]{4,4}(\\-[0-9]{2,2}\\-[0-9]{2,2})"
        s = re.sub(f"<docDate when=\"{date_regex}\">{date_regex}</docDate>", f"<docDate when=\"{year_str}\">{year_str}</docDate>", s)

        f = open(protocol, "wb")
        f.write(s.encode("utf-8"))
        f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--df", type=str, default="../riksdagen-dateparser/scraped_dates.csv")
    args = parser.parse_args()
    main(args)
