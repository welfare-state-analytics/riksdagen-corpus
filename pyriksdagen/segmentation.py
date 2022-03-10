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
from .utils import infer_metadata
from .db import filter_db, year_iterator
from .match_mp import *
from itertools import combinations

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
    txt1 = re.sub("[^a-zA-Zß-ÿÀ-Þ ]+", "", txt0)
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

    # Second vice speaker
    if re.search('andre vice', lower_txt):
        speaker_db = speaker_db[speaker_db["role"].str.contains('2_vice')]
    
    # Third vice speaker
    elif re.search('tredje vice', lower_txt):
        speaker_db = speaker_db[speaker_db["role"].str.contains('3_vice')]

    # First vice speaker
    elif re.search(r'(förste)?\svice', lower_txt):
        speaker_db = speaker_db[speaker_db["role"].str.contains('1_vice')]

    # Speaker
    elif re.search(r'(herr|fru)?\s?talman', lower_txt):
        speaker_db = speaker_db[speaker_db["role"].str.contains('speaker')]

    if len(set(speaker_db["id"])) == 1:
        return speaker_db["id"].iloc[0]

def detect_minister(matched_txt, minister_db, intro_dict):
    """
    Detect a minister in a snippet of text. Returns a minister id (str) if found, otherwise None.
    """
    lower_txt = matched_txt.lower()

    # Filter by gender
    if 'gender' in intro_dict:
        gender = intro_dict["gender"]
        minister_db = minister_db[minister_db["gender"] == gender]

    # Match by name
    if 'name' in intro_dict:
        name = intro_dict["name"].lower()
        # thage petterson
        #print(minister_db)
        name_matches = names_in(name, minister_db)
        if not name_matches.empty:
            if len(set(name_matches["id"])) == 1:
                return name_matches["id"].iloc[0]

    # Match by role
    # Catch "utrikesdepartementet"
    if role := re.search(r'([A-Za-zÀ-ÿ]+)(?:departementet)', lower_txt):
        r = role.group(0).replace('departementet', '')
        role_matches = minister_db[minister_db["role"].str.contains(r, regex=False)]
        if not role_matches.empty:
            if len(set(role_matches["id"])) == 1:
                return role_matches["id"].iloc[0]

    # Catch "ministern för utrikes ärendena (...)"
    elif role := re.search(r'(?:ministern för )([A-Za-zÀ-ÿ]+)', lower_txt):
        r = role.group(0).split()[-1]
        role_matches = minister_db[minister_db["role"].str.contains(r, regex=False)]
        if not role_matches.empty:
            if len(set(role_matches["id"])) == 1:
                return role_matches["id"].iloc[0]

    elif role := re.search(r'[A-Za-zÀ-ÿ]+minister', lower_txt):
        r = role.group(0).replace('minister', '')
        role_matches = minister_db[minister_db["role"].str.contains(r, regex=False)]
        if not role_matches.empty:
            if len(set(role_matches["id"])) == 1:
                return role_matches["id"].iloc[0]

def detect_mp(intro_dict, db, party_map=None):
    """
    Match an MP in a text snippet. Returns an MP id (str) if found, otherwise None.

    If multiple people are matched, defaults to returning None.
    """

    intro_dict["party_abbrev"] = party_map.get(intro_dict.get("party", ""), "")
    variables = ['party_abbrev', 'specifier', 'name']
    variables = [v for v in variables if v in list(db.columns)] # removes missing variables
    variables = sum([list(map(list, combinations(variables, i))) for i in range(len(variables) + 1)], [])[1:]
    matching_funs = [name_equals, names_in]

    return match_mp(intro_dict, db, variables, matching_funs)

def intro_to_dict(intro_text, expressions):

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

    if "specifier" in d:
        d["specifier"] = d["specifier"].replace("i ", "")

    return d

def expression_dicts(pattern_db):
    expressions = dict()
    manual = dict()
    for _, row in pattern_db.iterrows():
        pattern = row["pattern"]
        exp = re.compile(pattern)
        # Calculate digest for distringuishing patterns without ugly characters
        pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
        expressions[pattern_digest] = exp
    return expressions, manual


def detect_introduction(paragraph, expressions):
    """
    Detect whether the current paragraph contains an introduction of a speaker.

    Returns a dict if an intro is detected, otherwise None.
    """
    for pattern_digest, exp in expressions.items():
        for m in exp.finditer(paragraph.strip()):
            matched_txt = m.group()
            person = None
            segmentation = "speech_start"
            d = {
                "pattern": pattern_digest,
                "who": person,
                "segmentation": segmentation,
                "txt": matched_txt,
            }

            return d

def combine_intros(elem1, elem2, intro_expressions, other_expressions):
    """
    Join intros that have been split as an artifact of the data processing.
    """
    if elem1.text is None or elem2.text is None:
        return False
    combine = False
    for exp, _ in other_expressions:
        for m in exp.finditer(elem1.text.strip()):
            combine = True

    intro = detect_introduction(elem2.text, intro_expressions)
    combine = combine and intro is not None
    combine = combine and "Anf" not in elem2.text
    if combine:
        elem2.text = elem1.text + " " + elem2.text
        elem1.text = ""

    return combine