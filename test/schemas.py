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
    def test_generated_example(self):
        schema_path = "schemas/parla-clarin.xsd"
        protocol_id = "prot-198990--93"
        fname = "prot_198990__93-031.xml"
        
        # Package argument can be None since the file is already saved on disk
        content_blocks = get_blocks(protocol_id, None)
        metadata = infer_metadata(fname.split(".")[0])
        tei = create_tei(protocol, metadata)
        parla_clarin_str = create_parlaclarin(tei, metadata)
        print("pc str created..")
        
        parlaclarin_path = "input/parla-clarin/generated-example.xml"
        f = open(parlaclarin_path, "w")
        f.write(parla_clarin_str)
        f.close()
        
        valid = validate_xml_schema(parlaclarin_path, schema_path)
        self.assertEqual(valid, True)

    # Parla-clarin generated from example OCR XML
    def test_generated_example(self):
        schema_path = "schemas/parla-clarin.xsd"
        protocol_id1 = "1955/prot-1955--ak--22" # Andra kammaren
        protocol_id2 = "1933/prot-1933--fk--5" # Första kammaren
        protocol_id3 = "197879/prot-197879--14" # Enkammarsriksdagen
        protocol_id4 = "199596/prot-199596--35" # Digital original

        folder = "corpus/protocols/"
        parlaclarin_path1 = folder + protocol_id1 + ".xml"
        parlaclarin_path2 = folder + protocol_id2 + ".xml"
        parlaclarin_path3 = folder + protocol_id3 + ".xml"
        parlaclarin_path4 = folder + protocol_id4 + ".xml"

        valid1 = validate_xml_schema(parlaclarin_path1, schema_path)
        valid2 = validate_xml_schema(parlaclarin_path2, schema_path)
        valid3 = validate_xml_schema(parlaclarin_path3, schema_path)
        valid4 = validate_xml_schema(parlaclarin_path4, schema_path)

        self.assertEqual(valid1, True)
        self.assertEqual(valid2, True)
        self.assertEqual(valid3, True)
        self.assertEqual(valid4, True)


if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
