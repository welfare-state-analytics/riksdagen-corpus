from lxml import etree
from pyriksdagen.segmentation import detect_mp, expression_dicts, detect_introduction, classify_paragraph
from pyriksdagen.utils import element_hash
import re
import datetime

def _iter(root):
    for body in root.findall(".//{http://www.tei-c.org/ns/1.0}body"):
        for div in body.findall("{http://www.tei-c.org/ns/1.0}div"):
            for ix, elem in enumerate(div):
                if elem.tag == "{http://www.tei-c.org/ns/1.0}u":
                    yield "u", elem
                elif elem.tag == "{http://www.tei-c.org/ns/1.0}note":
                    yield "note", elem
                elif elem.tag == "{http://www.tei-c.org/ns/1.0}pb":
                    yield "pb", elem
                else:
                    yield None

def detect_mps(root, mp_db, pattern_db):
    """
    Re-detect MPs in a parla clarin protocol, based on the (updated)
    MP database.
    """
    current_speaker = None
    prev = None

    for tag, elem in _iter(root):
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
                    new_prev = prev.attrib["{http://www.w3.org/XML/1998/namespace}id"]
                    new_next = elem.attrib["{http://www.w3.org/XML/1998/namespace}id"]
                    elem.set("prev", new_prev)
                    prev.set("next", new_next)

            else:
                elem.attrib["who"] = "unknown"
                prev = None
        elif tag == "note":
            if elem.attrib.get("type", None) == "speaker":
                if type(elem.text) == str:
                    current_speaker = detect_mp(elem.text, mp_db)
                    prev = None

    # Do two loops to preserve attribute order 
    for tag, elem in _iter(root):
        if tag == "u":
            if elem.attrib.get("prev") == "delete":
                del elem.attrib["prev"]
            if elem.attrib.get("next") == "delete":
                del elem.attrib["next"]

    return root

def find_introductions(root, pattern_db, names_ids):
    """
    Find instances of curation patterns in all files in a folder.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        folder: Folder of files to be searched.
    """

    #return root
    root.text = None
    current_speaker = None
    expressions, manual = expression_dicts(pattern_db)

    for ix, elem_tuple in enumerate(list(_iter(root))):
        tag, elem = elem_tuple
        if tag == "u":
            u = None
            u_parent = elem.getparent()
            u_parent.text = None
            for seg in list(elem):
                if type(seg.text) == str:
                    introduction = detect_introduction(seg.text, expressions, names_ids)
                    if introduction is not None:
                        pass#print("NEW", seg.text)
                        seg.tag = "{http://www.tei-c.org/ns/1.0}note"
                        seg.attrib["type"] = "speaker"
                        if u is not None:
                            u.addnext(seg)
                        else:
                            elem.addnext(seg)

                        u = etree.Element("{http://www.tei-c.org/ns/1.0}u")
                        #u.text = None
                        if introduction["who"] is not None:
                            u.attrib["who"] = introduction["who"]
                        else:
                            u.attrib["who"] = "unknown"

                        seg.addnext(u)
                        if seg.text[-1] != ":":
                            ix = seg.text.index(":")
                            rest = seg.text[ix+1:]
                            seg.text = seg.text[:ix+1]
                            new_seg = etree.SubElement(u, "{http://www.tei-c.org/ns/1.0}seg")
                            new_seg.text = rest

                        
                    elif u is not None:
                        u.append(seg)
                        u.text = None

        elif tag == "note":
            parent = elem.getparent()
            parent.text = None
            #if not elem.attrib.get("type", None) == "speaker":
            if type(elem.text) == str:
                introduction = detect_introduction(elem.text, expressions, names_ids)
                    
                if introduction is not None:
                    if not elem.attrib.get("type", None) == "speaker":
                        pass#print("NEW note", elem.text)
                    else:
                        pass#print("OLD", elem.text)

    return root

def reclassify_paragrahps(root, classifier):
    u = None
    prev_elem = None
    for ix, elem_tuple in enumerate(list(_iter(root))):

        print("ix", ix)
        tag, elem = elem_tuple
        if tag == "u":
            u = elem
            for seg in list(elem):
                if seg.attrib["n"] is not "manual" and type(seg.text) == str:
                    prediction = classify_paragraph(paragraph, classifier)
                    # If the paragraph is predicted to be a <note>
                    if prediction[0] > prediction[1]:
                        seg.tag = "{http://www.tei-c.org/ns/1.0}note"
                        if prev_elem is not None:
                            prev_elem.addnext(seg)
                        prev_elem = seg
                        u = None
                    # If the paragraph is predicted to be a <seg>
                    else:
                        if u is None:
                            u = etree.Element("{http://www.tei-c.org/ns/1.0}u")
                            prev_elem.addnext(u)

                        u.append(seg)
                        prev_elem = u
                        
        elif tag == "note":
            if elem.attrib.get("type") not in ["speaker", "date"] and elem.attrib["n"] is not "manual":
                if type(elem.text) == str:
                    paragraph = elem.text
                    prediction = classify_paragraph(paragraph, classifier)
                    # If the paragraph is predicted to be a <note>
                    if prediction[0] > prediction[1]:
                        u = None
                        prev_elem = elem
                    else:
                        if u is None:
                            u = etree.Element("{http://www.tei-c.org/ns/1.0}u")
                            if prev_elem is not None:
                                prev_elem.addnext(u)
                            prev_elem = u
                        elem.tag = "{http://www.tei-c.org/ns/1.0}seg"
                        u.append(elem)
                else:
                    prev_elem = elem
            else:
                prev_elem = elem

    return root


