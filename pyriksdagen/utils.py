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
from pathlib import Path


def elem_iter(root, ns="{http://www.tei-c.org/ns/1.0}"):
    """
    Return an iterator of the elements (utterances, notes, segs, pbs) in a protocol body
    """
    for body in root.findall(".//" + ns + "body"):
        for div in body.findall(ns + "div"):
            for ix, elem in enumerate(div):
                if elem.tag == ns + "u":
                    yield "u", elem
                elif elem.tag == ns + "note":
                    yield "note", elem
                elif elem.tag == ns + "pb":
                    yield "pb", elem
                elif elem.tag == ns + "seg":
                    yield "seg", elem
                elif elem.tag == "u":
                    elem.tag = ns + "u"
                    yield "u", elem
                else:
                    print(elem.tag)
                    yield None


def infer_metadata(filename):
    """
    Heuristically infer metadata from a protocol id or filename.

    Returns a dict with keys "protocol", "chamber", "year", and "number"
    """
    metadata = dict()
    filename = filename.replace("-", "_")
    metadata["protocol"] = filename.split("/")[-1].split(".")[0]
    split = filename.split("/")[-1].split("_")

    # Year
    for s in split:
        yearstr = s[:4]
        if yearstr.isdigit():
            year = int(yearstr)
            if year > 1800 and year < 2100:
                metadata["year"] = year

                # Protocol ids of format 197879 have two years, eg. 1978 and 1979
                if s[4:6].isdigit():
                    metadata["secondary_year"] = year + 1

    # Chamber
    metadata["chamber"] = "Enkammarriksdagen"
    if "_ak_" in filename:
        metadata["chamber"] = "Andra kammaren"
    elif "_fk_" in filename:
        metadata["chamber"] = "Första kammaren"

    try:
        metadata["number"] = int(split[-1])
    except:
        pass  # print("Number parsing unsuccesful", filename)

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
    """
    Validate an XML file against a schema.
    """
    xml_file = lxml.etree.parse(xml_path)

    schema = lxml.etree.XMLSchema(file=schema_path)
    is_valid = schema.validate(xml_file)

    return is_valid


def protocol_iterators(corpus_root, start=None, end=None):
    """
    Returns an iterator of protocol paths in a corpus.
    """
    folder = Path(corpus_root)
    for protocol in sorted(folder.glob("**/*.xml")):
        path = protocol.relative_to(".")
        assert (start is None) == (
            end is None
        ), "Provide both start and end year or neither"
        if start is not None and end is not None:
            metadata = infer_metadata(protocol.name)

            if start - 1 <= metadata["year"] and end + 1 >= metadata["year"]:
                yield str(protocol.relative_to("."))

        else:
            yield str(protocol.relative_to("."))
