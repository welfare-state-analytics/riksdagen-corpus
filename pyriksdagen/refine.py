from lxml import etree
import re
from pyparlaclarin.read import element_hash
import dateparser
import pandas as pd
from .utils import elem_iter, infer_metadata, parse_date
from .db import load_expressions, filter_db, load_patterns, load_metadata
from .segmentation import (
    detect_mp,
    detect_minister,
    detect_speaker,
    expression_dicts,
    detect_introduction,
    intro_to_dict,
)
from .match_mp import multiple_replace
from datetime import datetime


def redetect_protocol(metadata, protocol):
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
    parser = etree.XMLParser(remove_blank_text=True)

    party_mapping, join_intros, mp_db, minister_db, speaker_db = metadata
    join_intros = join_intros[join_intros['protocol'] == protocol]
    
    protocol_id = protocol.split("/")[-1]
    metadata = infer_metadata(protocol)
    root = etree.parse(protocol, parser).getroot()
    
    # Year from the folder name
    year = metadata["year"]
    # Take into account folders such as 198889
    secondary_year = metadata.get("secondary_year", year)

    dates = [
        parse_date(elem.attrib.get("when"))
        for elem in root.findall(tei_ns + "docDate")
        if parse_date(elem.attrib.get("when")).year in [year, secondary_year]
    ]
    
    # Dates from xml is wrong for digitized era        
    if len(dates) > 0:
        start_date, end_date = min(dates), max(dates)          

    else:
        start_date = datetime(year,1,1)
        end_date = datetime(secondary_year,12,31)
    
    year_mp_db = filter_db(mp_db, start_date=start_date, end_date=end_date)
    year_minister_db = filter_db(minister_db, start_date=start_date, end_date=end_date)
    year_speaker_db = filter_db(speaker_db, start_date=start_date, end_date=end_date)
    
    # Introduction patterns
    pattern_db = load_patterns()
    pattern_db = pattern_db[
        (pattern_db["start"] <= year) & (pattern_db["end"] >= year)
    ]

    root, unk = detect_mps(
        root,
        None,
        pattern_db,
        mp_db=year_mp_db,
        minister_db=year_minister_db,
        speaker_db=year_speaker_db,
        metadata=metadata,
        party_map=party_mapping,
        join_intros=join_intros,
        protocol_id=protocol_id,
        unknown_variables=["gender", "party", "other"],
    )

    b = etree.tostring(
        root, pretty_print=True, encoding="utf-8", xml_declaration=True
    )

    f = open(protocol, "wb")
    f.write(b)
    f.close()
    return unk


def detect_mps(root, names_ids, pattern_db, mp_db=None, minister_db=None, minister_db_secondary=None, speaker_db=None, metadata=None, party_map=None, join_intros=None, protocol_id=None, unknown_variables=None):
    """
    Re-detect MPs in a parla clarin protocol, based on the (updated)
    MP database.
    """
    mp_expressions = load_expressions(phase="mp")
    ids_to_join = set(join_intros['xml_id1'].tolist()+join_intros['xml_id2'].tolist())
    
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    current_speaker = None
    prev = None
    mp_db_secondary = pd.DataFrame()

    # Extract information of unknown speakers
    unknowns = []

    #print(metadata)
    # For bicameral era, prioritize MPs from the same chamber as the protocol
    if "chamber" in metadata:
        chamber = {'Första kammaren': 1, 'Andra kammaren':2}.get(metadata['chamber'], 0)
        mp_db_secondary = mp_db[mp_db['chamber'] != chamber]
        mp_db = mp_db[mp_db['chamber'] == chamber]
        speaker_db = speaker_db[speaker_db['chamber'] == chamber]

    for tag, elem in elem_iter(root):
        if tag == "u":
            # Deleting and adding attributes changes their order;
            # Mark as 'delete' instead and delete later
            elem.set("prev", "delete")
            elem.set("next", "delete")
            if current_speaker is not None:
                elem.attrib["who"] = current_speaker
                if prev is None:
                    prev = elem
                else:
                    new_prev = prev.attrib[xml_ns + "id"]
                    new_next = elem.attrib[xml_ns + "id"]
                    elem.set("prev", new_prev)
                    prev.set("next", new_next)

            else:
                elem.attrib["who"] = "unknown"
                prev = None
        elif tag == "note":
            if elem.attrib.get("type", None) == "speaker":
                text = elem.text
                # Join split intros detected by BERT
                if elem.attrib.get(xml_ns + "id") in ids_to_join:
                    join_intro = join_intros.loc[
                                (join_intros['xml_id1'] == elem.attrib.get(xml_ns + "id")) |
                                (join_intros['xml_id2'] == elem.attrib.get(xml_ns + "id")), 'text']
                    text = join_intro.iloc[0]

                if type(text) == str:
                    d = intro_to_dict(text, mp_expressions)
                    if 'name' in d:
                        d['name'] = multiple_replace(d['name'])
                        
                    if 'other' in d:
                        # Match minister
                        if 'statsråd' in d["other"].lower() or 'minister' in d["other"].lower():
                            current_speaker = detect_minister(text, minister_db, d)

                        elif 'talman' in d["other"].lower():
                            current_speaker = detect_speaker(text, speaker_db, metadata=metadata)

                        else:
                            current_speaker = None

                    # Match mp if not minister/talman and a name is identified
                    # if current_speaker is None and 'name' in d:
                    elif 'name' in d:

                        current_speaker = detect_mp(d, db=mp_db, party_map=party_map)

                        if current_speaker is None and len(mp_db_secondary) > 0:
                            current_speaker = detect_mp(d, db=mp_db_secondary, party_map=party_map)
                    else:
                        current_speaker = None

                    if current_speaker is None:
                        unknowns.append([protocol_id, elem.attrib.get(f'{xml_ns}id')] + [d.get(key, "") for key in unknown_variables])
                    
                    prev = None

    # Do two loops to preserve attribute order
    for tag, elem in elem_iter(root):
        if tag == "u":
            if elem.attrib.get("prev") == "delete":
                del elem.attrib["prev"]
            if elem.attrib.get("next") == "delete":
                del elem.attrib["next"]

    return root, unknowns


