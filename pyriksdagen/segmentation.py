"""
Implements the segmentation of the data into speeches and
ultimately into the Parla-Clarin XML format.
"""
import numpy as np
import pandas as pd
import re, hashlib, copy, os
import progressbar
from os import listdir
from os.path import isfile, join
from lxml import etree
from .download import get_blocks, fetch_files
from .utils import infer_metadata
from .db import filter_db, year_iterator

# Classify paragraph
def classify_paragraph(paragraph, classifier, prior=np.log([0.8, 0.2])):
    """
    Classify paragraph into speeches / descriptions with provided classifier

    """
    words = paragraph.split()
    V = len(words)
    if V == 0:
        return prior

    x = np.zeros((V, classifier["dim"]))

    ft = classifier["ft"]
    for ix, word in enumerate(words):
        vec = ft.get_word_vector(word)
        x[ix] = vec

    pred = classifier["model"].predict(x, batch_size=V)
    return np.sum(pred, axis=0) + prior


def _is_metadata_block(txt0):
    txt1 = re.sub("[^a-zA-ZåäöÅÄÖ ]+", "", txt0)
    len0 = len(txt0)

    # Empty blocks should not be classified as metadata
    if len(txt0.strip()) == 0:
        return False

    # Metadata generally don't introduce other things
    if txt0.strip()[-1] == ":":
        return False

    # Or list MPs
    if "Anf." in txt0:
        return False

    len1 = len(txt1)
    len2 = len(txt0.strip())
    if len2 == 0:
        return False

    # Crude heuristic. Skip if
    # a) over 15% is non alphabetic characters
    # and b) length is under 150 characters

    # TODO: replace with ML algorithm
    return float(len1) / float(len0) < 0.85 and len0 < 150

def detect_speaker(matched_txt, speaker_db, metadata=None):
    """
    Detect the speaker of the house
    """
    lower_txt = matched_txt.lower()

    # Only match if minister is mentioned in intro
    if "talman" in lower_txt:
        if "herr talmannen" in lower_txt or "fru talmannen" in lower_txt:
            speaker_db = speaker_db[speaker_db["titel"] == "talman"]
        elif "förste vice talman" in lower_txt:
            speaker_db = speaker_db[speaker_db["titel"] == "1_vice_talman"]
        elif "andre vice" in lower_txt:
            speaker_db = speaker_db[speaker_db["titel"] == "2_vice_talman"]
        elif "tredje vice" in lower_txt:
            speaker_db = speaker_db[speaker_db["titel"] == "3_vice_talman"]
        else:
            speaker_db = speaker_db[speaker_db["titel"] == "talman"]

        # Do this afterwards to reduce computational cost
        speaker_db = speaker_db[speaker_db["start"] <= metadata["end_date"]]
        speaker_db = speaker_db[speaker_db["end"] >= metadata["start_date"]]
        speaker_db = speaker_db[speaker_db["chamber"] == metadata["chamber"]]

        #print(metadata)
        if len(speaker_db) == 1:
            speaker_id = list(speaker_db["id"])[0]
            return speaker_id

def detect_minister(matched_txt, minister_db, date=None):
    """
    Detect a minister in a snippet of text. Returns a minister id (str) if found, otherwise None.
    """
    lower_txt = matched_txt.lower()

    # Only match if minister is mentioned in intro
    if "statsråd" in lower_txt or "minister" in lower_txt:
        if "Ramel" in matched_txt:
            print(matched_txt)
        dbrows = list(minister_db.iterrows())
        ministers = []
        # herr statsrådet LINDGREN
        for ix, row in dbrows:
            lastname = row["name"].upper().split()[-1].strip()
            # print(lastname)
            if lastname in matched_txt:
                # Check that the whole name exists as a word
                # So that 'LIND' won't be matched for 'LINDGREN'
                matched_split = re.sub(r"[^A-Za-zÀ-ÿ /-]+", "", matched_txt)
                matched_split = matched_split.split()
                if lastname in matched_split:
                    if date is None:
                        ministers.append(row["id"])
                    elif date > row["start"] and date < row["end"]:
                        ministers.append(row["id"])
                    else:
                        print("lastname", lastname, date, row["start"])

        # statsrådet Lindgren
        if len(ministers) == 0:
            for ix, row in dbrows:
                lastname = row["name"].split()[-1].strip()

                # Preliminary check for performance reasons
                if lastname in matched_txt:
                    # Check that the whole name exists as a word
                    # So that 'Lind' won't be matched for 'Lindgren'
                    matched_split = re.sub(r"[^A-Za-zÀ-ÿ /-]+", "", matched_txt)
                    matched_split = matched_split.split()
                    if lastname in matched_split:
                        ministers.append(row["id"])

        if len(ministers) >= 1:
            return ministers[0]


