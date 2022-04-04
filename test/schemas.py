import unittest

import pandas as pd
from lxml import etree
from pyriksdagen.utils import validate_xml_schema, infer_metadata
from pyriksdagen.download import get_blocks
from pyriksdagen.export import create_tei, create_parlaclarin
from pyriksdagen.db import load_patterns

class Test(unittest.TestCase):

    # Official example parla-clarin 
    def test_official_example(self):
        schema_path = "schemas/parla-clarin.xsd"
        parlaclarin_path = "input/parla-clarin/official-example.xml"
        
        valid = validate_xml_schema(parlaclarin_path, schema_path)
        self.assertEqual(valid, True)

    # Parla-clarin generated from example OCR XML
    def test_protocols(self):
        schema_path = "schemas/parla-clarin.xsd"
        protocol_id1, msg1 = "1955/prot-1955--ak--22", "Andra kammaren"
        protocol_id2, msg2 = "1933/prot-1933--fk--5", "Första kammaren"
        protocol_id3, msg3 = "197879/prot-197879--14", "Enkammarsriksdagen"
        protocol_id4, msg4 = "199596/prot-199596--35", "Digital original, format 1"
        protocol_id5, msg5 = "201011/prot-201011--19", "Digital original, format 2"
        protocol_id6, msg6 = "201819/prot-201819--45", "Digital original, format 3"

        folder = "corpus/protocols/"
        valid1 = validate_xml_schema(f"{folder}{protocol_id1}.xml", schema_path)
        valid2 = validate_xml_schema(f"{folder}{protocol_id2}.xml", schema_path)
        valid3 = validate_xml_schema(f"{folder}{protocol_id3}.xml", schema_path)
        valid4 = validate_xml_schema(f"{folder}{protocol_id4}.xml", schema_path)
        valid5 = validate_xml_schema(f"{folder}{protocol_id5}.xml", schema_path)
        valid6 = validate_xml_schema(f"{folder}{protocol_id6}.xml", schema_path)

        self.assertTrue(valid1, f"{msg1}: {protocol_id1}")
        self.assertTrue(valid2, f"{msg2}: {protocol_id2}")
        self.assertTrue(valid3, f"{msg3}: {protocol_id3}")
        self.assertTrue(valid4, f"{msg4}: {protocol_id4}")
        self.assertTrue(valid5, f"{msg5}: {protocol_id5}")
        self.assertTrue(valid6, f"{msg6}: {protocol_id6}")

if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
