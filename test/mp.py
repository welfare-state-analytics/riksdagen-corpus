import unittest

import pandas as pd
from lxml import etree
from pyriksdagen.utils import validate_xml_schema, infer_metadata
from pyriksdagen.download import get_blocks
from pyriksdagen.export import create_tei, create_parlaclarin
from pyriksdagen.segmentation import find_instances, apply_instances
from pyriksdagen.db import load_patterns, filter_db
import os
import progressbar

class Test(unittest.TestCase):

    # Official example parla-clarin 
    def test_protocol(self):
        parser = etree.XMLParser(remove_blank_text=True)

        def test_one_protocol(root, mp_ids, mp_db):
            found = True
            years = []
            date = None
            for docDate in root.findall(".//{http://www.tei-c.org/ns/1.0}docDate"):
                docDateYear = docDate.attrib.get("when", "unknown")
                date = docDateYear
                docDateYear = int(docDateYear.split("-")[0])
                years.append(docDateYear)

            for year in years:
                if year not in mp_ids:
                    year_db = filter_db(mp_db, year=year)
                    ids = list(year_db["id"])
                    mp_ids[year] = ids

            for body in root.findall(".//{http://www.tei-c.org/ns/1.0}body"):
                for div in body.findall("{http://www.tei-c.org/ns/1.0}div"):
                    for ix, elem in enumerate(div):
                        if elem.tag == "{http://www.tei-c.org/ns/1.0}u":
                            who = elem.attrib.get("who", "unknown")
                            if who != "unknown":
                                elem_found = False
                                for year in years:
                                    if who in mp_ids[year]:
                                        elem_found = True

                                if not elem_found:
                                    found = False

            return found

        folder = "corpus/"
        mp_db = pd.read_csv("corpus/members_of_parliament.csv")
        mp_ids = {}

        failed_protocols = []
        for outfolder in progressbar.progressbar(os.listdir(folder)):
            outfolder = outfolder + "/"
            if os.path.isdir(folder + outfolder):
                for protocol_id in os.listdir(folder + outfolder):
                    protocol_id = protocol_id.split(".")[0]
                    root = etree.parse(folder + outfolder + protocol_id + ".xml", parser).getroot()
                    if not test_one_protocol(root, mp_ids, mp_db):
                        failed_protocols.append(protocol_id)

        print("Protocols with inactive MPs tagged as speakers:", ", ".join(failed_protocols))
        self.assertEqual(len(failed_protocols) == 0, True)




if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
