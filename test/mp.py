import unittest

import pandas as pd
from lxml import etree
from pyriksdagen.utils import validate_xml_schema, infer_metadata
from pyriksdagen.db import load_patterns, filter_db, load_ministers, load_metadata
from pathlib import Path
import progressbar
import warnings

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

            false_whos = []
            whos = set()
            for body in root.findall(".//{http://www.tei-c.org/ns/1.0}body"):
                for div in body.findall("{http://www.tei-c.org/ns/1.0}div"):
                    for ix, elem in enumerate(div):
                        if elem.tag == "{http://www.tei-c.org/ns/1.0}u":
                            who = elem.attrib.get("who", "unknown")
                            if who != "unknown":
                                whos.add(who)
                                elem_found = False
                                for year in years:
                                    if who in mp_ids[year]:
                                        elem_found = True

                                if not elem_found:
                                    found = False
                                    false_whos.append(who)

            # Check for dead or child speakers
            dead_whos = []
            child_whos = []
            mp_doa = mp_db[['id', 'born', 'dead']].drop_duplicates().reset_index(drop=True)
            mp_doa['born'] = mp_doa['born'].fillna('0000')
            mp_doa['dead'] = mp_doa['dead'].fillna('9999')

            fronts = root.findall(".//{http://www.tei-c.org/ns/1.0}front")
            heads = fronts[0].findall(".//{http://www.tei-c.org/ns/1.0}head")
            for who in whos:
                mp = mp_doa.loc[mp_doa['id'] == who]

                warning_text = f"Speaker {who} not found in db. Protocol {heads[0].text}"
                self.assertGreaterEqual(len(mp), 1, warning_text)

                born = min(mp['born'].apply(lambda x: int(x[:4])))
                dead = max(mp['dead'].apply(lambda x: int(x[:4])))
                if max(years) > dead:
                    dead_whos.append(who)
                if max(years) < born + 15:
                    child_whos.append(who)
            
            return found, false_whos, dead_whos, child_whos

        # new
        folder = "corpus/protocols"
        *_, mp_db, minister_db, speaker_db = load_metadata()
        mp_db = pd.concat([mp_db, minister_db, speaker_db])

        mp_ids = {}

        failed_protocols = []
        for outfolder in progressbar.progressbar(list(Path(folder).glob("*/"))):
            for protocol_path in outfolder.glob("*.xml"):
                protocol_id = protocol_path.stem
                path_str = str(protocol_path.resolve())
                root = etree.parse(path_str, parser).getroot()
                found, false_whos, dead_whos, child_whos = test_one_protocol(root, mp_ids, mp_db)
                if not found:
                    failed_protocols.append(protocol_id + " (" + false_whos[0] + ")")

        print("Protocols with inactive MPs tagged as speakers:", ", ".join(failed_protocols))
        print("Dead MPs tagged as speakers:", ", ".join(dead_whos))
        print("Children MPs tagged as speakers:", ", ".join(child_whos))

        self.assertEqual(len(failed_protocols), 0)




if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
