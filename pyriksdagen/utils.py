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
