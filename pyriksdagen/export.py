"""
Parla Clarin generation
"""
import pandas as pd
import progressbar, copy
from lxml import etree
from pyparlaclarin.create import pc_header, create_parlaclarin

from .utils import infer_metadata, get_formatted_uuid, XML_NS
from .download import get_blocks
from .db import year_iterator


def create_tei(root, metadata):
    """
    Create a Parla-Clarin TEI element from a list of segments.

    Args:
        root (lxml.etree.Element): the protocol data as an lxml tree root
        metadata (dict): Metadata of the parliamentary session
    
    Returns
        tei (lxml.etree.Element): the protocol as a TEI-formatted lxml tree root
    """

    metadata = copy.deepcopy(metadata)

    tei = etree.Element("TEI")
    protocol_id = root.attrib["id"]
    metadata["document_title"] = (
        protocol_id.replace("_", " ").split("-")[0].replace("prot", "Protokoll")
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

    current_speaker = None
    current_page = -1

    pb = etree.SubElement(body_div, "pb")
    pb.attrib["n"] = str(current_page)
    page_url = "https://betalab.kb.se/" + protocol_id + "/"
    page_filename = (
        protocol_id.replace("-", "_") + "-{:03d}".format(current_page) + ".jp2/_view"
    )
    pb.attrib["facs"] = page_url + page_filename

    element_seed = ""
    for content_block in root:
        new_page = content_block.attrib.get("page", current_page)
        new_page = int(new_page)
        if new_page != current_page:
            current_page = new_page
            element_seed = f"{protocol_id}\n{current_page}\n"
            pb = etree.SubElement(body_div, "pb")
            pb.attrib["n"] = str(current_page)
            page_url = "https://betalab.kb.se/" + protocol_id + "/"
            page_filename = (
                protocol_id.replace("-", "_")
                + "-{:03d}".format(current_page)
                + ".jp2/_view"
            )
            pb.attrib["facs"] = page_url + page_filename

        for textblock in content_block:
            text = " ".join(textblock.text.split())
            if text == "":
                continue
            note = etree.SubElement(body_div, "note")
            note.text = text

            # Generate reproducible UUID
            element_seed += text
            note.attrib[f"{XML_NS}id"] = get_formatted_uuid(element_seed)

    return tei

def dict_to_tei(data):
    """
    Convert a metadata dict into a TEI XML tree

    Args:
        data (dict): dictionary containing protocol level metadata

    Returns:
        tei (lxml.etree.Element): the protocol as a TEI-formatted lxml tree root
    """
    metadata = copy.deepcopy(data)

    tei = etree.Element("TEI")
    protocol_id = metadata["protocol_id"]
    metadata["document_title"] = (
        protocol_id.replace("_", " ").split("-")[0].replace("prot", "Protokoll")
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

    for paragraph in data["paragraphs"]:
        note = etree.SubElement(body_div, "note")
        note.text = paragraph

    return tei


def gen_parlaclarin_corpus(
    protocol_db,
    archive,
    corpus_metadata=dict(),
    str_output=True,
):
    """
    Create a parla-clarin file out of all protocols that are provided.

    Args:
        protocol_db (pd.df): dataframe of the protocols
        archive (???): KB archive instance
        corpus_metadata (dict): metadata on the corpus
        str_output (bool): whether to return as an str. Deprecated.

    Returns:
        corpus (???): parlaclarin corpus
    """
    teis = []

    for ix, package in list(protocol_db.iterrows()):
        protocol_id = package["protocol_id"]
        pages = package["pages"]
        metadata = infer_metadata(protocol_id)
        protocol = get_blocks(protocol_id, archive)
        tei = create_tei(protocol, metadata)
        teis.append(tei)

    corpus_metadata["edition"] = "0.1.0"
    corpus = create_parlaclarin(teis, corpus_metadata)
    return corpus

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
        correction="Some data curation was done. It is documented in input/curation/instances",
        edition="0.4.2",
    )
    for key in default_metadata:
        if key not in data:
            data[key] = default_metadata[key]

    protocol_id = data["protocol_id"]
    yearstr = protocol_id[5:]
    yearstr = yearstr.split("-")[0]
    parlaclarin_path = f"corpus/protocols/{yearstr}/{protocol_id}.xml"

    tei = dict_to_tei(data)
    parla_clarin_str = create_parlaclarin(tei, data)
    f = open(parlaclarin_path, "w")
    f.write(parla_clarin_str)
    f.close()


def parlaclarin_workflow_individual(file_db, archive, corpus_metadata=dict()):
    """
    Create per-protocol parlaclarin files of all files provided in file_db.
    Does not return anything, instead writes the data on disk.

    Args:
        file_db (pd.df): dataframe of the files
        archive (???): KB archive instance
        corpus_metadata (dict): corpus-level metadata
    """
    for corpus_year, package_ids, year_db in year_iterator(file_db):
        print("Generate corpus for year", corpus_year)

        default_metadata = dict(
            document_title="Riksdagens protocols " + str(corpus_year),
            authority="National Library of Sweden and the WESTAC project",
            correction="Some data curation was done. It is documented in input/curation/instances",
        )
        for key in default_metadata:
            if key not in corpus_metadata:
                corpus_metadata[key] = default_metadata[key]

        year_db = file_db[file_db["year"] == corpus_year]
        for ix, row in progressbar.progressbar(list(year_db.iterrows())):
            df = pd.DataFrame([row], columns=year_db.columns)
            protocol_id = row["protocol_id"]
            parla_clarin_str = gen_parlaclarin_corpus(
                df,
                archive,
                corpus_metadata=corpus_metadata,
            )

            yearstr = protocol_id[5:]
            yearstr = yearstr.split("-")[0]
            parlaclarin_path = "corpus/protocols/" + yearstr + "/" + protocol_id + ".xml"
            f = open(parlaclarin_path, "w")
            f.write(parla_clarin_str)
            f.close()
