#!/usr/bin/env python3
"""
Generates a dynamic markdown file for the repo's main README.
    - generate variable dict
    - reads in readme-template.txt
    - substitutess variables
    - writes README.md
"""
from datetime import datetime
from pyriksdagen.utils import (
    protocol_iterators,
    elem_iter,
    )
from lxml import etree
from py_markdown_table.markdown_table import markdown_table
from tqdm import tqdm
import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import pandas as pd
import re, subprocess




here = os.path.dirname(__file__)
now = datetime.now()

corpus_paths = {
    "protocols_path": "corpus/protocols",
    "metadata_path": "corpus/metadata/"
}

md_row_names = {
    "-": "",
    "corpus_size": "Corpus size (GB)",
    "N_prot": "Number of parliamentary records",
    "N_prot_pages": "Total parliamentary record pages*",
    "N_prot_speeches": "Total parliamentary record speeches",
    "N_prot_words": "Total parliamentary record words",
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
    with open(f"README.md", 'w+') as out:
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
    """
    Calculate the corpus size in GB
    """
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




def count_pages_speeches_words(protocol):
    """
    Count pages (\<pb> elems) in protocols and words.
    """
    pages, speeches, words = 0,0,0
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()
    #tei = root.find(f"{tei_ns}TEI")
    for tag, elem in elem_iter(root):
        if tag == "u":
            for segelem in elem:
                words += len([_.strip() for _ in segelem.text.split(' ') if len(_) > 0 and _ != '\n'])
        elif tag in ["note"]:
            if 'type' in elem.attrib:
                if elem.attrib['type'] == 'speaker':
                    speeches += 1
    pages = len(root.findall(f"{tei_ns}pb"))
    return pages, speeches, words

def infer_year(protocol):
    return int(protocol.split('/')[-1].split('-')[1][:4])




def calculate_prot_stats():
    """
    Counts protocol docs, number of pages, and words
    """
    print("Calculating protocol summary statistics...")
    D = {"protocols":{}, "pages":{}, "speeches": {}, "words":{}}
    N_prot,N_prot_pages,N_prot_speeches, N_prot_words = 0,0,0,0
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=1867, end=2023)))
    for protocol in tqdm(protocols, total=len(protocols)):
        prot_year = infer_year(protocol)
        if prot_year not in D["protocols"]:
            D["protocols"][prot_year] = 0
            D["pages"][prot_year] = 0
            D["speeches"][prot_year] = 0
            D["words"][prot_year] = 0
        N_prot += 1
        D["protocols"][prot_year] += 1
        pp, sp, pw = count_pages_speeches_words(protocol)
        N_prot_pages += pp
        D["pages"][prot_year] += pp
        N_prot_speeches += sp
        D["speeches"][prot_year] += sp
        N_prot_words += pw
        D["words"][prot_year] += pw

    print(f"...{N_prot} protocols, {N_prot_pages} protocol pages, {N_prot_words} protocol words")
    return N_prot, N_prot_pages, N_prot_speeches, N_prot_words, D




def calculate_mot_stats():
    """
    Calculate N motions, N motion pages and N motion words
    """
    print("Calculating motion summary statistics...")
    print("...this function hasn't been written yet, return 0,0,0")
    N_mot, N_mot_pages, N_mot_words = 0,0,0
    return N_mot, N_mot_pages, N_mot_words




def count_MP():
    """
    Counts N unique MEPs (unique wiki id's) in the MP database
    """
    print("Counting MPs (unique people w/ role)...")
    N_MP = 0
    df = pd.read_csv("corpus/metadata/member_of_parliament.csv")
    N_MP = len(df["swerik_id"].unique())
    print(f"... {N_MP} individuals have a 'member of parliament' role")
    return N_MP




def count_MIN():
    """
    Counts ministers in the metadata
    """
    print("Counting ministers (unique people with role)...")
    N_MIN = 0
    df = pd.read_csv("corpus/metadata/minister.csv")
    N_MIN = len(df["swerik_id"].unique())
    print(f"... {N_MIN} individuals have a 'minister' role")
    return N_MIN




