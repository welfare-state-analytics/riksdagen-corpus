"""
Provides functions for the curation of the parliamentary data.
"""

import pandas as pd
import re, hashlib
import progressbar
from os import listdir
from lxml import etree
from os.path import isfile, join
from pyriksdagen.download import get_blocks, fetch_files
from pyriksdagen.utils import infer_metadata
from pyriksdagen.db import filter_db, year_iterator

def _langmod_loss(sentence):
    return 0.0

def improvement(sentence, regexp):
    """
    Calculates the improvement in probability for a suggested text edit. Returns a tuple of losses.
    """
    sentence_suggestion = regexp
    loss0 = _langmod_loss(sentence)
    loss1 = _langmod_loss(sentence_suggestion)

    return loss0, loss1
    
def find_instances(root, pattern_db, c_hashes = dict()):
    """
    Find instances of curation patterns in all files in a folder.

    Args:
        pattern_db: Patterns to be matched as a Pandas DataFrame.
        folder: Folder of files to be searched.
    """
    columns = ["pattern", "txt", "replacement"]
    data = []
    protocol_id = root.attrib["id"]
    expressions = dict()
    manual = dict()
    for _, row in pattern_db.iterrows():
        if row["type"] == "regex":
            pattern = row['pattern']
            replacement = row['replacement']
            exp = re.compile(pattern)
            #Calculate digest for distringuishing patterns without ugly characters
            pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
            expressions[pattern_digest] = (exp, replacement)
        elif row["type"] == "manual":
            manual[row["pattern"]] = row["replacement"]
    
    for content_block in root:
        cb_id = content_block.attrib["id"]
        page = content_block.attrib.get("page", 0)
        #content_txt = '\n'.join(content_block.itertext())
        for textblock in content_block:
            tb_id = textblock.attrib["id"]
            paragraph = textblock.text
            
            if paragraph is not None:
                for pattern, replacement in manual.items():
                    if pattern in paragraph:
                        paragraph = paragraph.replace(pattern, replacement)
                
                # Do not find regexp instances if paragraph has manual corrections
                if paragraph != textblock.text:
                    d = {"protocol_id": protocol_id,
                        "pattern": "manual",
                        "txt": textblock.text,
                        "replacement": paragraph,
                        "elem_id": tb_id,
                        }
                    data.append(d)
                    continue

                # Regexp 
                for pattern_digest, exp_tuple in expressions.items():
                    exp, outpattern = exp_tuple
                    for m in exp.finditer(paragraph):
                        matched_txt = m.group()
                        replacement = exp.sub(outpattern, matched_txt)
                        
                        d = {"protocol_id": protocol_id,
                        "pattern": pattern_digest,
                        "txt": matched_txt,
                        "replacement": replacement,
                        "elem_id": tb_id,
                        }
                        data.append(d)
    
    columns = ["pattern", "txt", "replacement", "elem_id"]
    return pd.DataFrame(data=data, columns=columns)

def apply_curations(protocol, instance_db):
    protocol_id = protocol.attrib["id"]
    applicable_instances = instance_db[instance_db["protocol_id"] == protocol_id]
    for _, row in applicable_instances.iterrows():
        elem_id = row["elem_id"]
        for target in protocol.xpath("//*[@id='" + elem_id + "']"):
            txt = row["txt"]
            replacement = row["replacement"]
            paragraph = target.text
            paragraph = paragraph.replace(txt, replacement)
            target.text = paragraph
    
    if protocol_id == "prot-1960--fk--19":
        f = open("prot-1960--fk--19-curation.xml", "wb")
        b = etree.tostring(protocol, encoding="utf-8", pretty_print=True)
        f.write(b)
        f.close()
    return protocol
    
def curation_workflow(file_db, archive, pattern_db):
    instance_dbs = []
    for corpus_year, package_ids, _ in year_iterator(file_db):
        print("Curating year:", corpus_year)
        
        year_patterns = filter_db(pattern_db, year=corpus_year)
        print(pattern_db)
        for protocol_id in progressbar.progressbar(package_ids):
            protocol_patterns = filter_db(pattern_db, protocol_id=protocol_id)
            protocol_patterns = pd.concat([protocol_patterns, year_patterns])
            page_content_blocks = get_blocks(protocol_id, archive)
            instance_db = find_instances(page_content_blocks, protocol_patterns)
            instance_db = instance_db.drop_duplicates()
            instance_dbs.append(instance_db)

    print(pd.concat(instance_dbs))
    instance_db = pd.concat(instance_dbs)
    instance_db["protocol_id"] = protocol_id
    return instance_db
