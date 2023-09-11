'''
Draw a random stratified sample by decade for manual quality control of corpus tags.
TODO: Does not take into account that multiple pages from same protocol can be sampled atm.
'''
import numpy as np
import pandas as pd
from lxml import etree
import argparse, progressbar, hashlib

from pyriksdagen.utils import infer_metadata, protocol_iterators

tei_ns = "{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

def get_date(root):
    for docDate in root.findall(f".//{tei_ns}docDate"):
        date_string = docDate.text
        break
    return date_string

def get_page_counts(corpus_path="corpus/protocols/"):
    parser = etree.XMLParser(remove_blank_text=True)
    rows = []
    for protocol_path in progressbar.progressbar(list(protocol_iterators(corpus_path, start=args.start, end=args.end))):
        root = etree.parse(protocol_path, parser)
        pbs = root.findall(f".//{tei_ns}pb")
        year = get_date(root)[:4]
        protocol_id = protocol_path.split("/")[-1].split(".")[0]
        rows.append([protocol_path, protocol_id, int(year), len(pbs)])

    df = pd.DataFrame(rows, columns=["protocol_path", "protocol_id", "year", "pages"])
    return df

def get_pagenumber(link):
    link = link.replace(".jp2/_view", "")
    link = link.split("-")[-1]
    link = link.split("page=")[-1]
    if link.isnumeric():
        return int(link)

def sample_page_counts(df, start, end, n, seed=None):
    df = df[df["year"] >= start]
    df = df[df["year"] <= end].copy()
    df["p"] = df["pages"] / df["pages"].sum()
    sample = df.sample(n, weights="p", replace=True, random_state=seed)
    #sample = sample.groupby(['protocol_id'], as_index=False).size()

    return sample

def parse_elem(elem, lines):
    elem_id = elem.attrib.get(f"{xml_ns}id")
    text = elem.text
    if text is None:
        text = ""

    text = text.strip()[:15]

    linenumber = None
    for i, l in enumerate(lines):
        if elem_id in l:
            linenumber = i + 1

    return text, elem_id, linenumber

def sample_pages(df, random_state=None):
    pages = np.array(df["pages"])
    x = np.random.randint(np.zeros(len(pages)), pages)
    if random_state is not None:
        x = random_state.randint(np.zeros(len(pages)), pages)
    df["x"] = x

    parser = etree.XMLParser(remove_blank_text=True)
    rows = []
    for _, row in df.iterrows():
        protocol_path = row["protocol_path"]
        x = row["x"]
        root = etree.parse(protocol_path, parser)
        pbs = root.findall(f".//{tei_ns}pb")
        facs = pbs[x].attrib["facs"]

        with open(protocol_path) as f:
            lines = f.read().split("\n")

        gh_link = ""
        rows.append([protocol_path, x, facs, gh_link])

    df_prime = pd.DataFrame(rows, columns=["protocol_path", "x", "facs", "gh_link"])
    df = df.merge(df_prime, how="left", on=["protocol_path", "x"])

    rows = []
    for _, row in df.iterrows():
        facs = row["facs"]
        protocol_path = row["protocol_path"]

        with open(protocol_path) as f:
            lines = f.read().split("\n")

        root = etree.parse(protocol_path, parser)
        active = False
        for div in root.findall(f".//{tei_ns}div"):
            for elem in div:
                if elem.tag == f"{tei_ns}pb":
                    if elem.attrib.get("facs") == facs:
                        active = True
                    else:
                        active = False
                elif active:
                    text, elem_id, linenumber = parse_elem(elem, lines)
                    url_root = f"https://github.com/welfare-state-analytics/riksdagen-corpus/blob/{args.branch}"
                    github = f"{url_root}/{protocol_path}#L{linenumber}"
                    if elem.tag == f"{tei_ns}u":
                        for seg in elem:
                            text, elem_id, linenumber = parse_elem(seg, lines)
                            url_root = f"https://github.com/welfare-state-analytics/riksdagen-corpus/blob/{args.branch}"
                            github = f"{url_root}/{protocol_path}#L{linenumber}"
                            rows.append([facs, text, elem_id, github])
                    else:
                        rows.append([facs, text, elem_id, github])

    df_prime = pd.DataFrame(rows, columns=["facs", "text", "elem_id", "github"])
    df = df.merge(df_prime, how="right", on=["facs"])
    cols = ["protocol_id", "x", "elem_id", "text", "facs", "github"]
    df = df[cols]
    return df

def flatten(df):
    df = df.drop_duplicates(["protocol_id", "x"])
    columns = ["protocol_id", "x", "comments", "facs" ,"github"]
    df = df[columns]
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", '--seed', type=str, default=None, help="Random state seed")
    parser.add_argument("-b", "--branch", type=str, default="main", help="Github branch where curation is happening.")
    parser.add_argument('-p', '--pages_per_decade', type=int, default=30, help="How many pages per decade? 30")
    parser.add_argument("-s", "--start", type=int, default=1920, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    parser.add_argument("--flatten", type=bool, default=False, help="Flatten output to only contain pages instead of elements")
    args = parser.parse_args()

    digest = hashlib.md5(args.seed.encode("utf-8")).digest()
    digest = int.from_bytes(digest, "big") % (2**32)

    path = 'corpus/protocols'
    protocol_df = get_page_counts()
    print(protocol_df)

    for decade in range(args.start // 10 * 10, args.end, 10):
        print("Decade:", decade)
        sample = sample_page_counts(protocol_df, decade, decade + 9, n=args.pages_per_decade, seed=digest)
        print(sample)

        prng = np.random.RandomState( (digest+decade) % (2**32))
        sample = sample_pages(sample, random_state=prng)
        sample = sample.sort_values(["protocol_id", "x"])
        sample["segmentation"] = None
        sample["seg_type"] = None
        sample["speaker"] = None
        sample["comments"] = None

        cols1 = [c for c in sample.columns if c not in ["facs", "github"]]
        cols2 = [c for c in sample.columns if c in ["facs", "github"]]

        cols = cols1 + cols2
        sample = sample[cols]
        if args.flatten:
            sample = flatten(sample)

        sample.to_csv(f"input/quality-control/sample_{decade}.csv", index=False)

        protocols_unique = list(sample.protocol_id.unique())
        with open(f"input/quality-control/sample_{decade}.txt", "w+") as outf:
            for up in protocols_unique:
                outf.write(f"corpus/protocols/{up.split('-')[1]}/{up}.xml\n")