def find_introductions(root, pattern_db, intro_ids, minister_db=None):
    """
    Find instances of curation patterns in all files in a folder.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        folder: Folder of files to be searched.
    """

    # return root
    root.text = None
    current_speaker = None
    expressions, manual = expression_dicts(pattern_db)

    for ix, elem_tuple in enumerate(list(elem_iter(root))):
        tag, elem = elem_tuple
        if tag == "u":
            u = None
            u_parent = elem.getparent()
            u_parent.text = None
            for seg in list(elem):
                if type(seg.text) == str:
                    introduction = detect_introduction(
                        seg, intro_ids
                    )
                    if introduction is not None:
                        pass  # print("NEW", seg.text)
                        seg.tag = "{http://www.tei-c.org/ns/1.0}note"
                        seg.attrib["type"] = "speaker"
                        if u is not None:
                            u.addnext(seg)
                        else:
                            elem.addnext(seg)

                        u = etree.Element("{http://www.tei-c.org/ns/1.0}u")
                        # u.text = None
                        if introduction["who"] is not None:
                            u.attrib["who"] = introduction["who"]
                        else:
                            u.attrib["who"] = "unknown"

                        seg.addnext(u)
                        matched_txt = introduction["txt"]
                        ix = None
                        if matched_txt[-1] != ":" and ":" in seg:
                            ix = len(matched_txt) + seg.text.index(matched_txt)
                        if ":" in matched_txt:
                            ix = matched_txt.index(":")
                            ix = ix + seg.text.index(matched_txt)
                        elif seg.text[-1] != ":" and ":" in seg:
                            ix = seg.text.index(":")

                        if ix is not None:
                            rest = seg.text[ix + 1 :]
                            seg.text = seg.text[: ix + 1]
                            new_seg = etree.SubElement(
                                u, "{http://www.tei-c.org/ns/1.0}seg"
                            )
                            new_seg.text = rest

                    elif u is not None:
                        u.append(seg)
                        u.text = None

        elif tag == "note":
            parent = elem.getparent()
            parent.text = None
            # if not elem.attrib.get("type", None) == "speaker":
            if type(elem.text) == str:

                introduction = detect_introduction(
                    elem, intro_ids
                )

                if introduction is not None:
                    if not elem.attrib.get("type", None) == "speaker":
                        print("NEW note", elem.text)
                        elem.attrib["type"] = "speaker"

                        matched_txt = introduction["txt"]
                        ix = None
                        if matched_txt[-1] != ":" and ":" in elem.text:
                            ix = len(matched_txt) + elem.text.index(matched_txt)
                        if ":" in matched_txt:
                            ix = matched_txt.index(":")
                            ix = ix + elem.text.index(matched_txt)
                        elif elem.text[-1] != ":" and ":" in elem:
                            ix = elem.text.index(":")
                        if ix is not None:
                            rest = elem.text[ix + 1 :].strip()
                            if len(rest) > 0:
                                u = etree.Element("{http://www.tei-c.org/ns/1.0}u")
                                # u.text = None
                                if introduction["who"] is not None:
                                    u.attrib["who"] = introduction["who"]
                                else:
                                    u.attrib["who"] = "unknown"

                                elem.addnext(u)

                                rest = elem.text[ix + 1 :]
                                elem.text = elem.text[: ix + 1]

                                new_seg = etree.SubElement(
                                    u, "{http://www.tei-c.org/ns/1.0}seg"
                                )
                                new_seg.text = rest

                    else:
                        pass  # print("OLD", elem.text)

    return root


