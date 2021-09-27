from lxml import etree
import re, random, datetime
from pyparlaclarin.read import element_hash
import dateparser

from .utils import elem_iter
from .segmentation import (
    detect_mp,
    detect_minister,
    detect_speaker,
    expression_dicts,
    detect_introduction,
    classify_paragraph,
)


def detect_mps(root, names_ids, pattern_db, mp_db=None, minister_db=None, speaker_db=None, metadata=None):
    """
    Re-detect MPs in a parla clarin protocol, based on the (updated)
    MP database.
    """
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    current_speaker = None
    prev = None

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
                if type(elem.text) == str:
                    current_speaker = detect_minister(elem.text, minister_db, date=metadata["start_date"])
                    if current_speaker is None:
                        current_speaker = detect_mp(elem.text, names_ids, mp_db=mp_db)
                    if current_speaker is None:
                        current_speaker = detect_speaker(elem.text, speaker_db, metadata=metadata)
                    prev = None

    # Do two loops to preserve attribute order
    for tag, elem in elem_iter(root):
        if tag == "u":
            if elem.attrib.get("prev") == "delete":
                del elem.attrib["prev"]
            if elem.attrib.get("next") == "delete":
                del elem.attrib["next"]

    return root


def find_introductions(root, pattern_db, names_ids, minister_db=None):
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
                        seg.text, expressions, names_ids, minister_db=minister_db
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
                    elem.text, expressions, names_ids, minister_db=minister_db
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


def update_hashes(root, protocol_id, manual=False):
    """
    Update XML element hashes to keep track which element has been manually modified
    """
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    n = "n"
    for tag, elem in elem_iter(root):
        if xml_ns + n in elem.attrib:
            del elem.attrib[xml_ns + n]

        # Page beginnings <pb> use the n attribute for other purposes
        if tag != "pb":
            elem_hash = element_hash(elem, protocol_id=protocol_id, chars=8)

            if not manual:
                if elem_hash != "manual":
                    if elem.attrib.get(n) != elem_hash:
                        elem.set(n, elem_hash)
            else:
                print(elem.attrib)
                print(elem.attrib[n], elem_hash)
                if elem.attrib[n] != elem_hash:
                    elem.set(n, "manual")

            if tag == "u":
                for subelem in elem:
                    subelem_hash = element_hash(
                        subelem, protocol_id=protocol_id, chars=8
                    )

                    if not manual:
                        if subelem_hash != "manual":
                            subelem.set(n, subelem_hash)
                    else:
                        if subelem.attrib.get(n) != subelem_hash:
                            subelem.set(n, "manual")

    return root
