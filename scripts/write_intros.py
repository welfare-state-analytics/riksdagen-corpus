"""
Scrape all intros from the parla-clarin files for a specified time range
"""
import pandas as pd
import random
from lxml import etree
import progressbar, argparse
from pyparlaclarin.read import (
    paragraph_iterator
)
from pyriksdagen.utils import protocol_iterators, infer_metadata

def first_date(root):
    for docDate in root.findall(".//{http://www.tei-c.org/ns/1.0}docDate"):
        date_string = docDate.text
        break
    return date_string

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

        docDates = root.findall(".//{http://www.tei-c.org/ns/1.0}docDate")
        docDate = docDates[0].text
        year = docDate[:4]

        for elem in paragraph_iterator(root, output="lxml"):
            if elem.tag == tei_ns + "note":
                note = elem
                if note.attrib.get("type") == "speaker":
                    note_text = note.text.strip()
                    note_text = ' '.join(note_text.split())

                    data_list.append([note_text, metadata["chamber"], year, protocol])

    df = pd.DataFrame(data_list)
    df.columns = ['intro', 'chamber', 'year', 'protocol']
    df.to_csv(args.output, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--output", type=str, default="output.csv")
    args = parser.parse_args()
    main(args)