def format_paragraph(paragraph, spaces = 12):
    words = paragraph.replace("\n", "").strip().split()
    s = "\n" + " " * spaces
    row = ""

    for word in words:
        if len(row) > 60:
            s += row.strip() + "\n" + " " * spaces
            row = word
        else:
            row += " " + word

    if len(row.strip()) > 0:
        s += row.strip() + "\n" + " " * (spaces - 2)

    if s.strip() == "":
        return None
    return s

def format_texts(root):
    for tag, elem in _iter(root):

        if type(elem.text) == str:
            elem.text = format_paragraph(elem.text)
        elif tag == "u":
            for seg in elem:
                if type(seg.text) == str:
                    seg.text = format_paragraph(seg.text, spaces=14)
                else:
                    seg.text = None
            elem.text = None
        elif tag == "pb":
            if "{http://www.w3.org/XML/1998/namespace}url" in elem.attrib:
                url = elem.attrib["{http://www.w3.org/XML/1998/namespace}url"]
                del elem.attrib["{http://www.w3.org/XML/1998/namespace}url"]
                elem.attrib["facs"] = url

    return root

def detect_date(root, protocol_year):
    month_numbers = dict(
        januari=1,
        februari=2,
        mars=3,
        april=4,
        maj=5,
        juni=6,
        juli=7,
        augusti=8,
        september=9,
        oktober=10,
        november=11,
        december=12,
        )

    dates = set()
    expression = "\\w{3,5}dagen den (\\d{1,2})\\.? (\\w{3,9}) (\\d{4})"
    expression2 = "\\w{3,5}dagen den (\\d{1,2})\\.? (\\w{3,9})"
    for ix, elem_tuple in enumerate(list(_iter(root))):
        tag, elem = elem_tuple
        if tag == "note" and type(elem.text) == str and len(elem.text) < 50:
            matches = re.search(expression, elem.text)
            matches2 = re.search(expression2, elem.text)
            if matches is not None:
                day = int(matches.group(1).replace(".", ""))
                month = matches.group(2).lower()
                month = month_numbers.get(month)
                year = int(matches.group(3))

                if month is None and year > 1800:
                    print("Could not parse:", matches.group(0))
                else:
                    elem.attrib["type"] = "date"
                    date = None
                    try:
                        date = datetime.datetime(year, month, day)
                        dates.add(date)
                    except ValueError:
                        print("Whoopsie!")
            elif matches2 is not None:
                day = int(matches2.group(1).replace(".", ""))
                month = matches2.group(2).lower()
                month = month_numbers.get(month)

                if month is None:
                    print("Could not parse:", matches2.group(0))
                else:
                    date = None
                    elem.attrib["type"] = "date"
                    try:
                        date = datetime.datetime(protocol_year, month, day)
                        dates.add(date)
                    except ValueError:
                        print("Whoopsie!")

    dates = sorted(list(dates))
    for text in root.findall(".//{http://www.tei-c.org/ns/1.0}text"):
        for front in text.findall("{http://www.tei-c.org/ns/1.0}front"):

            # Remove old docDates
            for docDate in front.findall("{http://www.tei-c.org/ns/1.0}docDate"):
                docDate.getparent().remove(docDate)
            for div in front.findall("{http://www.tei-c.org/ns/1.0}div"):
                for docDate in div.findall("{http://www.tei-c.org/ns/1.0}docDate"):
                    docDate.getparent().remove(docDate)
            
            if len(dates) > 0:
                for div in front.findall("{http://www.tei-c.org/ns/1.0}div"):
                    if div.attrib.get("type") == "preface":
                        for docDate in div.findall("{http://www.tei-c.org/ns/1.0}docDate"):
                            docDate.getparent().remove(docDate)
                        for date in dates:
                            formatted = date.strftime("%Y-%m-%d")
                            docDate = etree.SubElement(div, "docDate")
                            docDate.text = formatted
                            docDate.attrib["when"] = formatted
            else:
                for div in front.findall("{http://www.tei-c.org/ns/1.0}div"):
                    if div.attrib.get("type") == "preface":
                        formatted = str(protocol_year)
                        docDate = etree.SubElement(div, "docDate")
                        docDate.text = formatted
                        docDate.attrib["when"] = formatted

    return root, dates

def update_ids(root, protocol_id):
    ids = set()
    xml_id = "{http://www.w3.org/XML/1998/namespace}id"
    for tag, elem in _iter(root):
        if tag == "u":
            if xml_id in elem.attrib:
                ids.add(elem.attrib[xml_id])
        elif xml_id in elem.attrib:
            del elem.attrib[xml_id]

    for tag, elem in _iter(root):
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
    xml_n = "{http://www.w3.org/XML/1998/namespace}n"
    n = "n"
    for tag, elem in _iter(root):
        if xml_n in elem.attrib:
            del elem.attrib[xml_n]

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
                    subelem_hash = element_hash(subelem, protocol_id=protocol_id, chars=8)

                    if not manual:
                        if subelem_hash != "manual":
                            subelem.set(n, subelem_hash)
                    else:
                        if subelem.attrib.get(n) != subelem_hash:
                            subelem.set(n, "manual")

    return root
