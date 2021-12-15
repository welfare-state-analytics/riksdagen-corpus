"""
Convert the digital original files (1990->) into parla-clarin
"""
import os
from lxml import etree
import progressbar
import pandas as pd
import argparse

from pyriksdagen.download import read_xml_blocks, read_xml_blocks
from pyriksdagen.utils import infer_metadata

def main(args):
    dataraw = "input/raw/"
    outfolder = "input/protocols/"
    folders = os.listdir(dataraw)
    folders = [dataraw + folder for folder in folders if os.path.isdir(dataraw + folder)]
    folders = [folder for folder in folders if "-xml" not in folder]

    print(folders)

    columns = ["protocol_id", "year", "pages", "number"]
    rows = []

    for folder in sorted(folders):
        files = sorted(os.listdir(folder))

        print(folder)

        for fpath in progressbar.progressbar(files):
            html_path = folder + "/" + fpath
            xml_path = folder + "-xml/" + fpath.replace(".html", ".xml")
            root = get_html_blocks(html_path)
            if root is None:
                if os.path.exists(xml_path):
                    root = get_xml_blocks(xml_path, html_path)

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
    args = parser.parse_args()
    main(args)
