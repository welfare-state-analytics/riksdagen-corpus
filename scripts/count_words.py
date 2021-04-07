from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.utils import infer_metadata
from lxml import etree
import pandas as pd
import os, progressbar
import re
import seaborn as sns
from matplotlib import pyplot as plt

root = ""#"../"
pc_folder = root + "corpus/"
folders = os.listdir(pc_folder)

word_freqs = {}
words = ["finland", "norge"]
parser = etree.XMLParser(remove_blank_text=True)
for outfolder in progressbar.progressbar(folders):
    if os.path.isdir(pc_folder + outfolder):
        outfolder = outfolder + "/"
        protocol_ids = os.listdir(pc_folder + outfolder)
        protocol_ids = [protocol_id.replace(".xml", "") for protocol_id in protocol_ids if protocol_id.split(".")[-1] == "xml"]

        for protocol_id in protocol_ids:
            metadata = infer_metadata(protocol_id)
            filename = pc_folder + outfolder + protocol_id + ".xml"
            root = etree.parse(filename, parser).getroot()

            year = metadata["year"]
            #print(year, type(year))
            years = [int(elem.attrib.get("when").split("-")[0]) for elem in root.findall(".//{http://www.tei-c.org/ns/1.0}docDate")]

            if not year in years:
                year = years[0]

            for div in root.findall(".//{http://www.tei-c.org/ns/1.0}div"):
                for elem in div:
                    text = "\n".join(elem.itertext()).lower()
                    for wd in words:
                        if wd in text:
                            if year not in word_freqs:
                                word_freqs[year] = {}
                            d = word_freqs.get(year)
                            d[wd] = d.get(wd, 0) + 1

#print(word_freqs)   

rows = []
for year, d in word_freqs.items():
    row = [year] + [None] * len(words)

    for ix, word in enumerate(words):
        row[ix + 1] = d.get(word, 0)
    rows.append(row)


columns = ["year"] + words
df = pd.DataFrame(rows, columns=columns)

df = df.sort_values("year")
print(df)

df.index = df["year"]

df = df.drop("year", axis=1)
sns.set_theme()
sns.lineplot(
    data=df
    )

plt.show()
