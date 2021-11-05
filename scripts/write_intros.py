import pandas as pd
import random
from lxml import etree
import progressbar, argparse
from pyparlaclarin.read import (
    paragraph_iterator
)
from pyriksdagen.segmentation import (
    detect_mp_new
)
from pyriksdagen.utils import protocol_iterators, infer_metadata
from datetime import datetime

def parse_year(s, default=None):
    try:
        return datetime.strptime(s, "%Y-%m-%d").year
    except ValueError:
        if len(s) == 4:
            return int(s)
        else:
            return default

def main(args):
    data_list = []

    found = {}
    start_year = args.start
    end_year = args.end
    tei_ns = "{http://www.tei-c.org/ns/1.0}"

    parser = etree.XMLParser(remove_blank_text=True)
    protocols = list(protocol_iterators("corpus/", start=args.start, end=args.end))

    for protocol in progressbar.progressbar(protocols):
        metadata = infer_metadata(protocol)
        root = etree.parse(protocol, parser).getroot()

        years = [
            parse_year(elem.text.strip(), default=metadata["year"])
            for elem in root.findall(".//" + tei_ns + "docDate")
        ]
        metadata["year"] = max(years)
        for elem in paragraph_iterator(root, output="lxml"):
            if elem.tag == tei_ns + "note":
                note = elem
                if note.attrib.get("type") == "speaker":
                    note_text = note.text.strip()
                    note_text = ' '.join(note_text.split())

                    data_list.append([note_text, metadata["chamber"], metadata["year"], protocol])
        
    df = pd.DataFrame(data_list)
    df.columns = ['intro', 'chamber', 'year', 'protocol']
    df.to_csv('output.csv', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
