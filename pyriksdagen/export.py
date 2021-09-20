"""
Parla Clarin generation
"""
import pandas as pd
import progressbar, copy
from lxml import etree
from pyparlaclarin.create import pc_header, create_parlaclarin

from .utils import infer_metadata
from .download import get_blocks, fetch_files
from .db import filter_db, year_iterator


def create_tei(root, metadata):
    """
    Create a Parla-Clarin TEI element from a list of segments.

    Args:
        txts: a list of lists of strings, corresponds to content blocks and paragraphs, respectively.
        metadata: Metadata of the parliamentary session
    """
    # TODO: Rewrite completely
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
    current_page = 0
    u = None
    prev_u = None

    pb = etree.SubElement(body_div, "pb")
    pb.attrib["n"] = str(current_page)
    page_url = "https://betalab.kb.se/" + protocol_id + "/"
    page_filename = (
        protocol_id.replace("-", "_") + "-{:03d}".format(current_page) + ".jp2/_view"
    )
    pb.attrib["facs"] = page_url + page_filename

    for content_block in root:
        new_page = content_block.attrib.get("page", current_page)
        new_page = int(new_page)
        if new_page != current_page:
            current_page = new_page
            pb = etree.SubElement(body_div, "pb")
            pb.attrib["n"] = str(current_page)
            page_url = "https://betalab.kb.se/" + protocol_id + "/"
            page_filename = (
                protocol_id.replace("-", "_")
                + "-{:03d}".format(current_page)
                + ".jp2/_view"
            )
            pb.attrib["facs"] = page_url + page_filename

            if prev_u is None:
                prev_u = u
                u = None

        content_txt = "\n".join(content_block.itertext())
        is_empty = content_txt == ""
        segmentation = content_block.attrib.get("segmentation", None)
        if segmentation == "metadata":
            if prev_u is None:
                prev_u = u
                u = None
            for textblock in content_block:
                note = etree.SubElement(body_div, "note")
                note.text = textblock.text
                note.attrib[
                    "{http://www.w3.org/XML/1998/namespace}id"
                ] = textblock.attrib.get("id", None)
        elif segmentation == "note":
            for textblock in content_block:
                note = etree.SubElement(body_div, "note")
                note.text = textblock.text
                note.attrib[
                    "{http://www.w3.org/XML/1998/namespace}id"
                ] = textblock.attrib.get("id", None)
        else:
            for textblock in content_block:
                tb_segmentation = textblock.attrib.get("segmentation", None)
                if tb_segmentation == "speech_start":
                    prev_u = None
                    current_speaker = textblock.attrib.get("who", None)
                    note = etree.SubElement(body_div, "note", type="speaker")
                    u = etree.SubElement(body_div, "u")
                    if current_speaker is not None:
                        u.attrib["who"] = current_speaker
                    else:
                        u.attrib["who"] = "unknown"

                    # Introduction under <note> tag
                    # Actual speech under <u> tag
                    paragraph = textblock.text.split(":")
                    introduction = paragraph[0] + ":"
                    note.text = introduction
                    note.attrib[
                        "{http://www.w3.org/XML/1998/namespace}id"
                    ] = textblock.attrib.get("id", None)
                    if len(paragraph) > 1:
                        rest_of_paragraph = ":".join(paragraph[1:]).strip()
                        if len(rest_of_paragraph) > 0:
                            seg = etree.SubElement(u, "seg")
                            seg.text = rest_of_paragraph
                elif tb_segmentation == "note":
                    if prev_u is None:
                        prev_u = u
                        u = None
                    note = etree.SubElement(body_div, "note")
                    note.text = textblock.text
                    note.attrib[
                        "{http://www.w3.org/XML/1998/namespace}id"
                    ] = textblock.attrib.get("id", None)
                elif tb_segmentation == "metadata":
                    if prev_u is None:
                        prev_u = u
                        u = None
                    note = etree.SubElement(body_div, "note")
                    note.text = textblock.text
                else:
                    paragraph = textblock.text
                    if paragraph != "":
                        if u is not None:
                            seg = etree.SubElement(u, "seg")
                            seg.text = paragraph
                            seg.attrib[
                                "{http://www.w3.org/XML/1998/namespace}id"
                            ] = textblock.attrib.get("id", None)
                        elif prev_u is not None:
                            prev_u.attrib["next"] = "cont"
                            prev_u = None
                            u = etree.SubElement(body_div, "u")
                            if current_speaker is not None:
                                u.attrib["who"] = current_speaker
                            else:
                                u.attrib["who"] = "unknown"
                            u.attrib["prev"] = "cont"
                            seg = etree.SubElement(u, "seg")
                            seg.text = paragraph
                        else:
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


def parlaclarin_workflow_individual(file_db, archive, corpus_metadata=dict()):
    """
    Create per-protocol parlaclarin files of all files provided in file_db.
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
            parlaclarin_path = "corpus/" + yearstr + "/" + protocol_id + ".xml"
            f = open(parlaclarin_path, "w")
            f.write(parla_clarin_str)
            f.close()
