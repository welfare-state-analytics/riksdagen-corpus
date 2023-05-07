import unittest
import os
from lxml import etree
import alto
from nltk import edit_distance
import requests
import random
from pathlib import Path

parser = etree.XMLParser(remove_blank_text=True)
def get_root(path):
    root = etree.parse(path, parser).getroot()
    return root

# Official example parla-clarin 
def get_alto_words(content):
    try:
        altofile = alto.parse(content)
        words = altofile.extract_words()
    except:
        print("ALTO XML parsing unsuccessful")
        return None
    return words

def get_pc_words(root, page="random", ns="{http://www.tei-c.org/ns/1.0}"):
    if page == "random":
        pbs = list(root.findall(f".//{ns}pb"))
        pb_sources = [pb.attrib["facs"] for pb in pbs]
        page_strs = [page.split(".jp2")[0][-3:] for page in pb_sources]
        pages = [int(page_str) for page_str in page_strs]
        page = random.choice(pages)
        print("PAGE:", page)

    words = []
    correct_page = False
    alto_url = None
    for body in root.findall(f".//{ns}body"):
        for div in root.findall(f".//{ns}div"):
            for elem in div:
                if elem.tag == f"{ns}pb":
                    page_no = f"{page:03d}.jp2"
                    correct_page = page_no in str(elem.attrib["facs"])
                    if correct_page:
                        alto_url = elem.attrib["facs"].replace(".jp2/_view", ".xml")
                if correct_page:
                    clean_string = ' '.join([n.strip() for n in elem.itertext()]).strip()
                    words += clean_string.split()

    return words, alto_url, page

def clean_sentence(s):
    # Make test indifferent to hyphens and linebreaks
    s = s.replace("-", "").replace(" ", "")

    # Standardize punctuation
    s = s.replace("?", ".").replace("!", ".").replace(",", ".")

    # Make test indifferent to §/$/8 which are not well
    # differentiated by Tesseract
    s = s.replace("$", "§")
    s = s.replace("8", "§")
    return s

def calculate_difference(root_pc, page="random", auth=None):
    words_pc, alto_url, page = get_pc_words(root_pc, page=page)
    r = requests.get(alto_url, auth=auth)
    if r.content is None:
        print("HTTP response has no content")
        return None#0, 0.0, 0
    words_alto = get_alto_words(r.content)
    if words_alto is None:
        return None#0, 0.0, 0

    text_alto = " ".join(words_alto)
    text_alto = clean_sentence(text_alto)
    text_pc  = " ".join(words_pc)
    text_pc = clean_sentence(text_pc)

    sentences_alto = text_alto.split(".")
    sentences_pc = text_pc.split(".")

    max_len = max(len(sentences_pc), len(sentences_alto))
    incorrect = edit_distance(sentences_alto, sentences_pc)
    correct = max_len - incorrect
    
    return incorrect, incorrect / (incorrect + correct), page

class Test(unittest.TestCase):
    random.seed(429)
    # Parla-clarin generated from example OCR XML
    def test_protocols(self):
        folder = "corpus/protocols/"
        p = Path(folder)
        auth = os.environ.get("KBLAB_USERNAME"), os.environ.get("KBLAB_PASSWORD")

        all_testcases = []
        decades = list(range(1860, 1990, 10))
        print(f"Testing decades: {decades}")
        for decade in decades:
            testcases = list(p.glob(f"{decade // 10}*/*.xml"))
            testcases = sorted(testcases, key=lambda v: random.random())
            all_testcases = all_testcases + sorted(testcases[:100])
        
        percentage_fail = []
        absolute_fail = []
        loading_fail = []
        for protocol_path in all_testcases:
            print(protocol_path)
            protocol_id = str(protocol_path.stem)
            root_pc = get_root(protocol_path.relative_to("."))
            difference = calculate_difference(root_pc, auth=auth)
            if difference is None:
                loading_fail.append(protocol_id)
            else:
                absolute, percentage, page = difference
                print(f"{absolute} errors, {percentage * 100:.1f}%")
                if absolute >= 3:
                    print(f"{protocol_id}: {page} (absolute) over limit")
                    absolute_fail.append(protocol_id)
                if percentage >= 0.05:
                    print(f"{protocol_id}: {page} (percentage) over limit")
                    percentage_fail.append(protocol_id)
        
        absolute_fail_ratio = len(absolute_fail) / len(all_testcases)
        percentage_fail_ratio = len(percentage_fail) / len(all_testcases)
        succesful_loading_ratio = len(loading_fail) / len(all_testcases)
        print(f"Proportion of protocols with over 3 mismatching sentences: {absolute_fail_ratio}")
        print(f"Proportion of protocols with over 0.05% mismatching sentences: {percentage_fail_ratio}")
        self.assertTrue(absolute_fail_ratio < 0.03, f"Absolute ratio {absolute_fail_ratio} too high {absolute_fail}")
        self.assertTrue(percentage_fail_ratio < 0.05, f"Percentage ratio {percentage_fail_ratio} too high {percentage_fail}")
        self.assertTrue(succesful_loading_ratio < 0.03, f"Loading ratio {succesful_loading_ratio} too high {loading_fail}")

        # Perfect matching is unreasonable and a sign of an error in the test
        self.assertTrue(absolute_fail_ratio > 0.0, f"Absolute ratio zero {absolute_fail}")
        self.assertTrue(percentage_fail_ratio > 0.0, f"Percentage ratio zero {percentage_fail}")

if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()
