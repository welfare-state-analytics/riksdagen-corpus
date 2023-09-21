#!/usr/bin/env python3
"""
Check that all elements with text have IDs.
    - <u> is the oddball, no text (according to lxml), but we want it IDed
    - test checks cannonical elems : seg, u, and note for ID
    - and any other elem with text (elem.text != None or '')
"""
from lxml import etree
from pyriksdagen.utils import elem_iter, protocol_iterators
from tqdm import tqdm
import pandas as pd
import unittest
import warnings




class UndocumentedParagraphWarning(Warning):
    def __init__(self, warnstr):
        self.message = f"There are paragraphs without a valid ID attribute. N={warnstr}"

    def __str__(self):
        return self.message




class Test(unittest.TestCase):


    def count_missing_ids(self, protocol, counter, fails):
        tei_ns = "{http://www.tei-c.org/ns/1.0}"
        xml_ns = "{http://www.w3.org/XML/1998/namespace}"
        canonical_tags = [f'{tei_ns}u', 'u', f'{tei_ns}note', f'{tei_ns}seg']
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse(protocol, parser).getroot()
        for body in root.findall(".//" + tei_ns + "body"):
            for div in body.findall(tei_ns + "div"):
                for elem in div.iter():
                    if elem.tag in canonical_tags or (elem.text and len(elem.text) > 0):
                        if f'{xml_ns}id' not in elem.attrib:
                            counter += 1
                            fails.append([protocol, "no ID attr", elem.sourceline])
                        elif elem.attrib[f'{xml_ns}id'] == None or elem.attrib[f'{xml_ns}id'] == '':
                            # the parser will fail on the above line, so we should never get here.
                            counter += 1
                            fails.append([protocol, "empty ID string or NoneType ", elem.sourceline])
        return counter, fails


    def test_p_has_id(self):
        counter = 0
        fails = []
        f_cols = ["protocol", 'reason', "line_nr"]
        protocols = sorted(list(protocol_iterators("corpus/protocols/", start=1867, end=2022)))
        for p in tqdm(protocols, total=len(protocols)):
            counter, fails = self.count_missing_ids(p, counter, fails)

        if counter > 0:
            warnings.warn(str(counter) +'\n'+ pd.DataFrame(fails, columns=f_cols).to_string(), UndocumentedParagraphWarning)
        self.assertEqual(counter, 0)




if __name__ == '__main__':
    unittest.main()
