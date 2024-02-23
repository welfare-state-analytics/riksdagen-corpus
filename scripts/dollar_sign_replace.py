"""
Fix a common OCR error: § is replaced with $. Only do this if we are sure of the error.
"""
import argparse
from pyparlaclarin.refine import format_texts

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

def dollar_signs(root, exp_dollar_1, exp_dollar_2):
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
                    elif exp_dollar_1.search(elemtext) is not None:
                        m = exp_dollar_1.search(elemtext).group(0)
                        m_new = "§" + m[1:]
                        elem.text = elem.text.replace(m, m_new)
                    elif exp_dollar_2.search(elemtext) is not None:
                        m = exp_dollar_2.search(elemtext).group(0)
                        m_new = m.replace("$", "§")
                        elem.text = elem.text.replace(m, m_new)

    return root

def join_soft_hyphens_p(t):
    t = " ".join(t.split())
    t = re.sub(' ?\u00ad ?', '', t)
    return t

def join_soft_hyphens(root, soft_hyphen):
    for body in root.findall(f".//{tei_ns}body"):
        for div in body.findall(f"{tei_ns}div"):
            for elem in div:
                if elem.tag == f"{tei_ns}u":
                    for seg in elem:
                        if seg.text is not None:
                            seg.text = join_soft_hyphens_p(seg.text)
                elif elem.text is not None:
                    elem.text = join_soft_hyphens_p(elem.text)
    root = format_texts(root, padding=10)
    return root

def main(args):
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))    
    print(protocols)
    parser = etree.XMLParser(remove_blank_text=True)
    
    exp_dollar_1 = re.compile("^8 [0-9]{1,2}\.")
    exp_dollar_2 = re.compile("^[0-9]{1,2} ?\$")

    soft_hyphen = re.compile("^[0-9]{1,2} ?\$")

    for protocol in tqdm(protocols, total=len(protocols)):
        with open(protocol) as f:
            root = etree.parse(f, parser).getroot()

        root = dollar_signs(root, exp_dollar_1, exp_dollar_2)
        root = join_soft_hyphens(root, soft_hyphen)
        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )

        with open(protocol, "wb") as f:
            f.write(b)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=1920, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    parser.add_argument("--parallel", type=int, default=1, help="type=int, default=1: nymber of parallel...doesn't seem to do anything.")
    args = parser.parse_args()
    main(args)
