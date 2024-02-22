#!/usr/bin/env python3
"""
Test there are no empty speeches.
"""
from .pytestconfig import fetch_config
from datetime import datetime
from lxml import etree
from pyriksdagen.utils import (
    parse_protocol,
    protocol_iterators,
)
from tqdm import tqdm
import pandas as pd
import unittest
import warnings




class EmptyElement(Warning):

    def __init__(self, m):
        self.message = m

    def __str__(self):
        return self.message




class Test(unittest.TestCase):

    def test_no_empty_speech(self):
        """
        Test protocol has no empty `u` or `seg` elements
        """
        rows = []
        protocols = sorted(list(protocol_iterators("corpus/protocols/",
                                                   start=1867,
                                                   end=2022)))
        for p in tqdm(protocols, total=len(protocols)):
            root, ns = parse_protocol(p, get_ns=True)
            for elem in root.iter(f'{ns["tei_ns"]}u'):
                if len(elem) == 0:
                    if f'{ns["xml_ns"]}id' in elem.attrib:
                        u_id = elem.attrib[f'{ns["xml_ns"]}id']
                        rows.append([p, "u", u_id])
                        warnings.warn(f"Empty u-elem: {p}, {u_id}", EmptyElement)
                else:
                    for seg in elem:
                        if not seg.text or seg.text.strip() == '':
                            if f'{ns["xml_ns"]}id' in seg.attrib:
                                seg_id = seg.attrib[f'{ns["xml_ns"]}id']
                                rows.append([p, "seg", seg_id])
                                warnings.warn(f"Empty seg-elem: {p}, {seg_id}", EmptyElement)
        if len(rows) > 0:
            config = fetch_config("empty-speech")
            if config and config["write_empty_speeches"]:
                now = datetime.now().strftime('%Y%m%d-%H%M%S')
                cols = ["protocol", "elem", "elem_id"]
                df = pd.DataFrame(rows, columns=cols)
                df.to_csv(
                    f"{config['test_out_path']}empty-speech_{now}.csv",
                    sep=';',
                    index=False)

        self.assertEqual(len(rows), 0)




if __name__ == '__main__':
    unittest.main()
