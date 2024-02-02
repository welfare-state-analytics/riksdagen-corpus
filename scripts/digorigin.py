"""
Convert the digital original files (1990->) into parla-clarin
"""
import os
from lxml import etree
import progressbar
import pandas as pd
import argparse

from pyriksdagen.download import oppna_data_to_dict
from pyriksdagen.export import dict_to_parlaclarin
from pyriksdagen.utils import infer_metadata

import json
import pandas as pd
from pathlib import Path
import progressbar

def main(args):
    json_files = []
    for infolder in args.infolder:
        json_files += list(Path(infolder).glob("*.json"))
    for fpath in progressbar.progressbar(list(json_files)):
        with open(fpath, encoding='utf-8-sig') as f:
            data = json.load(f)

        session = data["dokumentstatus"]["dokument"]["rm"]
        pid = data["dokumentstatus"]["dokument"]["nummer"]
        date = data["dokumentstatus"]["dokument"]["datum"]
        html = data["dokumentstatus"]["dokument"]["html"]
        year = int(date.split("-")[0])
        if year >= args.start and year <= args.end:
            data = oppna_data_to_dict(data)
            data["edition"] = args.edition
            metadata = infer_metadata(data["protocol_id"])
            for field in ["number", "sitting"]:
                data[field] = metadata[field]

            (Path(args.corpus_location) / f"{metadata['sitting']}").mkdir(parents=True, exist_ok=True)
            # Create parlaclarin and write to disk
            dict_to_parlaclarin(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1990)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--corpus_location", type=str, default="corpus/protocols")
    parser.add_argument("--edition", type=str, required=True)
    parser.add_argument("--infolder", nargs='+', type=str, required=True,
        help="Path to the prot-*.json folder downloaded from Riksdagens Öppna Data")
    args = parser.parse_args()
    main(args)
