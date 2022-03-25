"""
Convert the digital original files (1990->) into parla-clarin
"""
import os
from lxml import etree
import progressbar
import pandas as pd
import argparse

from pyriksdagen.download import read_xml_blocks, read_html_blocks
from pyriksdagen.utils import infer_metadata

import json
import pandas as pd
from pathlib import Path
import progressbar

def main(args):
    outfolder = "input/raw/"

    columns = ["protocol_id", "year", "pages", "number"]
    rows = []


    rows = []
    json_files = Path(args.infolder).glob("*.json")
    for fpath in progressbar.progressbar(list(json_files)):
        with open(fpath, encoding='utf-8-sig') as f:
            data = json.load(f)

        session = data["dokumentstatus"]["dokument"]["rm"]
        pid = data["dokumentstatus"]["dokument"]["nummer"]
        date = data["dokumentstatus"]["dokument"]["datum"]
        html = data["dokumentstatus"]["dokument"]["html"]
        year = int(date.split("-")[0])

        if year >= args.start and year <= args.end:
            #html_path = folder + "/" + fpath
            #xml_path = folder + "-xml/" + fpath.replace(".html", ".xml")
            root = read_html_blocks(html)
            if root is None:
                continue
                if os.path.exists(xml_path):
                    root = read_xml_blocks(xml_path, html_path)

            if root is not None:
                protocol_id = root.attrib["id"]
                metadata = infer_metadata(protocol_id)

                root_str = etree.tostring(root, encoding="utf-8", pretty_print=True).decode(
                    "utf-8"
                )

                if not os.path.exists(outfolder + protocol_id):
                    os.mkdir(outfolder + protocol_id)

                f = open(outfolder + protocol_id + "/original.xml", "w")
                f.write(root_str)
                f.close()

                row = [protocol_id, metadata["year"], None, metadata["number"]]

                # Set pages to 1 if there is content
                if len("".join(root.itertext())) >= 10:
                    row[2] = 1

                rows.append(row)


    protocol_db = pd.DataFrame(rows, columns=columns)
    print(protocol_db)

    protocol_db.to_csv("input/protocols/digital_originals.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1990)
    parser.add_argument("--end", type=int, default=2021)
    parser.add_argument("--infolder", type=str, required=True)
    args = parser.parse_args()
    main(args)
