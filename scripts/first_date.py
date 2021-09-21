from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.refine import detect_date
from pyriksdagen.utils import infer_metadata
from pyparlaclarin.read import get_dates
from lxml import etree
import pandas as pd
import os
import progressbar
import numpy as np

"""
Scrapes protocols for first docDate tag
OBS requires pyriksdagen locally
"""

def first_date(root):
    for docDate in root.findall(".//{http://www.tei-c.org/ns/1.0}docDate"):
        date_string = docDate.text
        break
    return date_string

pc_folder = "corpus/"
folders = os.listdir(pc_folder)
folders = [folder for folder in folders if folder.isnumeric()]
folders = sorted(folders)

data_list = []

parser = etree.XMLParser(remove_blank_text=True)
for outfolder in folders:
    if os.path.isdir(pc_folder + outfolder):
        outfolder = outfolder + "/"
        protocol_ids = os.listdir(pc_folder + outfolder)
        protocol_ids = [protocol_id.replace(".xml", "") for protocol_id in protocol_ids if protocol_id.split(".")[-1] == "xml"]
        
        for protocol_id in protocol_ids:
            if protocol_id.endswith('--1'):

                filename = pc_folder + outfolder + protocol_id + ".xml"
                root = etree.parse(filename, parser).getroot()
                
                date = first_date(root)
                
                data_list.append([date, filename])

df = pd.DataFrame(data_list)
df.columns = ['date', 'file']
df.to_csv('riksdagen_opening_dates.csv', index=False)


