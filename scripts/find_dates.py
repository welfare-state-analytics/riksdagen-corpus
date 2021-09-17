from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.refine import detect_date
from pyriksdagen.utils import infer_metadata
from lxml import etree
import pandas as pd
import os
import progressbar

pc_folder = "corpus/"
folders = os.listdir(pc_folder)

parser = etree.XMLParser(remove_blank_text=True)
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
            metadata = infer_metadata(protocol_id)
            filename = pc_folder + outfolder + protocol_id + ".xml"

            root = etree.parse(filename, parser)
            root, dates = detect_date(root, metadata["year"])

            b = etree.tostring(
                root, pretty_print=True, encoding="utf-8", xml_declaration=True
            )

            f = open(filename, "wb")
            f.write(b)
            f.close()
