#!/usr/bin/env python3
from lxml import etree
from pyriksdagen.utils import protocol_iterators, elem_iter
import os
import pandas as pd



print('..reading in Tomas\' dataframe...')
here = os.path.dirname(__file__)
tomas = pd.read_feather("corpus/_quality_assessment/speech_index_0.10.0.feather")
tomas_intro_ids = tomas['who_intro_id'].values
print('..read.')


def count_words(t):
    tokens = [_.strip() for _ in t.split(' ') if len(_) > 0 and _ != '\n']
    return len(tokens)


def dump_empty(introelem):
    c = 0
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    intro_id = introelem.attrib[f'{xml_ns}id']
    if intro_id not in tomas_intro_ids:
        c += 1
        print(intro_id, c)
    return c


def count_speaches(protocol):
    speeches = 0
    words = 0
    drop = 0
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
                    #drop += dump_empty(elem)
        if tag == "u":
            for segelem in elem:
                words += count_words(segelem.text)
    pb = tei.findall(f"{tei_ns}pb")
    return speeches, words, len(pb), drop






def main():

    p = {}
    s = {}
    dropped_s = {}
    w = {}
    pages = {}

    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=1920, end=2022)))
    for prot in protocols:
        year = prot.split('/')[-1].split('-')[1][:4]
        #print(prot, year)
        if year not in p:
            p[year] = 0
        if year not in s:
            s[year] = 0
        if year not in w:
            w[year] = 0
        if year not in dropped_s:
            dropped_s[year] = 0
        p[year] += 1
        if year not in pages:
            pages[year] = 0
        #print(p,s)
        intros, words, pagen, drop = count_speaches(prot)
        s[year] += intros
        w[year] += words
        pages[year] += pagen
        dropped_s[year] += drop
        print(prot, year, pagen, intros, drop, words)

    rows = []
    cols = ["year", "prot", "pages", "intros","t_speeches", "words", ]
    for k, v in p.items():
        t_speeches = len(tomas.loc[tomas['year']==int(k)])
        rows.append([int(k), v, pages[k], s[k], t_speeches, w[k]])
    df = pd.DataFrame(rows, columns = cols)
    df.to_csv(f"{here}/_psw-counts.csv", index=False, sep=';')




if __name__ == '__main__':
    main()