def detect_mp(matched_txt, names_ids, mp_db=None, also_last_name=True):
    """
    Match an MP in a text snippet. Returns an MP id (str) if found, otherwise None.

    If multiple people are matched, defaults to returning None.
    """
    person = []

    # Prefer uppercase
    # SVEN LINDGREN
    for name, identifier in names_ids:
        if name.upper() in matched_txt:
            person.append(identifier)

    # Sven Lindgren
    if len(person) == 0:
        for name, identifier in names_ids:
            if name in matched_txt:
                person.append(identifier)

    # Lindgren, Sven
    if len(person) == 0:
        for name, identifier in names_ids:
            last_name = " " + name.split()[-1] + ","
            if last_name in matched_txt:
                first_name = name.split()[0]
                rest = matched_txt.split(last_name)[-1]
                if first_name in rest:
                    person.append(identifier)

    # LINDGREN, SVEN
    if len(person) == 0:
        for name, identifier in names_ids:
            last_name = " " + name.split()[-1] + ","
            last_name = last_name.upper()
            if last_name in matched_txt:
                first_name = name.split()[0]
                rest = matched_txt.split(last_name)[-1]
                if first_name.upper() in rest.upper():
                    person.append(identifier)

    # Lindgren i Stockholm
    if len(person) == 0 and mp_db is not None:
        for _, row in mp_db.iterrows():
            # print(row)
            i_name = row["name"].split()[-1] + " " + row["specifier"]
            if i_name.lower() in matched_txt.lower():
                person.append(row["id"])

    if also_last_name:
        # LINDGREN
        if len(person) == 0:
            for name, identifier in names_ids:
                name = name.split()[-1]
                if " " + name.upper() + " " in matched_txt:
                    person.append(identifier)
                elif " " + name.upper() + ":" in matched_txt:
                    person.append(identifier)

        # Herr/Fru Lindgren
        if len(person) == 0:
            matched_txt_lower = matched_txt.lower()
            for name, identifier in names_ids:
                last_name = " " + name.split()[-1]
                herr_name = "herr" + last_name.lower()
                fru_name = "fru" + last_name.lower()

                if herr_name in matched_txt_lower:
                    ix = matched_txt_lower.index(herr_name)
                    aftermatch = matched_txt_lower[ix + len(herr_name) :]
                    aftermatch = aftermatch[:1]
                    if aftermatch in [" ", ":", ","]:
                        person.append(identifier)

                if fru_name in matched_txt_lower:
                    ix = matched_txt_lower.index(fru_name)
                    aftermatch = matched_txt_lower[ix + len(fru_name) :]
                    aftermatch = aftermatch[:1]
                    if aftermatch in [" ", ":", ","]:
                        person.append(identifier)

        # Lindgren
        if len(person) == 0:
            for name, identifier in names_ids:
                last_name = " " + name.split()[-1]

                if last_name in matched_txt:
                    ix = matched_txt.index(last_name)
                    aftermatch = matched_txt[ix + len(last_name) :]
                    aftermatch = aftermatch[:1]
                    if aftermatch in [" ", ":", ","]:
                        person.append(identifier)

                elif last_name.upper() in matched_txt:
                    # print(matched_txt, last_name, last_name.upper())
                    person.append(identifier)

    if len(person) == 1:
        return person[0]
    else:
        person_names = list(set(["_".join(m.split("_")[:-1]) for m in person]))
        if len(person_names) == 1:
            return person[-1]
        else:
            return None

def detect_mp_new(intro_text, expressions):
    intro_text = intro_text.strip()
    d = {}
    for exp, t in expressions:
        m = exp.search(intro_text)
        if m is not None:
            matched_text = m.group(0)
            if t not in d:
                d[t] = matched_text.strip()
                intro_text = intro_text.replace(matched_text, " ")
    if "name" in d:
        if ", " in d["name"]:
            s = d["name"].split(", ")
            d["name"] = s[1] + " " + s[0]
    if "gender" in d:
        d["gender"] = d["gender"].lower()
        if d["gender"] == "herr":
            d["gender"] = "man"
        if d["gender"] in ["fru", "fröken"]:
            d["gender"] = "woman"
    return d

def expression_dicts(pattern_db):
    expressions = dict()
    manual = dict()
    for _, row in pattern_db.iterrows():
        if row["type"] == "regex":
            pattern = row["pattern"]
            exp = re.compile(pattern)
            # Calculate digest for distringuishing patterns without ugly characters
            pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
            expressions[pattern_digest] = exp
        elif row["type"] == "manual":
            manual[row["pattern"]] = row["segmentation"]
    return expressions, manual


def detect_introduction(paragraph, expressions, names_ids, minister_db=None):
    """
    Detect whether the current paragraph contains an introduction of a speaker.

    Returns a dict if an intro is detected, otherwise None.
    """
    for pattern_digest, exp in expressions.items():
        for m in exp.finditer(paragraph.strip()):
            matched_txt = m.group()
            person = detect_minister(matched_txt, minister_db)
            if person is None:
                person = detect_mp(matched_txt, names_ids)
            segmentation = "speech_start"
            d = {
                "pattern": pattern_digest,
                "who": person,
                "segmentation": segmentation,
                "txt": matched_txt,
            }

            return d
