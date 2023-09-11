"""
Implements the segmentation of the data into speeches and
ultimately into the Parla-Clarin XML format.
"""
import numpy as np
import re, hashlib
from .db import load_expressions
from .match_mp import match_mp, name_equals, name_almost_equals, names_in, names_in_rev
from itertools import combinations

# Classify paragraph
def classify_paragraph(paragraph, classifier, prior=np.log([0.8, 0.2])):
    """
    Classify paragraph into speeches / descriptions with provided classifier
    
    Args:
        paragraph (str): the text content of a paragraph
        classifier (dict): a dictionary that includes 'dim', 'ft' and 'model' keys for classification
        prior (np.array): log prior for the classes
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


def detect_speaker(matched_txt, speaker_db, metadata=None):
    """
    Detect the speaker of the house

    Args:
        matched_txt (str): intro text
        speaker_db (pd.df): dataframe containing the speaker metadata
        metadata (dict): metadata about the protocol. Deprecated.

    Returns
        speaker_id (str): ID as a string if detected, otherwise None
    """
    lower_txt = matched_txt.lower()

    # Second vice speaker
    if re.search('andre vice', lower_txt):
        speaker_db = speaker_db[speaker_db["role"].str.contains('andre')]
        
    # Third vice speaker
    elif re.search('tredje vice', lower_txt):
        speaker_db = speaker_db[speaker_db["role"].str.contains('tredje')]

    # First vice speaker
    elif re.search(r'(förste)?\svice', lower_txt):
        speaker_db = speaker_db[speaker_db["role"].str.contains('förste')]

    # Speaker
    elif re.search(r'(herr|fru)?\s?talman', lower_txt):
        speaker_db = speaker_db[speaker_db["role"] == 'talman']

    if len(set(speaker_db["id"])) == 1:
        return speaker_db["id"].iloc[0]

def detect_minister(matched_txt, minister_db, intro_dict):
    """
    Detect a minister

    Args:
        matched_txt (str): intro text
        minister_db (pd.df): dataframe containing the minister metadata
        intro_dict (dict): processed information about the intro text, possibly containing eg. 'gender' 
    
    Returns:
        ministed_id (str): ID as a string if detected, otherwise None
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

def detect_mp(intro_dict, db, party_map=None, match_fuzzily=False):
    """
    Match an MP in a text snippet. Returns an MP id (str) if found, otherwise None.

    If multiple people are matched, defaults to returning None.
    """

    intro_dict["party_abbrev"] = party_map.get(intro_dict.get("party", ""), "")
    variables = ['party_abbrev', 'specifier', 'name']
    variables = [v for v in variables if v in list(db.columns)] # removes missing variables
    variables = sum([list(map(list, combinations(variables, i))) for i in range(len(variables) + 1)], [])[1:]
    if match_fuzzily:
        matching_funs = [name_equals, name_almost_equals, names_in]
    else:
        matching_funs = [name_equals, names_in]
    return match_mp(intro_dict, db, variables, matching_funs)

def intro_to_dict(intro_text, expressions=None):
    """
    Convert introduction to a metadata dictionary.
    Tries to detect 'name', 'gender', 'party', 'specified', as well as some misc things labeled as 'other'.

    Args:
        intro_text (str): introduction text
        expressions (list): a list of regular expressions used for metadata detection.
            Used for optimization, the algorithm works the same if not provided.
    
    Returns:
        d (dict): detected metadata
    """
    if expressions is None:
        expressions = load_expressions(phase="mp")
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
        s = d["name"]
        s = s.replace('-', ' ')
        if ", " in s:
            s = s.split(", ")
            s = s[1] + " " + s[0]
        d["name"] = s

    if "gender" in d:
        d["gender"] = d["gender"].lower()
        if d["gender"] in ["herr", "friherre"]:
            d["gender"] = "man"
        if d["gender"] in ["fru", "fröken"]:
            d["gender"] = "woman"

    if "specifier" in d:
        d["specifier"] = d["specifier"].replace("i ", "")
        d["specifier"] = d["specifier"].replace("från ", "")

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


def detect_introduction(elem, intro_ids):
    """
    Detect whether the current paragraph contains an introduction of a speaker.

    Returns a dict if an intro is detected, otherwise None.
    """
    if elem.attrib.get("{http://www.w3.org/XML/1998/namespace}id") in intro_ids:

            d = {
                "pattern": None,
                "who": None,
                "segmentation": None,
                "txt": elem.text,
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
        if elem1.text.strip()[-1] == "-":
            elem2.text = elem1.text.strip()[:-1] + "-" + elem2.text.strip()
        else:
            elem2.text = elem1.text + " " + elem2.text
        elem1.text = ""

    return combine

def join_text(text1, text2):
    text1, text2 = list(map(lambda x: ' '.join(x.replace('\n', ' ').split()), [text1, text2]))
    # Account for words split over textblocks with '-'
    if text1.endswith('-'):
        return ''.join([text1[:-1], text2])
    else:
        return ' '.join([text1, text2])
