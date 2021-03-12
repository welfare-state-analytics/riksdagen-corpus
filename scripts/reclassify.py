from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.refine import reclassify_paragrahps, format_texts
from pyriksdagen.utils import infer_metadata
from lxml import etree
import pandas as pd
import os, progressbar

root = ""#"../"
pc_folder = root + "corpus/"
folders = os.listdir(pc_folder)

mp_db = pd.read_csv(root + "corpus/members_of_parliament.csv")

import tensorflow as tf
import fasttext.util

model = tf.keras.models.load_model("input/segment-classifier")

# Load word vectors from disk or download with the fasttext module
vector_path = 'cc.sv.300.bin'
fasttext.util.download_model('sv', if_exists='ignore')
ft = fasttext.load_model(vector_path)

classifier = dict(
    model=model,
    ft=ft,
    dim=ft.get_word_vector("hej").shape[0]
)

parser = etree.XMLParser(remove_blank_text=True)
for outfolder in progressbar.progressbar(folders):
    if os.path.isdir(pc_folder + outfolder):
        outfolder = outfolder + "/"
        protocol_ids = os.listdir(pc_folder + outfolder)
        protocol_ids = [protocol_id.replace(".xml", "") for protocol_id in protocol_ids if protocol_id.split(".")[-1] == "xml"]

        for protocol_id in protocol_ids:
            if "prot-1935" in protocol_id:
                print(protocol_id)
                metadata = infer_metadata(protocol_id)
                filename = pc_folder + outfolder + protocol_id + ".xml"
                root = etree.parse(filename, parser).getroot()

                root = reclassify_paragrahps(root, classifier)
                root = format_texts(root)
                b = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

                f = open(filename, "wb")
                f.write(b)
                f.close()