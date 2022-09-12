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
    sentences_pc = text_pc.split(".")

    max_len = max(len(sentences_pc), len(sentences_alto))
    incorrect = edit_distance(sentences_alto, sentences_pc)
    correct = max_len - incorrect
    
    return incorrect, incorrect / (incorrect + correct)

class Test(unittest.TestCase):

    # Parla-clarin generated from example OCR XML
    def test_protocols(self):
        folder = "corpus/protocols/"
        testcases = []
        #testcases.append(("1923/prot-1923--ak--22", "test/data/prot-1955--ak--22-008.xml", 8))
        #testcases.append(("1927/prot-1927--fk--7", "test/data/prot-1955--ak--22-008.xml", 8))
        #testcases.append(("1931/prot-1931--ak--10", "test/data/prot-1955--ak--22-008.xml", 8))
        #testcases.append(("1930/prot-1930--fk--33", "test/data/prot-1955--ak--22-008.xml", 8))

        testcases.append(("1955/prot-1955--ak--22", "test/data/prot-1955--ak--22-008.xml", 8))
        
        for protocol_id, alto_path, page in testcases:
            print(protocol_id, alto_path, page)
            root_pc = get_root(f"{folder}{protocol_id}.xml")
            print(root_pc)
            absolute, percentage = calculate_difference(alto_path, root_pc)
            print(absolute, percentage)
            self.assertTrue(absolute < 5, f"{protocol_id}: {page} (absolute)")
            self.assertTrue(percentage < 0.05, f"{protocol_id}: {page} (percentage)")

if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
