#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides useful utilities for the other modules as well as for general use.
"""

import lxml
from lxml import etree
from bs4 import BeautifulSoup
from pathlib import Path
from pyparlaclarin.refine import format_texts
from datetime import datetime
import hashlib, uuid, base58, requests, tqdm
import zipfile

XML_NS = "{http://www.w3.org/XML/1998/namespace}"

def elem_iter(root, ns="{http://www.tei-c.org/ns/1.0}"):
    """
    Return an iterator of the elements (utterances, notes, pbs) in a protocol body

    Args:
        root (lxml.etree.Element): the protocol data as an lxml tree root
        ns (str): TEI namespace, defaults to TEI v1.0.

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
                #elif elem.tag == ns + "seg": # Code doesn't return segs anyway (2023-09-20), but
                #    yield "seg", elem        # commenting out in case of catastrophy -- fully delete after
                elif elem.tag == "u":
                    elem.tag = ns + "u"
                    yield "u", elem
                else:
                    print(elem.tag)
                    yield None


def infer_metadata(filename):
    """
    Heuristically infer metadata from a protocol id or filename.
    
    Args:
        filename (str): the protocols filename. Agnostic wrt. dashes and underscores. Can be relative or absolute.

    Returns a dict with keys "protocol", "chamber", "year", and "number"
    """
    metadata = dict()
    filename = filename.replace("-", "_")
    metadata["protocol"] = filename.split("/")[-1].split(".")[0]
    split = filename.split("/")[-1].split("_")
    metadata["document_type"] = split[0]

    # Year
    for s in split:
        yearstr = s[:4]
        if yearstr.isdigit():
            year = int(yearstr)
            if year > 1800 and year < 2100:
                metadata["year"] = year
                metadata["sitting"] = str(year)

                # Protocol ids of format 197879 have two years, eg. 1978 and 1979
                if s[4:6].isdigit():
                    metadata["secondary_year"] = year + 1
                    metadata["sitting"] += f"/{s[4:6]}"

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


def clean_html(s):
    """
    Read a HTML file and turn it into valid XML

    Args:
        s (str): original HTML as a string

    Returns:
        tree (lxml.etree.tree): XML tree
    """
    soup = BeautifulSoup(s)
    pretty_html = soup.prettify()
    return etree.fromstring(pretty_html)


def validate_xml_schema(xml_path, schema_path):
    """
    Validate an XML file against a schema.

    Args:
        xml_path (str): path to the XML file
        schema_path (str): path to the schema file

    Returns:
        is_valid (bool): whether the XML is valid according to the schema
    """
    xml_file = lxml.etree.parse(xml_path)
    xml_file.xinclude()

    schema = lxml.etree.XMLSchema(file=schema_path)
    is_valid = schema.validate(xml_file)

    return is_valid


def protocol_iterators(corpus_root, start=None, end=None):
    """
    Returns an iterator of protocol paths in a corpus.

    Args:
        corpus_root (str): path to the corpus root
        start (int): start year
        end (int): end year

    Returns:
        iterator of the protocols as relative paths to current location
    """
    folder = Path(corpus_root)
    for protocol in sorted(folder.glob("**/*.xml")):
        path = protocol.relative_to(".")
        assert (start is None) == (
            end is None
        ), "Provide both start and end year or neither"
        if start is not None and end is not None:
            metadata = infer_metadata(protocol.name)
            year = metadata["year"]
            secondary_year = metadata.get("secondary_year", year)
            if start <= year and end >= secondary_year:
                yield str(protocol.relative_to("."))

        else:
            yield str(protocol.relative_to("."))

def parse_date(s):
    """
    Parse datetimes with special error handling

    Args:
        s (str): datetime as a string

    Returns:
        date (datetime.datetime): date as a datetime
    """
    try:
        return datetime.strptime(s, "%Y-%m-%d")

    except ValueError:
        if len(s) == 4:
            if int(s) > 1689 and int(s) < 2261:
                return datetime(int(s), 6, 15)
            else:
                return None
        else:
            return None

def get_formatted_uuid(seed=None):
    """
    Generate a UUID and format it in base58.
    The formatted UUID is prepended bu 'i-' so that it can be used as an XML ID

    Args:
        seed (str): Random seed. Optional.

    Returns:
        id (str): formatted UUID
    """

    if seed is None:
        x = uuid.uuid4()
    else:
        m = hashlib.md5()
        m.update(seed.encode('utf-8'))
        x = uuid.UUID(m.hexdigest())

    return f"i-{str(base58.b58encode(x.bytes), 'UTF8')}"


def _download_with_progressbar(url, fname, chunk_size=1024):
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    with open(fname, 'wb') as file, tqdm.tqdm(
        desc=fname,
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=chunk_size):
            size = file.write(data)
            bar.update(size)

def download_corpus(path="./"):
    """
    Downloads the full corpus.
    Does not return anything, just downloads the corpus ZIP and unzips it.

    Args:
        path (str): path for the download

    """
    p = Path(path)
    url = "https://github.com/welfare-state-analytics/riksdagen-corpus/releases/latest/download/corpus.zip"
    zip_path = p / "corpus.zip"
    corpus_path = p / "corpus"
    if corpus_path.exists():
        print(f"WARNING: data already exists at the path '{corpus_path}'. It will be overwritten once the download is finished.")

    zip_path_str = str(zip_path.relative_to("."))
    extraction_path = str(p.relative_to("."))
    
    # Download file and display progress
    _download_with_progressbar(url, zip_path_str)
    with zipfile.ZipFile(zip_path_str, "r") as zip_ref:
        print("Exract to", corpus_path, "...")
        zip_ref.extractall(extraction_path)

    zip_path.unlink()

def get_doc_dates(protocol):
    """
    Gets the content of <docDate> elements. 

    - match_error is True when the value of the "when" attribte doesn't match the element's text value.

    - dates is a list of dates.
    """
    match_error = False
    dates = []
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()
    date_elems = root.findall(f"{tei_ns}docDate")
    for de in date_elems:
        when_attrib = de.get("when")
        elem_text = de.text
        if not when_attrib == elem_text:
            match_error = True
        dates.append(when_attrib)
    return match_error, dates

def write_protocol(prot_elem, prot_path):
    """
    Writes the protocol lxml element (`prot_elem`) to the specified path (`prot_path`).
    """
    prot_elem = format_texts(prot_elem)
    b = etree.tostring(
        prot_elem,
        pretty_print=True,
        encoding="utf-8",
        xml_declaration=True
    )
    with open(prot_path, "wb") as f:
        f.write(b)

def parse_protocol(protocol_path, get_ns=False):
    """
    Parse a protocol, return root element (and name space defnitions).
    """
    tei_ns = "{http://www.tei-c.org/ns/1.0}"
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol_path, parser).getroot()
    if get_ns:
        return root, {"tei_ns":tei_ns, "xml_ns":xml_ns}
    else:
        return root



