import unittest
import os
from lxml import etree
from pyriksdagen.utils import protocol_iterators
import random
from pathlib import Path
import progressbar

TEI_NS ="{http://www.tei-c.org/ns/1.0}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"


parser = etree.XMLParser(remove_blank_text=True)
def get_root(path):
    root = etree.parse(path, parser).getroot()
    return root

def check_next_prev_coherence(root):
    """
    Check that

    a) all 'next' attributes point to next <u> element
    b) all 'prev' attributes point to previous <u> element

    """
    
    next_attrib = None
    prev_id = None

    for body in root.findall(f".//{TEI_NS}body"):
        for div in root.findall(f".//{TEI_NS}div"):
            for elem in div:
                if elem.tag == f"{TEI_NS}u":

                    if next_attrib is not None:
                        if next_attrib != elem.attrib[f"{XML_NS}id"]:
                            return False

                    next_attrib = elem.attrib.get("next")

                    if "prev" in elem.attrib:
                        if prev_id != elem.attrib["prev"]:
                            return False

                    prev_id = elem.attrib[f"{XML_NS}id"]
    return True


class Test(unittest.TestCase):

    def test_next_prev(self):
        for protocol_path in progressbar.progressbar(sorted(list(protocol_iterators("corpus/protocols/")))):
            root = get_root(protocol_path)
            coherent_protocol = check_next_prev_coherence(root)

            self.assertTrue(coherent_protocol, f"Protocol {protocol_path} has incoherent 'next'/'prev' tagging")

if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