def detect_date(root, metadata):
    """
    Detect notes with dates in them. Update docDate metadata accordingly.
    """

    dates = set()
    number_dates = set()
    expression = "\\w{3,5}dagen den (\\d{1,2})\\.? (\\w{3,9}) (\\d{4})"
    expression2 = "\\w{3,5}dagen den (\\d{1,2})\\.? (\\w{3,9})"
    expression3 = "(\\d{1,2})\\.? (\\w{3,9}) (\\d{4,4})"
    protocol_year = metadata["year"]
    protocol_years = {protocol_year, metadata.get("secondary_year", protocol_year)}
    yearless = set()

    for ix, elem_tuple in enumerate(list(elem_iter(root))):
        tag, elem = elem_tuple
        if tag == "note" and type(elem.text) == str and len(" ".join(elem.text.split()))  < 50:
            matches = re.search(expression, elem.text)
            matches2 = re.search(expression2, elem.text)
            matches3 = re.search(expression3, elem.text)

            # Dates with the year included, surely date
            if matches is not None:
                elem.attrib["type"] = "date"
                datestr = matches.group(1) + " " + matches.group(2) + " " + matches.group(3)
                date = dateparser.parse(datestr, languages=["sv"])
                if date is not None:
                    if date.year in protocol_years:
                        number_dates.add(date)

            # Dates with the year included, though unsure if protocol date
            elif matches3 is not None:
                datestr = matches3.group()
                date = dateparser.parse(datestr, languages=["sv"])
                if date is not None:
                    if date.year in protocol_years:
                        dates.add(date)

            # Dates without a year
            elif matches2 is not None:
                elem.attrib["type"] = "date"
                datestr = matches2.group(1) + " " + matches2.group(2)
                yearless.add(datestr)

    if len(dates) > 0:
        protocol_year = list(dates)[0].year
    elif len(number_dates) > 0:
        dates = number_dates
        protocol_year = list(dates)[0].year

    for datestr in yearless:
        date = dateparser.parse(datestr + " " + str(protocol_year), languages=["sv"])
        if date is not None:
            dates.add(date)

    dates = sorted(list(dates))
    tei_ns = "{http://www.tei-c.org/ns/1.0}"
    for text in root.findall(".//" + tei_ns + "text"):
        for front in text.findall(".//" + tei_ns + "front"):

            # Remove old docDates
            for docDate in front.findall(".//" + tei_ns + "docDate"):
                docDate.getparent().remove(docDate)
            for div in front.findall(".//" + tei_ns + "div"):
                for docDate in div.findall(".//" + tei_ns + "docDate"):
                    docDate.getparent().remove(docDate)

            if len(dates) > 0:
                for div in front.findall(".//" + tei_ns + "div"):
                    if div.attrib.get("type") == "preface":
                        for docDate in div.findall(".//" + tei_ns + "docDate"):
                            docDate.getparent().remove(docDate)
                        for date in dates:
                            formatted = date.strftime("%Y-%m-%d")
                            docDate = etree.SubElement(div, "docDate")
                            docDate.text = formatted
                            docDate.attrib["when"] = formatted
            else:
                for div in front.findall(".//" + tei_ns + "div"):
                    if div.attrib.get("type") == "preface":
                        formatted = str(protocol_year)
                        docDate = etree.SubElement(div, "docDate")
                        docDate.text = formatted
                        docDate.attrib["when"] = formatted

    return root, dates


def update_ids(root, protocol_id):
    """
    Update element id's
    """
    ids = set()
    xml_id = "{http://www.w3.org/XML/1998/namespace}id"
    for tag, elem in elem_iter(root):
        if tag == "u":
            if xml_id in elem.attrib:
                ids.add(elem.attrib[xml_id])
        elif xml_id in elem.attrib:
            del elem.attrib[xml_id]

    for tag, elem in elem_iter(root):
        if tag == "u":
            if xml_id not in elem.attrib:
                updated_hash = element_hash(elem, protocol_id)
                hash_ix = 0
                updated_id = "i-" + updated_hash + "-" + str(hash_ix)

                while updated_id in ids:
                    hash_ix += 1
                    updated_id = "i-" + updated_hash + "-" + str(hash_ix)

                elem.attrib[xml_id] = updated_id
                ids.add(updated_id)

            for subelem in elem:
                if xml_id in subelem.attrib:
                    del subelem.attrib[xml_id]

    return root

