#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides useful utilities for the other modules as well as for general use.
"""

import lxml
from lxml import etree
import xml.etree.ElementTree as et
import sys, re, os
from bs4 import BeautifulSoup
import pandas as pd
import hashlib

def infer_metadata(filename):
    metadata = dict()
    filename = filename.replace("-", "_")
    metadata["protocol"] = filename.split("/")[-1].split(".")[0]
    split = filename.split("/")[-1].split("_")
    
    # Year
    for s in split:
        s = s[:4]
        if s.isdigit():
            year = int(s)
            if year > 1800 and year < 2100:
                metadata["year"] = year

    # Chamber
    metadata["chamber"] = "Enkammarriksdagen"
    if "_ak_" in filename:
        metadata["chamber"] = "Andra kammaren"
    elif "_fk_" in filename:
        metadata["chamber"] = "Första kammaren"
    
    try:
        metadata["number"] = int(split[-1])
    except:
        print("Number parsing unsuccesful", filename)
        
    return metadata

def element_hash(elem, protocol_id="", chars=16):
    """
    Calculate a deterministic hash for an XML element
    """
    # The hash seed consists of 
    # 1. Element text without line breaks
    elem_text = elem.text
    if elem_text is None:
        elem_text = ""
    elem_text = elem_text.strip().replace("\n", " ")
    elem_text = ' '.join(elem_text.split())
    # 2. The element tag
    elem_tag = elem.tag
    # 3. The element attributes in alphabetical order,
    # excluding the XML ID and XML n
    xml_id = "{http://www.w3.org/XML/1998/namespace}id"
    xml_n = "{http://www.w3.org/XML/1998/namespace}n"
    n = "n"
    excluded = [xml_id, xml_n, n, "prev", "next"]
    elem_attrib = {key: value for key, value in elem.attrib.items() if key not in excluded}
    elem_attrib = str(sorted(elem_attrib.items()))
    seed = protocol_id + "\n" + elem_text + "\n" + elem_tag + "\n" + elem_attrib
    encoded_seed = seed.encode("utf-8")
    # Finally, the hash is calculated via MD5
    digest = hashlib.md5(encoded_seed).hexdigest()
    return digest[:chars]

def _clean_html(raw_html):
    # Clean the HTML code in the Riksdagen XML text format
    raw_html = raw_html.replace("\n", " NEWLINE ")
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = cleantext.replace(" NEWLINE ", "\n")
    return cleantext

def read_riksdagen_xml(path):
    """
    Read Riksdagen XML text format and return a tuple
    consisting of an etree of , as well as the HTML
    inside the text element
    """
    # TODO: implement

    xml, cleaned_html

def read_html(path):
    """
    Read a HTML file and turn it into valid XML
    """
    f = open(path)
    soup = BeautifulSoup(f)
    f.close()
    pretty_html = soup.prettify()
    return etree.fromstring(pretty_html)
    
def validate_xml_schema(xml_path, schema_path):
    xml_file = lxml.etree.parse(xml_path)

    schema = lxml.etree.XMLSchema(file=schema_path)
    is_valid = schema.validate(xml_file)

    return is_valid


def parlaclarin_to_md(tree):
    """
    Convert Parla-Clarin XML to markdown. Returns a string.
    """
    return ""

def parlaclarin_to_txt(tree):
    """
    Convert Parla-Clarin XML to plain text. Returns a string.
    """
    segments = tree.findall('.//seg')

    for segment in segments:
        etree.strip_tags(segment, 'seg')
        #print(type(segment))
    #return 
    segment_txts = [etree.tostring(segment, pretty_print=True, encoding="UTF-8").decode("utf-8") for segment in segments]
    segment_txts = [txt.replace("<seg>", "").replace("</seg>", "") for txt in segment_txts]

    print(segment_txts[0])
    print(type(segment_txts[0]))

    return "\n".join(segment_txts)

def speeches_with_name(tree, name):
    """
    Convert Parla-Clarin XML to plain text. Returns a string.
    """
    us = tree.findall('.//u')

    texts = []
    for u in us:
        if name.lower() in u.attrib['who'].lower():
            text = etree.tostring(u, pretty_print=True, encoding="UTF-8").decode("utf-8")
            texts.append(text)
        #print(type(segment))
    return texts

if __name__ == '__main__':
    validate_parla_clarin_example()
    #update_test()
