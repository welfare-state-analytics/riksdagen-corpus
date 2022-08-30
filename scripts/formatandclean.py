"""
Format text lines to be under max line length, remove empty tags, update hashes.
"""
from pyparlaclarin.refine import format_texts
from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.refine import (
    detect_mps,
    find_introductions,
    update_ids,
    update_hashes,
)
from pyriksdagen.utils import infer_metadata
from lxml import etree
import pandas as pd
import os, progressbar, argparse
from pathlib import Path

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)
    protocol_folders = list(Path(args.corpus_path).glob("protocols/*"))
    for folder in progressbar.progressbar(protocol_folders):
        year = folder.stem[:4]
        year = int(year)
        if args.start <= year <= args.end:
            for file in folder.glob("*.xml"):
                protocol_id = file.stem
                with file.open() as f:
                    root = etree.parse(f, parser).getroot()

                root = format_texts(root)
                root = update_hashes(root, protocol_id)
                root = update_ids(root, protocol_id)
                b = etree.tostring(
                    root, pretty_print=True, encoding="utf-8", xml_declaration=True
                )

                with file.open("wb") as f:
                    f.write(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus_path", type=str, default="corpus")
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
