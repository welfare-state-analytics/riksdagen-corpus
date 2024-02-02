"""
Convert the digital original files (1990->) into parla-clarin
"""
import os
from lxml import etree
import progressbar
import pandas as pd
import argparse

from pyriksdagen.download import dl_kb_blocks, LazyArchive, count_pages
from pyriksdagen.export import dict_to_parlaclarin
from pyriksdagen.utils import infer_metadata

import json
import pandas as pd
from pathlib import Path
import progressbar

def main(args):
    if args.protocol_ids is not None:
        package_ids = args.protocol_ids
    else:
        df = count_pages(args.start, args.end)
        print(df)
        package_ids = list(df["protocol_id"])
    archive = LazyArchive()
    for package_id in progressbar.progressbar(list(package_ids)):
        data = infer_metadata(package_id)
        print("metadata", data)
        data["authority"] = args.authority
        data["session"] = data["sitting"]
        data["protocol_id"] = data["protocol"]
        data["source_uri"] = f"https://betalab.kb.se/{package_id}/_view"

        data["licence"] = "Licence: Attribution 4.0 International (CC BY 4.0)"
        data["licence_url"] = "https://creativecommons.org/licenses/by/4.0/"

        paragraphs = dl_kb_blocks(package_id, archive)
        print()
        print(paragraphs[0])
        data["edition"] = args.edition
        data["paragraphs"] = paragraphs

        # Create parlaclarin and write to disk
        dict_to_parlaclarin(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1867)
    parser.add_argument("--end", type=int, default=1990)
    parser.add_argument("--authority", type=str, default="SWERIK Project, 2023-2027")
    parser.add_argument("--edition", type=str, required=True)
    parser.add_argument("--protocol_ids", type=str, nargs="+", default=None)
    args = parser.parse_args()
    main(args)
