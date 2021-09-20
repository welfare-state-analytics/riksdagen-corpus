"""
Concatenate split names of format "PERS- SON" into "PERSSON"
"""
from lxml import etree
import pandas as pd
import os, progressbar, re
from pyparlaclarin.read import paragraph_iterator
from pyparlaclarin.refine import format_texts


def main():
    pattern = "([A-ZÅÄÖÉ]{2,10})(- )([A-ZÅÄÖÉ]{2,10})"
    e = re.compile(pattern)
    pc_folder = "corpus/"
    folders = os.listdir(pc_folder)
    parser = etree.XMLParser(remove_blank_text=True)
    for outfolder in progressbar.progressbar(folders):
        if os.path.isdir(pc_folder + outfolder):
            outfolder = outfolder + "/"
            protocol_ids = os.listdir(pc_folder + outfolder)
            for protocol_id in progressbar.progressbar(protocol_ids):
                filename = pc_folder + outfolder + protocol_id
                root = etree.parse(filename, parser).getroot()

                for elem in paragraph_iterator(root, output="lxml"):
                    pass  # if elem.text is not None:
                    #    print(elem.text)
                    txt = elem.text
                    if txt is not None and len(e.findall(txt)) > 0:
                        elem.text = re.sub(pattern, r"\1\3", txt)
                    # e.match(string)

                root = format_texts(root)

                b = etree.tostring(
                    root, pretty_print=True, encoding="utf-8", xml_declaration=True
                )

                f = open(filename, "wb")
                f.write(b)
                f.close()


if __name__ == "__main__":
    main()
