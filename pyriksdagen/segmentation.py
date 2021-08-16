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
from pyriksdagen.mp import detect_mp
from pyriksdagen.download import get_blocks, fetch_files
from pyriksdagen.utils import infer_metadata
from pyriksdagen.db import filter_db, year_iterator

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

def detect_mp(matched_txt, names_ids, mp_db=None, also_last_name=True):
    """
    Match the introduced speaker in a text snippet
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

    # TODO: herr Lindgren i Stockholm

    if len(person) == 0 and mp_db is not None:
        for _, row in mp_db.iterrows():
            #print(row)
            i_name = row["name"].split()[-1] + " " + row["specifier"]
            #print(i_name)
            if i_name.lower() in matched_txt.lower():
                person.append(row["id"])

    if also_last_name:
        # Herr Lindgren
        if len(person) == 0:
            matched_txt_lower = matched_txt.lower()
            for name, identifier in names_ids:
                last_name = " " + name.split()[-1]
                herr_name = "herr" + last_name.lower()
                fru_name = "fru" + last_name.lower()

                if herr_name in matched_txt_lower:
                    ix = matched_txt_lower.index(herr_name)
                    aftermatch = matched_txt_lower[ix + len(herr_name):]
                    aftermatch = aftermatch[:1]
                    if aftermatch in [" ", ":", ","]:
                        person.append(identifier)

                if fru_name in matched_txt_lower:
                    ix = matched_txt_lower.index(fru_name)
                    aftermatch = matched_txt_lower[ix + len(fru_name):]
                    aftermatch = aftermatch[:1]
                    if aftermatch in [" ", ":", ","]:
                        person.append(identifier)

        # Lindgren
        if len(person) == 0:
            for name, identifier in names_ids:
                last_name = " " + name.split()[-1]
                
                if last_name in matched_txt:
                    ix = matched_txt.index(last_name)
                    aftermatch = matched_txt[ix + len(last_name):]
                    aftermatch = aftermatch[:1]
                    if aftermatch in [" ", ":", ","]:
                        person.append(identifier)

                elif last_name.upper() in matched_txt:
                    #print(matched_txt, last_name, last_name.upper())
                    person.append(identifier)

    if len(person) == 1:
        return person[0]
    else:
        person_names = list(set(["_".join(m.split("_")[:-1]) for m in person]))
        if len(person_names) == 1:
            return person[-1]
        else:
            return None

def expression_dicts(pattern_db):
    expressions = dict()
    manual = dict()
    for _, row in pattern_db.iterrows():
        if row["type"] == "regex":
            pattern = row['pattern']
            exp = re.compile(pattern)
            #Calculate digest for distringuishing patterns without ugly characters
            pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
            expressions[pattern_digest] = exp
        elif row["type"] == "manual":
            manual[row["pattern"]] = row["segmentation"]
    return expressions, manual

def detect_introduction(paragraph, expressions, names_ids):
    for pattern_digest, exp in expressions.items():
        for m in exp.finditer(paragraph.strip()):
            matched_txt = m.group()
            person = detect_mp(matched_txt, names_ids)
            segmentation = "speech_start"
            d = {
            "pattern": pattern_digest,
            "who": person,
            "segmentation": segmentation,
            "txt": matched_txt,
            }

            return d

# Instance detection
def find_instances_xml(root, pattern_db, mp_db, classifier):
    """
    Find instances of segment start and end patterns in a txt file.

    Args:
        root: root of an lxml tree to be pattern matched.
        pattern_db: Patterns to be matched as a Pandas DataFrame.
    """
    columns = ['protocol_id', "elem_id", "pattern", "segmentation", "who", "id"]
    data = []
    protocol_id = root.attrib["id"]
    metadata = infer_metadata(protocol_id)
    pattern_rows = list(pattern_db.iterrows())
    
    mp_db = mp_db[mp_db["chamber"] == metadata["chamber"]]
    names = mp_db["name"]
    ids = mp_db["id"]
    names_ids = list(zip(names,ids))
    
    expressions, manual = expression_dicts(pattern_db)
    
    prot_speeches = dict()
    for content_block in root:
        cb_id = content_block.attrib["id"]
        content_txt = '\n'.join(content_block.itertext())
        if not _is_metadata_block(content_txt):
            for textblock in content_block:
                tb_id = textblock.attrib["id"]
                paragraph = textblock.text

                # Do not do segmentation if paragraph is empty
                if type(paragraph) != str:
                    continue

                for pattern, segmentation in manual.items():
                    if pattern in paragraph:
                        person = detect_mp(paragraph, names_ids)
                        #person = detect_mp(matched_txt, names_ids)
                        d = {"pattern": "manual",
                            "segmentation": segmentation,
                            "elem_id": tb_id,
                            }
                        continue

                # Detect speaker introductions
                d = detect_introduction(paragraph, expressions, names_ids)

                # Do not do further segmentation if speech is detected
                if d is not None:
                    d["elem_id"] = tb_id
                    data.append(d)
                    continue

                # Use ML model to classify paragraph
                if classifier is not None:
                    preds = classify_paragraph(paragraph, classifier)
                    if np.argmax(preds) == 1:
                        segmentation = "note"
                        d = {
                        "segmentation": segmentation,
                        "elem_id": tb_id,
                        }

                        data.append(d)
        else:
            d = {"pattern": None, "who": None, "segmentation": "metadata"}
            d["elem_id"] = cb_id
            data.append(d)

    df = pd.DataFrame(data, columns=columns)
    df["protocol_id"] = protocol_id
    return df

def apply_instances(protocol, instance_db):
    protocol_id = protocol.attrib["id"]
    
    applicable_instances = instance_db[instance_db["protocol_id"] == protocol_id]
    applicable_instances = applicable_instances.drop_duplicates(subset=['elem_id'])

    for _, row in applicable_instances.iterrows():
        elem_id = row["elem_id"]
        for target in protocol.xpath("//*[@id='" + elem_id + "']"):
            target.attrib["segmentation"] = row["segmentation"]
            if type(row["who"]) == str:
                target.attrib["who"] = row["who"]

            if type(row["id"]) == str:
                target.attrib["id"] = row["id"]

    return protocol
    
def find_instances(protocol_id, archive, pattern_db, mp_db, classifier=None):
    page_content_blocks = get_blocks(protocol_id, archive)
    instance_db = find_instances_xml(page_content_blocks, pattern_db, mp_db, classifier=classifier)
    
    instance_db["protocol_id"] = protocol_id
    return instance_db
    
def segmentation_workflow(file_db, archive, pattern_db, mp_db, ml=True):
    classifier = None
    if ml:
        import tensorflow as tf
        import fasttext.util

        model = tf.keras.models.load_model("input/segment-classifier")

        # Load word vectors from disk or download with the fasttext module
        vector_path = 'cc.sv.300.bin'
        fasttext.util.download_model('sv', if_exists='ignore')
        ft = fasttext.load_model(vector_path)

        classifier = dict(
            model=model,
            ft=ft,
            dim=ft.get_word_vector("hej").shape[0]
        )

    instance_dbs = []
    for corpus_year, package_ids, _ in year_iterator(file_db):
        print("Segmenting year:", corpus_year)
        
        year_patterns = filter_db(pattern_db, year=corpus_year)
        year_mps = filter_db(mp_db, year=corpus_year)
        print(year_mps)

        for protocol_id in progressbar.progressbar(package_ids):
            protocol_patterns = filter_db(pattern_db, protocol_id=protocol_id)
            protocol_patterns = pd.concat([protocol_patterns, year_patterns])
            instance_db = find_instances(protocol_id, archive, protocol_patterns, year_mps, classifier=classifier)
            instance_dbs.append(instance_db)
    
    return pd.concat(instance_dbs)
