#!/usr/bin/env python3
from lxml import etree
from pyriksdagen.utils import protocol_iterators, elem_iter
import os
import pandas as pd




here = os.path.dirname(__file__)




def count_words(t):
    return len(t.split(' '))




def count_speaches(protocol):
    speeches = 0
    words = 0
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()
    tei = root.find(f"{tei_ns}TEI")

    for tag, elem in elem_iter(root):
        if tag in ["note"]:
            if 'type' in elem.attrib:
                if elem.attrib['type'] == 'speaker':
                    speeches += 1
        if tag == "u":
            for segelem in elem:
                words += count_words(segelem.text)

    return speeches, words




def main():

    p = {}
    s = {}
    w = {}

    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=1867, end=2022)))
    for prot in protocols:
        year = prot.split('/')[-1].split('-')[1][:4]
        print(prot, year)
        if year not in p:
            p[year] = 0
        if year not in s:
            s[year] = 0
        if year not in w:
            w[year] = 0
        p[year] += 1
        #print(p,s)
        intros, words = count_speaches(prot)
        s[year] += intros
        w[year] += words
        print(prot, year, intros, words)

    rows = []
    cols = ["year", "prot", "intros", "words"]
    for k, v in p.items():
        rows.append([int(k), v, s[k], w[k]])
    df = pd.DataFrame(rows, columns = cols)
    df.to_csv(f"{here}/_psw-counts.csv", index=False, sep=';')




if __name__ == '__main__':
    main()
