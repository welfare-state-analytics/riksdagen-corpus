from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.refine import reclassify, format_texts, random_classifier
from pyriksdagen.utils import infer_metadata
from lxml import etree
import pandas as pd
import os, progressbar, sys

parser = etree.XMLParser(remove_blank_text=True)


def reclassify_protocol(folder, protocol_id):
    metadata = infer_metadata(protocol_id)
    filename = folder + protocol_id + ".xml"
    root = etree.parse(filename, parser).getroot()

    root = reclassify(root, random_classifier)
    root = format_texts(root)
    b = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

    f = open(filename, "wb")
    f.write(b)
    f.close()


def main(args):
    pc_folder = "corpus/"
    if len(args) >= 2:
        for filename in args[1:]:
            folder = "/".join(filename.split("/")[:-1]) + "/"
            protocol_id = filename.split("/")[-1].replace(".xml", "")
            assert filename == folder + protocol_id + ".xml", (
                folder + protocol_id + ".xml"
            )
            reclassify_protocol(folder, protocol_id)

    else:
        folders = os.listdir(pc_folder)
        for outfolder in progressbar.progressbar(folders):
            if os.path.isdir(pc_folder + outfolder):
                outfolder = outfolder + "/"
                protocol_ids = os.listdir(pc_folder + outfolder)
                protocol_ids = [
                    protocol_id.replace(".xml", "")
                    for protocol_id in protocol_ids
                    if protocol_id.split(".")[-1] == "xml"
                ]

                for protocol_id in protocol_ids:
                    reclassify_protocol(pc_folder + outfolder, protocol_id)


if __name__ == "__main__":
    args = sys.argv
    main(args)
