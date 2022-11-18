"""
Fix a common OCR error: § is replaced with $. Only do this if we are sure of the error.
"""
import argparse
from pyriksdagen.db import load_metadata
from pyriksdagen.refine import redetect_protocol
from pyriksdagen.utils import protocol_iterators
from pyriksdagen.segmentation import join_text
from tqdm import tqdm
from multiprocessing import Pool
from functools import partial
from lxml import etree
import re

tei_ns ="{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"


def main(args):
    exp = re.compile("^8 [0-9]{1,2}\.")
    exp2 = re.compile("^[0-9]{1,2} ?\$")

    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))    
    parser = etree.XMLParser(remove_blank_text=True)
    
    for protocol in tqdm(protocols, total=len(protocols)):
        with open(protocol) as f:
            root = etree.parse(f, parser).getroot()

        for body in root.findall(f".//{tei_ns}body"):
            for div in body.findall(f"{tei_ns}div"):
                for elem in div:
                    if elem.tag == f"{tei_ns}note":
                        elemtext = " ".join(elem.text.split())

                        if "$" == elemtext[0]:
                            #print(elemtext)
                            #pass
                            elem.text = elem.text.replace("$", "§")
                            print(elem.text)
                        elif exp.search(elemtext) is not None:
                            m = exp.search(elemtext).group(0)
                            m_new = "§" + m[1:]
                            elem.text = elem.text.replace(m, m_new)
                        elif exp2.search(elemtext) is not None:
                            m = exp2.search(elemtext).group(0)
                            m_new = m.replace("$", "§")
                            elem.text = elem.text.replace(m, m_new)


        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )

        with open(protocol, "wb") as f:
            f.write(b)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--parallel", type=int, default=1)
    args = parser.parse_args()
    main(args)
