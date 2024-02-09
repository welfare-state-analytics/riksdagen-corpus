"""
Parla Clarin generation
"""
import pandas as pd
import progressbar, copy
from lxml import etree
from pyparlaclarin.create import pc_header, create_parlaclarin
from pyparlaclarin.refine import format_texts

from .utils import infer_metadata, get_formatted_uuid, XML_NS, TEI_NS
from .db import year_iterator

def dict_to_tei(data):
    """
    Convert a metadata dict into a TEI XML tree

    Args:
        data (dict): dictionary containing protocol level metadata

    Returns:
        tei (lxml.etree.Element): the protocol as a TEI-formatted lxml tree root
    """
    metadata = copy.deepcopy(data)

    nsmap = {None: TEI_NS}
    nsmap = {key: value.replace("{", "").replace("}", "") for key,value in nsmap.items()}
    tei = etree.Element("TEI", nsmap=nsmap)
    protocol_id = metadata["protocol_id"]
    metadata["document_title"] = (
        f"Swedish parliamentary record {metadata['sitting']}, number {metadata['number']}"
    )
    documentHeader = pc_header(metadata)
    tei.append(documentHeader)

    text = etree.SubElement(tei, "text")
    front = etree.SubElement(text, "front")
    preface = etree.SubElement(front, "div", type="preface")
    etree.SubElement(preface, "head").text = protocol_id.split(".")[0]
    if "date" not in metadata:
        year = metadata.get("year", 2020)
        metadata["date"] = str(year) + "-01-01"

    etree.SubElement(preface, "docDate", when=metadata["date"]).text = metadata.get(
        "date", "2020-01-01"
    )

    body = etree.SubElement(text, "body")
    body_div = etree.SubElement(body, "div")

    protocol_id = protocol_id.replace("_", "-")
    element_seed = f"{protocol_id}\nNA\n"
    print(element_seed)
    for paragraph in data["paragraphs"]:
        if type(paragraph) == int:
            element_seed = f"{protocol_id}\n{paragraph}\n"
            pb = etree.SubElement(body_div, "pb")
            sitting, number = metadata["sitting"], metadata["number"]
            paragraph = f"{paragraph:03d}"
            link = f"https://betalab.kb.se/prot-{sitting}--{number}/prot_{sitting}__{number}-{paragraph}.jp2/_view"
            pb.attrib["facs"] = link
        else:
            note = etree.SubElement(body_div, "note")
            note.text = paragraph
            element_seed += paragraph
            note.attrib[f"{XML_NS}id"] = get_formatted_uuid(element_seed)

    return tei

def add_to_corpus_meta_file_list(metadata):
    """
    add entry to corpus-level metadata xml files
    """
    xi_ns = "{http://www.w3.org/2001/XInclude}"
    chambers = {
        "Enkammarriksdagen": "ek",
        "Andra kammaren": "ak",
         "Första kammaren": "fk"
    }
    parser = etree.XMLParser(remove_blank_text=True)
    meta_path = f"corpus/protocols/prot-{chambers[metadata['chamber']]}.xml"
    file_path = f"./{metadata['sitting']}/{zero_pad_prot_nr(metadata['protocol'])}.xml"
    root = etree.parse(meta_path, parser).getroot()
    include = root.find(f".//{xi_ns}include[@href=\"{file_path}\"]")
    if include:
        print(f"File already listed in corpus metadata -- {metadata['protocol']}. Are you re-curating")
    else:
        include = etree.SubElement(root, f"{xi_ns}include")
        include.attrib["href"] = file_path
    with open(meta_path, "wb") as f:
        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )
        f.write(b)



def dict_to_parlaclarin(data):
    """
    Create per-protocol parlaclarin files of all files provided in file_db.
    Does not return anything, instead writes the data on disk.

    Args:
        data (dict): metadata and data

    Returns:
        None
    """
    session = data["session"]
    default_metadata = dict(
        document_title=f"Riksdagens protocols {session}",
        authority="National Library of Sweden and the WESTAC project",
        correction="Some programmatic corrections have been made to counter errors stemming from the OCR process.",
    )
    for key in default_metadata:
        if key not in data:
            data[key] = default_metadata[key]

    protocol_id = data["protocol_id"].replace("_", "-")
    number = str(data["number"])
    protocol_id = protocol_id[:-len(number)]

    number = f"{data['number']:03d}"
    protocol_id += number
    print("Formatted protocol ID", protocol_id)
    yearstr = protocol_id[5:]
    yearstr = yearstr.split("-")[0]
    parlaclarin_path = f"corpus/protocols/{yearstr}/{protocol_id}.xml"

    tei = dict_to_tei(data)
    with open(parlaclarin_path, "wb") as f:
        b = etree.tostring(
            tei, pretty_print=True, encoding="utf-8", xml_declaration=True
        )
        f.write(b)
    parser = etree.XMLParser(remove_blank_text=True)
    tei = etree.parse(parlaclarin_path, parser).getroot()
    tei = format_texts(tei, padding=10)
    with open(parlaclarin_path, "wb") as f:
        b = etree.tostring(
            tei, pretty_print=True, encoding="utf-8", xml_declaration=True
        )
        f.write(b)


def zero_pad_prot_nr(protocol_id):
    constituents = protocol_id.split('-')
    if len(constituents) > 1:
        id_nr = '{:0>3}'.format(constituents[-1])
        constituents = constituents[:-1]
        constituents.append(f"{id_nr}")
        protocol_id = '-'.join(constituents)
    else:
        constituents = protocol_id.split('_')
        id_nr = '{:0>3}'.format(constituents[-1])
        constituents = constituents[:-1]
        constituents.append(f"{id_nr}")
        protocol_id = '-'.join(constituents)
    return protocol_id