def gen_prot_plot(df, path, title_string, ylab):
    scales = {
        "Words":1e6,
        "Pages":1e3,
        "Speeches":1e3,
        "Records":1
    }
    labels = {
        "Words":"M",
        "Pages":"k",
        "Speeches":"k",
        "Records":""
    }
    path_dir = os.path.dirname(path)
    fig_name = os.path.basename(path).split('.')[0]
    versions = df.columns
    versions = sorted(set(versions), key=lambda v: list(map(int, v[1:].split('.'))), reverse=True)
    versions = versions[:4]
    df = df[versions]
    p, a = plt.subplots()
    a.plot(df)
    plt.title(title_string)
    plt.legend(versions, loc ="upper left")
    a.set_xlabel('Year')
    a.set_ylabel(ylab)
    ticks_y = ticker.FuncFormatter(lambda x, pos: '{0:g}{1}'.format(x/scales[ylab], labels[ylab]))
    a.yaxis.set_major_formatter(ticks_y)
    plt.savefig(f"{path_dir}/{fig_name}.png")




def main(args):
    print(f"CALUCLATING SUMSTATS FOR {args.version}")
    print("---------------------------------")
    new_version_row = [args.version]
    new_version_row.append(calculate_corpus_size())
    prot_stats = calculate_prot_stats()
    prot_d = prot_stats[4]
    [new_version_row.append(_) for _ in prot_stats[:4]]
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


    print("GENERATING SUMSTAT PLOTS:")
    n_prot_path = "scripts/stats-dashboard/figures/n-prot/n-prot.csv"
    prot_pages_path = "scripts/stats-dashboard/figures/prot-pages/prot-pages.csv"
    prot_speeches_path = "scripts/stats-dashboard/figures/prot-speeches/prot-speeches.csv"
    prot_words_path = "scripts/stats-dashboard/figures/prot-words/prot-words.csv"

    n_prot_df = pd.read_csv(n_prot_path)
    prot_pages_df = pd.read_csv(prot_pages_path)
    prot_speeches_df = pd.read_csv(prot_speeches_path)
    prot_words_df = pd.read_csv(prot_words_path)

    n_prot_df.set_index('year', inplace=True)
    prot_pages_df.set_index('year', inplace=True)
    prot_speeches_df.set_index('year', inplace=True)
    prot_words_df.set_index('year', inplace=True)

    n_prot_df[args.version] = prot_d["protocols"]
    prot_pages_df[args.version] = prot_d["pages"]
    prot_speeches_df[args.version] = prot_d["speeches"]
    prot_words_df[args.version] = prot_d["words"]

    n_prot_df.to_csv(n_prot_path)
    prot_pages_df.to_csv(prot_pages_path)
    prot_speeches_df.to_csv(prot_speeches_path)
    prot_words_df.to_csv(prot_words_path)

    gen_prot_plot(n_prot_df, n_prot_path, f"Number of Parliamentary Records over time ({args.version})", "Records")
    gen_prot_plot(prot_pages_df, prot_pages_path, f"Number of Pages in Parliamentary Records over time ({args.version})", "Pages")
    gen_prot_plot(prot_speeches_df, prot_speeches_path, f"Number of Speeches in Parliamentary Records over time ({args.version})", "Speeches")
    gen_prot_plot(prot_words_df, prot_words_path, f"Number of Words in Parliamentary Records over time ({args.version})", "Words")
    print("...done")

    print("GENERATING PLOTS OF MP COVERAGE:")
    mp_coverage = subprocess.run(
        ['python', 'scripts/stats-dashboard/mp-coverage.py'],
        capture_output=True, text=True
    )
    assert mp_coverage.returncode == 0
    mp_plot = subprocess.run(
        ['python', 'scripts/stats-dashboard/plot-mp-coverage.py', "-v", args.version],
        capture_output=True, text=True
    )
    assert mp_plot.returncode == 0
    mp_plot_ratio = subprocess.run(
        ['python', 'scripts/stats-dashboard/plot-mp-coverage-ratio.py', "-v", args.version],
        capture_output=True, text=True
    )
    assert mp_plot_ratio.returncode == 0
    print("...done")

    print("RENDERING NEW README FILE:")
    to_render = {
            "Updated": now.strftime("%Y-%m-%d, %H:%M:%S"),
            "Version": args.version,
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
