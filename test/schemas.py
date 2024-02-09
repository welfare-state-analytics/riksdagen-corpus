import unittest

import pandas as pd
from lxml import etree
from pyriksdagen.utils import validate_xml_schema, infer_metadata
from pyriksdagen.db import load_patterns
from pathlib import Path
import random
import xmlschema
random.seed(429)

class Test(unittest.TestCase):

    def test_official_example(self):
        """
        Validate the official ParlaClarin example provided by ParlaClarin.
        """
        schema_path = "schemas/parla-clarin.xsd"
        parlaclarin_path = "input/parla-clarin/official-example.xml"
        
        valid = validate_xml_schema(parlaclarin_path, schema_path)
        self.assertEqual(valid, True)

    def test_protocols(self):
        """
        For each year, randomly choose a file and check it against the ParlaClarin schema.
        """
        schema_path = "schemas/parla-clarin.xsd"
        folder = "corpus/protocols/"
        years = sorted([p.stem for p in Path(folder).glob("*") if p.is_dir()])
        
        self.assertGreaterEqual(len(years), 1, "We should have a nonempty set of data folders")

        schema = xmlschema.XMLSchema(schema_path)
        for year in years:
            files_year = list(Path(folder).glob(f"{year}/*.xml"))
            self.assertGreaterEqual(len(files_year), 1, f"For year(s) {year}, we should have a nonempty set of XML files")
            file = random.choice(files_year)
            print(year, file.stem)
            valid = validate_xml_schema(file.absolute(), schema_path, schema=schema)
            self.assertTrue(valid, f"{year}s: {file.stem}")


if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
