#!/usr/bin/env python3
"""
Generates a markdown file for the repo's main README.
    - generate variable dict
    - reads in readme-template.txt
    - substitutess variables
    - writes README.md
"""
from pyriksdagen.utils import (
    protocol_iterators,
    elem_iter,
    )
from lxml import etree
from py_markdown_table.markdown_table import markdown_table
from tqdm import tqdm
import argparse, os
import pandas as pd
import re



here = os.path.dirname(__file__)


"""
TO DO
=====
Corpus information
------------------
(This should probably just be a table).

[x] The total number of persons in the MP catalogue
[x] The total number of pages by document type
[x] The size in Gb of the corpus folder

Corpus Statistics - Figures
---------------------------
[x] Number of documents by type (protocols, motions, government bills etc), year, and corpus version
[x] Number of pages by type (protocols, motions, government bills etc), year, and corpus version
[_] Number of MPs by year and chamber (with the actual number of seats as a line - Bobs plot, but more readable)
[ ] The number of speeches by year and corpus version

Corpus Quality
--------------
[x] Speech-to-speaker mapping proportion by year and corpus version
[_] Number of members of parliament by year and chamber as a ratio with respect to the actual number of seats (see paper)
[ ] The OCR quality (character- and word error rate) by decade and document type (records)
    - note this is a two-stage sample and needs to be estimated by taking this into account, liam knows more
[ ] The segmentation error by decennia and document type (records)
[ ] The segmentation classification error by decennia and document type (records)
[ ] The number proportion of empty chairs and chairs with multiple persons overlap.
"""


corpus_paths = {
        "protocols_path": "corpus/protocols",
        "metadata_path": "corpus/metadata/",
    }

md_row_names = {
    "-": "",
    "corpus_size": "Corpus size (GB)",
    "N_prot": "Number of protocols",
    "N_prot_pages": "Total protocol pages*",
    "N_prot_words": "Total protocol words",
    "N_mot": "Number of Motions",
    "N_mot_pages": "Total motion pages",
    "N_mot_words": "Total motion words",
    "N_MP": "Number of people with MP role",
    "N_MIN": "Number of people with minister role"
    }




def render_markdown(renderd):
    with open(f"{here}/readme-template.md", 'r') as inf:
        template = inf.read()
    readme = template.format(**renderd)
    with open(f"{here}/_README.md", 'w+') as out: # testing -- later write to project root
        out.write(readme)
    return True




def mk_table_data(df):
    table_data = []
    D = {}
    version = sorted(list(set(df['version'])), key=lambda s: list(map(int, s[1:].split('.'))), reverse=True)
    cols = [c for c in df.columns if c != "version"]
    for v in version[:3]:
        dfv = df.loc[df["version"]==v].copy()
        dfv.reset_index(inplace=True, drop=True)
        for col in cols:
            if col not in D:
                D[col] = {}
            D[col][v] = dfv.at[0, col]
    for k, v in D.items():
        n = {'': md_row_names[k]}
        n.update(v)
        table_data.append(n)
    return table_data




def calculate_corpus_size():
    print("Calculating corpus size...")
    corpus_size = 0
    for k, v in corpus_paths.items():
        for dirpath, dirnames, filenames in os.walk(v):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    corpus_size += os.path.getsize(fp)
    fsize = "%.2f" % (corpus_size / (1024 * 1024 * 1024)) # converts size to gigabytes
    print(f"...{fsize} GB")
    return fsize




def count_pages_words(protocol):
    pages, words = 0,0
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()
    tei = root.find(f"{tei_ns}TEI")
    for tag, elem in elem_iter(root):
        if tag == "u":
            for segelem in elem:
                words += len([_.strip() for _ in segelem.text.split(' ') if len(_) > 0 and _ != '\n'])
    pages = len(tei.findall(f"{tei_ns}pb"))
    return pages, words




def calculate_prot_stats():
    print("Calculating protocol summary statistics...")
    N_prot,N_prot_pages,N_prot_words = 0,0,0
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=1867, end=2022)))
    for protocol in tqdm(protocols, total=len(protocols)):
        N_prot += 1
        pp, pw = count_pages_words(protocol)
        N_prot_pages += pp
        N_prot_words += pw
    print(f"...{N_prot} protocols, {N_prot_pages} protocol pages, {N_prot_words} protocol words")
    return N_prot, N_prot_pages, N_prot_words




def calculate_mot_stats():
    print("Calculating motion summary statistics...")
    print("...this function hasn't been written yet, return 0,0,0")
    N_mot, N_mot_pages, N_mot_words = 0,0,0
    return N_mot, N_mot_pages, N_mot_words




def count_MP():
    print("Counting MPs (unique people w/ role)...")
    N_MP = 0
    df = pd.read_csv("corpus/metadata/member_of_parliament.csv")
    N_MP = len(df["wiki_id"].unique())
    print(f"... {N_MP} individuals have a 'member of parliament' role")
    return N_MP




def count_MIN():
    print("Counting ministers (unique people with role)...")
    N_MIN = 0
    df = pd.read_csv("corpus/metadata/minister.csv")
    N_MIN = len(df["wiki_id"].unique())
    print(f"... {N_MIN} individuals have a 'minister' role")
    return N_MIN




def main(args):
    print(f"CALUCLATING SUMSTATS FOR {args.version}")
    print("---------------------------------")
    new_version_row = [args.version]
    new_version_row.append(calculate_corpus_size())
    #[new_version_row.append(_) for _ in calculate_prot_stats()]
    [new_version_row.append(_) for _ in [0,0,0]] # use this to do fast testing
    [new_version_row.append(_) for _ in calculate_mot_stats()]
    new_version_row.append(count_MP())
    new_version_row.append(count_MIN())

    # Update running stats
    running_stats = pd.read_csv(f"{here}/descr_stats_version.csv")
    running_stats.drop(running_stats[running_stats.version == args.version].index, inplace=True)
    running_stats.reset_index(inplace=True, drop=True)
    running_stats.loc[len(running_stats)] = new_version_row
    running_stats.to_csv(f"{here}/descr_stats_version.csv", index=False)

    # generate table data
    table_data = mk_table_data(running_stats)
    # generate table
    table = markdown_table(
            table_data
        ).set_params(
            quote=False,
            padding_width=3,
            row_sep="markdown"
        ).get_markdown()

    print("Sumstats, last 3 versions:\n")
    print(table)
    print("\n\n")

    to_render = {
            "sumstats_table": table,
        }
    if render_markdown(to_render):
        print("New README generated successfully.")




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", "--version", type=str)
    args = parser.parse_args()
    exp = re.compile(r"v([0-9]+)([.])([0-9]+)([.])([0-9]+)(b|rc)?([0-9]+)?")
    if exp.search(args.version) is None:
        print(f"{args.version} is not a valid version number. Exiting")
        exit()
    else:
        args.version = exp.search(args.version).group(0)
        main(args)
