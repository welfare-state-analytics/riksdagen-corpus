"""
Convert the digital original files (1990->) into parla-clarin
"""
import os
from lxml import etree
import progressbar
import pandas as pd
import argparse

from pyriksdagen.download import dl_kb_blocks, LazyArchive, count_pages, convert_alto
from pyriksdagen.export import dict_to_parlaclarin
from pyriksdagen.utils import infer_metadata

import json
import pandas as pd
from pathlib import Path
import progressbar

def fetch_local_package(pgk_path, package):
    filenames = sorted(os.listdir(f"{pgk_path}/{package}"))
    def files():
        for fname in filenames:
            with open(f"{pgk_path}/{package}/{fname}", 'r') as f:
                yield f.read()
    return filenames, files()

def main(args):
    if args.local_alto is not None:
        package_ids = args.local_alto
        archive = None
    else:
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

        if archive:
            paragraphs = dl_kb_blocks(package_id, archive)
        else:
            filenames, files = fetch_local_package(args.alto_path, package_id)
            paragraphs = convert_alto(filenames, files)
        print()
        print(paragraphs[0])
        data["paragraphs"] = paragraphs

        # Create parlaclarin and write to disk
        dict_to_parlaclarin(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1867)
    parser.add_argument("--end", type=int, default=1990)
    parser.add_argument("--authority", type=str, default="SWERIK Project, 2023-2027")
    parser.add_argument("--protocol_ids", type=str, nargs="+", default=None)
    parser.add_argument("--local-alto", type=str, nargs="+", default=None, help="Locally stored alto package (folder=protocol name, contents=pages.")
    parser.add_argument("--alto-path", type=str, help="Path to `--local-alto` directories")
    args = parser.parse_args()
    main(args)
