"""
Convert the digital original files (1990->) into parla-clarin
"""
import os
from lxml import etree
import progressbar
import pandas as pd
import argparse

from pyriksdagen.download import dl_kb_blocks, LazyArchive
from pyriksdagen.export import dict_to_parlaclarin
from pyriksdagen.utils import infer_metadata

import json
import pandas as pd
from pathlib import Path
import progressbar

def main(args):
    package_ids = ["prot-198990--7"]
    archive = LazyArchive()
    for package_id in progressbar.progressbar(list(package_ids)):
        data = infer_metadata(package_id)
        print("metadata", data)
        data["session"] = data["sitting"]
        data["protocol_id"] = data["protocol"]
        paragraphs = dl_kb_blocks(package_id, archive)
        print()
        print(paragraphs[0])
        data["edition"] = args.edition
        data["paragraphs"] = paragraphs

        # Create parlaclarin and write to disk
        dict_to_parlaclarin(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1990)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--edition", type=str, default="0.4.2")
    args = parser.parse_args()
    main(args)
