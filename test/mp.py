import unittest

import pandas as pd
from lxml import etree
from pyriksdagen.utils import validate_xml_schema, infer_metadata
from pyriksdagen.download import get_blocks
from pyriksdagen.export import create_tei, create_parlaclarin
from pyriksdagen.db import load_patterns, filter_db, load_ministers
from pathlib import Path
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

            false_whos = []
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
                                    false_whos.append(who)

            return found, false_whos

        folder = "corpus/"
        wikidata = pd.read_csv("corpus/wiki-data/observation.csv")
        wiki_minister_db = load_ministers('corpus/wiki-data/minister.json')
        wikidata = pd.concat([wikidata, wiki_minister_db])
        wd_db = wikidata[["start", "end"]]
        wd_db["id"] = wikidata["wiki_id"]
        wd_db["start"] = pd.DatetimeIndex(pd.to_datetime(wd_db["start"], errors="coerce")).year
        wd_db["end"] = pd.DatetimeIndex(pd.to_datetime(wd_db["end"], errors="coerce")).year
        wd_db = wd_db.fillna(2024)

        mp_db = pd.read_csv("corpus/members_of_parliament.csv")[["id", "start", "end"]]
        sk_db = pd.read_csv("corpus/members_of_parliament_sk.csv")[["id", "start", "end"]]
        minister_db = pd.read_csv("corpus/ministers.csv")[["id", "start", "end"]]
        talman_db = pd.read_csv("corpus/talman.csv")[["id", "start", "end"]]
        minister_db["start"] = pd.DatetimeIndex(minister_db["start"]).year
        minister_db["end"] = pd.DatetimeIndex(minister_db["end"]).year
        talman_db = talman_db[talman_db["start"].notnull()]
        talman_db = talman_db[talman_db["end"].notnull()]
        talman_db["start"] = pd.to_datetime(talman_db["start"], errors="coerce")
        talman_db["end"] = pd.to_datetime(talman_db["end"], errors="coerce")
        talman_db["start"] = pd.DatetimeIndex(talman_db["start"]).year
        talman_db["end"] = pd.DatetimeIndex(talman_db["end"]).year
        mp_db = pd.concat([wd_db, mp_db, minister_db, talman_db, sk_db])
        print(mp_db)
        mp_ids = {}

        failed_protocols = []
        for outfolder in progressbar.progressbar(list(Path(folder).glob("*/"))):
            for protocol_path in outfolder.glob("*.xml"):
                protocol_id = protocol_path.stem
                path_str = str(protocol_path.resolve())
                root = etree.parse(path_str, parser).getroot()
                found, false_whos = test_one_protocol(root, mp_ids, mp_db)
                if not found:
                    failed_protocols.append(protocol_id + " (" + false_whos[0] + ")")

        print("Protocols with inactive MPs tagged as speakers:", ", ".join(failed_protocols))
        self.assertEqual(len(failed_protocols), 0)




if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
