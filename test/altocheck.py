import unittest

from lxml import etree
import alto
from nltk import edit_distance

parser = etree.XMLParser(remove_blank_text=True)
def get_root(path):
    root = etree.parse(path, parser).getroot()
    return root

# Official example parla-clarin 
def get_alto_words(path):
    altofile = alto.parse_file(path)
    words = altofile.extract_words()
    return words, len(words)

def get_pc_words(root, page, ns="{http://www.tei-c.org/ns/1.0}"):
    words = []
    correct_page = False
    for body in root.findall(f".//{ns}body"):
        for div in root.findall(f".//{ns}div"):
            for elem in div:
                if elem.tag == f"{ns}pb":
                    page_no = f"{page:03d}.jp2"
                    correct_page = page_no in str(elem.attrib["facs"])
                if correct_page:
                    clean_string = ' '.join([n.strip() for n in elem.itertext()]).strip()
                    words += clean_string.split()

    return words, len(words)

def calculate_difference(alto_path, root_pc):
    words_alto, len_alto = get_alto_words(alto_path)
    words_pc, len_pc = get_pc_words(root_pc, 8)

    text_alto = " ".join(words_alto).replace("-", "").replace(" ", "")
    text_pc  = " ".join(words_pc).replace("-", "").replace(" ", "")
    
    sentences_alto = text_alto.split(".")
    sentences_pc = text_alto.split(".")

    max_len = max(len(sentences_pc), len(sentences_alto))
    incorrect = edit_distance(sentences_alto, sentences_pc)
    correct = max_len - incorrect
    
    return incorrect, incorrect / (incorrect + correct)

class Test(unittest.TestCase):

    # Parla-clarin generated from example OCR XML
    def test_protocols(self):
        schema_path = "schemas/parla-clarin.xsd"
        protocol_id1, msg1 = "1955/prot-1955--ak--22", "Andra kammaren"
        alto_path1 = "test/data/prot-1955--ak--22-008.xml"
        folder = "corpus/protocols/"

        root_pc1 = get_root(f"{folder}{protocol_id1}.xml")

        absolute1, percentage1 = calculate_difference(alto_path1, root_pc1)
        print(absolute1, percentage1)
        self.assertTrue(absolute1 < 5, f"{msg1}: {protocol_id1} (absolute)")
        self.assertTrue(percentage1 < 0.05, f"{msg1}: {protocol_id1} (percentage)")

if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
