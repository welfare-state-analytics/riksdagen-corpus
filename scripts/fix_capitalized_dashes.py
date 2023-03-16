"""
Concatenate split names of format "PERS- SON" into "PERSSON"
"""
from lxml import etree
import pandas as pd
import os, progressbar, re
import argparse
from pyparlaclarin.read import paragraph_iterator
from pyparlaclarin.refine import format_texts
from pyriksdagen.utils import protocol_iterators
from tqdm import tqdm


def main(args):
    pattern = "([A-ZÀ-Þ]{2,10})(- )([A-ZÀ-Þ]{2,10})"
    e = re.compile(pattern)

    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
    #print(protocols)
    parser = etree.XMLParser(remove_blank_text=True)

    for protocol in tqdm(protocols, total=len(protocols)):
        with open(protocol) as f:
            root = etree.parse(f, parser).getroot()

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

            with open(protocol, "wb") as f:
                f.write(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=1920, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    args = parser.parse_args()
    main(args)
