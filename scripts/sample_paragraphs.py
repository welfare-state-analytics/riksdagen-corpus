'''
Draw a random stratified sample of paragraphs by year and chamber for manual quality control of corpus tags.
'''
import pandas as pd
from lxml import etree
import argparse, progressbar
import base58
from pyriksdagen.utils import protocol_iterators, infer_metadata
import warnings

tei_ns = "{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"
parser = etree.XMLParser(remove_blank_text=True)

def get_date(root):
    for docDate in root.findall(f".//{tei_ns}docDate"):
        date_string = docDate.text
        break
    return date_string

def get_paragraph_counts(start, end, corpus_path="corpus/protocols/", paragraph_type=None):
    rows = []
    protocol_list = list(protocol_iterators(corpus_path, start=start, end=end+1))
    if len(protocol_list) == 0:
        warnings.warn(f"No protocols between {start} and {end}")
        return None
    for protocol_path in progressbar.progressbar(protocol_list):
        root = etree.parse(protocol_path, parser)
        elems = root.findall(f".//{tei_ns}seg") + root.findall(f".//{tei_ns}note")
        year = get_date(root)[:4]
        year = int(year)
        if year < start or year > end:
            continue

        protocol_id = protocol_path.split("/")[-1].split(".")[0]
        metadata = infer_metadata(protocol_id)
        chamber = metadata["chamber"]
        chamber = "".join([wd[0] for wd in chamber.split()]).lower()
        
        for elem in elems:
            if paragraph_type == "intro":
                if elem.attrib.get("type") != "speaker":
                    continue
            id_elem = elem.attrib[f"{xml_ns}id"]
            id_number = base58.b58decode(id_elem.split("-")[-1])
            id_number = int.from_bytes(id_number, "big")
            rows.append([protocol_path, protocol_id, year, id_elem, chamber, id_number])

    df = pd.DataFrame(rows, columns=["protocol_path", "protocol_id", "year", "elem_id", "chamber", "ordinal"])
    df = df.sort_values("ordinal")

    return df

def parse_paragrahps(df):
    rows = []
    for _, row in df.iterrows():
        protocol_path = row["protocol_path"]
        root = etree.parse(protocol_path, parser)
        elem_id = row["elem_id"]
        pageno = None
        text = None
        current_pageno = None
        for body in root.findall(f".//{tei_ns}body"):
            for div in body.findall(f".//{tei_ns}div"):
                for elem in div:
                    if elem.tag == f"{tei_ns}pb":
                        current_pageno = elem.attrib["facs"]
                        #print(pageno)
                    elif elem.tag == f"{tei_ns}u":
                        for subelem in elem:
                            if subelem.attrib[f"{xml_ns}id"] == elem_id:
                                pageno = current_pageno
                                text = subelem.text
                                
                    if elem.attrib.get(f"{xml_ns}id", "") == elem_id:
                        pageno = current_pageno
                        text = elem.text
    
        if text is None:
            text = ""
        text = " ".join(text.split())
        rows.append([elem_id, text, pageno])
        
    df_prime = pd.DataFrame(rows, columns=["elem_id", "text", "link"])
    df = df.merge(df_prime, on="elem_id", how="left")
    return df
                
def sample_paragraphs(df):
    rows = []
    df_prime = pd.DataFrame(rows, columns=["facs", "text", "elem_id", "github"])
    df = df.merge(df_prime, how="right", on=["facs"])
    cols = ["protocol_id", "x", "elem_id", "text", "facs", "github"]
    df = df[cols]
    return df

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument('--head', type=int, default=0, help="Start taking paragraphs from this index")
    argparser.add_argument('--tail', type=int, default=3, help="Take paragraphs until this index")
    argparser.add_argument("--start", type=int, default=1867, help="Start year")
    argparser.add_argument("--end", type=int, default=2029, help="End year")
    argparser.add_argument("--paragraph_type", type=str, default=None, help="Type of paragraphs to sample [None, 'intro']")
    args = argparser.parse_args()

    path = 'corpus/protocols'

    dfs = []
    for decade in range(args.start, args.end):
        print("Year:", decade)
        decade_end = decade
        protocol_df = get_paragraph_counts(decade, decade_end, paragraph_type=args.paragraph_type)
        if protocol_df is None:
            continue
        print(protocol_df)
        for chamber in list(set(protocol_df["chamber"])):
            chamber_df = protocol_df[protocol_df["chamber"] == chamber]
            sample = chamber_df.head(args.tail)
            sample = sample.tail(args.tail - args.head)
            sample = parse_paragrahps(sample)
            
            sample["segmentation"] = None
            sample["comments"] = None

            cols = ["protocol_id", "elem_id", "segmentation", "comments", "text", "link"]
            sample = sample[cols]
            #sample.to_csv(f"input/gold-standard/prot-{decade}--{chamber}-segment-classification.csv", index=False)
            #sample.to_csv(f"input/gold-standard/prot-{decade}--{chamber}-segment-classification.csv", index=False)

            subset = f"prot-{decade}--{chamber}"
            sample["subset"] = subset

            dfs.append(sample)

    df = pd.concat(dfs)

    if args.paragraph_type == "intro":
        df["speaker_name"] = None
        df["speaker_i_ort"] = None
        df["speaker_party"] = None
        df["speaker_born"] = None
        df["speaker_wiki_id"] = None
        cols = ["protocol_id", "elem_id", "speaker_name", "speaker_i_ort", "speaker_party", "speaker_born", "speaker_wiki_id", "comments", "text", "link"]
        df = df[cols]
        
    df.to_csv(f"input/gold-standard/prot-segment-classification.csv", index=False)



