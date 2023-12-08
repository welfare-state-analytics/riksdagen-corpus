"""
Classify intros that are problematic due to unreasonable split and fix them.

Best to run the script in three stages:
1. classify poorly split intros: `-c`
1.1. eyeball te resulting csv and remove rows that shouldn't get merged
2. run with -H
2.1 correct hyphenation in the `input/segmentation/hyphen-surname.json`
3. join intros `-j`
"""
from functools import partial
from lxml import etree
from pyriksdagen.dataset import MergeDataset
from pyriksdagen.utils import (
    protocol_iterators,
    parse_protocol,
    write_protocol,
    )
from tqdm import tqdm
import argparse, json, multiprocessing, os
import pandas as pd
import os, re, sys, time




allcaps = re.compile(r"\b[A-ZÀ-Þ -]{3,}\b")




def find_consequtive_intros(protocol, intro_df):
    '''
    Create dataset of intro+subsequent note/seg/intro to predict if they should be merged.
    '''
    intro_ids = intro_df.loc[intro_df['file_path'] == protocol, 'id'].tolist()

    parser = etree.XMLParser(remove_blank_text=True)
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    root = etree.parse(protocol, parser).getroot()
    
    speaker = False
    data = []
    for elem in root.iter():
        if 'note' not in elem.tag and 'seg' not in elem.tag:
            continue

        if speaker:
            data.append([protocol, xml_id, elem.attrib.get(xml_ns+"id"), text, elem.text])
            speaker = False

        if elem.attrib.get(xml_ns+"id") in intro_ids:
            xml_id = elem.attrib.get(xml_ns+"id")
            text = elem.text
            speaker = True

    return pd.DataFrame(data, columns=['protocol', 'xml_id1', 'xml_id2', 'text1', 'text2'])




def find_intros(protocols):
    rows = []
    cols = ["file_path", "id"]
    for protocol in tqdm(protocols, total=len(protocols)):
        root, ns = parse_protocol(protocol, get_ns=True)
        notes = root.findall(".//{http://www.tei-c.org/ns/1.0}note")
        for note in notes:
            if "type" in note.attrib and note.attrib["type"] == "speaker":
                rows.append([protocol, note.attrib[f"{ns['xml_ns']}id"]])
    return pd.DataFrame(rows, columns=cols)




def classify_split_intros(args):
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoModelForNextSentencePrediction
    # Gather prediction data
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
    if args.read_intros:
        intro_df = pd.read_csv('input/segmentation/_intros.csv')
    else:
        print("Looking for intros")
        intro_df = find_intros(protocols)
        intro_df.to_csv('input/segmentation/_intros.csv', index=False)
        print(intro_df)

    if args.read_predictions:
        df = pd.read_csv("input/segmentation/_intro-prediction-data.csv")
    else:
        find_func = partial(find_consequtive_intros, intro_df=intro_df)
        data = []
        with multiprocessing.Pool() as pool:
            print('Start gathering prediction data')
            for df in tqdm(pool.imap(find_func, protocols), total=len(protocols)):
                data.append(df)
        df = pd.concat(data)
        print(df)
        df.to_csv("input/segmentation/_intro-prediction-data.csv", index=False)

    model = AutoModelForNextSentencePrediction.from_pretrained("_jesperjmb/MergeIntrosNSP").to("cuda")
    test_dataset = MergeDataset(df)
    test_loader = DataLoader(test_dataset, batch_size=64, num_workers=4)
    intros = []
    with torch.no_grad():
        print('Start predicting')
        for token_info, xml_id1s, xml_id2s, text1s, text2s, protocol in tqdm(test_loader, total=len(test_loader)):
            output = model( input_ids=token_info["input_ids"].squeeze(dim=1).to("cuda"),
                            token_type_ids=token_info["token_type_ids"].squeeze(dim=1).to("cuda"),
                            attention_mask=token_info["attention_mask"].squeeze(dim=1).to("cuda"))

            preds = torch.argmax(output[0], dim=1)

            for protocol, xml_id1, xml_id2, text1, text2, pred in zip(protocol, xml_id1s, xml_id2s, text1s, text2s, preds):
                if pred == 1 and 'anf.' not in text2.lower():
                    intros.append([protocol, xml_id1, xml_id2, text1, text2])

    df = pd.DataFrame(intros, columns=['protocol', 'xml_id1', 'xml_id2', 'text1', 'text2'])
    df.to_csv('input/segmentation/_join_intros.csv', index=False)
    return df




def strip_whitespace(text):
    return ' '.join([_.strip() for _ in text.split('\n')]).strip()




def join_intros(df):
    protocols = df["protocol"].unique()
    try:
        with open("input/segmentation/_hyphen-surname.json", "r") as inj:
            D = json.load(inj)
    except:
        print("ERROR: `input/segmentation/_hyphen-surname.json` not found. Run with `-H`")
        sys.exit()
    print("Joining split intros")
    for p in tqdm(protocols, total=len(protocols)):
        p_df = df.loc[df["protocol"] == p]
        root, ns = parse_protocol(p, get_ns=True)
        for i, row in p_df.iterrows():
            if pd.isnull(row['ignore']):
                id1 = row['xml_id1']
                id2 = row['xml_id2']

                intro_a = root.find(f".//{ns['tei_ns']}note[@{ns['xml_ns']}id='{id1}']")
                intro_b = root.find(f".//{ns['tei_ns']}note[@{ns['xml_ns']}id='{id2}']")
                t1 = strip_whitespace(intro_a.text)
                t2 = strip_whitespace(intro_b.text)

                if t1.endswith('-'):
                    intro = ''.join([t1, t2])
                    m = re.search(allcaps, intro).group(0).strip()
                    if m in D:
                        intro = re.sub(allcaps, f' {D[m]["correct"]}', intro)
                elif t1.endswith(' S:') and t2.startswith('T '):
                    intro = ''.join([t1, t2])
                else:
                    intro = ' '.join([t1, t2])
                intro_a.text = intro
                intro_b.getparent().remove(intro_b)
        write_protocol(root, p)




def dictify_hyphen_names():
    print("Generating hypen-surname.json")
    df = pd.read_csv("input/segmentation/_join_intros.csv")
    D = {}
    for i, r in df.iterrows():
        if r['ignore'] != "TRUE":
            t1 = strip_whitespace(r['text1'])
            t2 = strip_whitespace(r['text2'])
            m = None
            if t1.endswith('-'):
                intro = ''.join([t1, t2])
                m = re.search(allcaps, intro).group(0).strip()
                if m not in D:
                    D[m] = {"count":0, "correct": m}
                D[m]["count"] += 1
            else:
                intro = ' '.join([t1, t2])
            print(intro)
            if m:
                print("~~|"+m+"|~~")
            print("")
    with open("input/segmentation/_hyphen-surname.json", "w+") as outj:
        json.dump(D, outj, ensure_ascii=False, indent=4)




def main(args):
    if args.hyphen_check:
        dictify_hyphen_names()
    else:
        df = None
        if args.classify_only:
            df = classify_split_intros(args)
        if args.join_only:
            if df:
                join_intros(df)
            else:
                join_intros(pd.read_csv('input/segmentation/_join_intros.csv'))




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start",
                        type=int,
                        default=1867,
                        help="n.b. --start / --end only work on the classification. Joining intros in the protocol will operate on whatever is in the input csv.")
    parser.add_argument("-e", "--end",
                        type=int,
                        default=2022,
                        help="n.b. --start / --end only work on the classification. Joining intros in the protocol will operate on whatever is in the input csv.")
    parser.add_argument("-r", "--read-intros",
                       action="store_true",
                       help="Read existing file at `input/segmentation/intros.csv`.")
    parser.add_argument("-R", "--read-predictions",
                       action="store_true",
                       help="Read existing file at `input/segmentation/intro-prediction-data.csv`.")
    parser.add_argument("-c", "--classify-only",
                        action="store_true",
                        help="only run the classification model to produce input/segmentation/join_intros.csv")
    parser.add_argument("-H", "--hyphen-check",
                        action="store_true",
                        help="create a dictionary of names with hyphens in the `input/segmentation/join_intros.csv` file.")
    parser.add_argument("-j", "--join-only",
                        action="store_true",
                        help="only join split intros (requires input/segmentation/join_intros.csv, produced by --classify-only and hyphen-surname.json produced by --hyphen check. It's a good idea to check both of these files manually to kick out errors in join_intros, and verify hyphenationd in hyphen-surname.json.)")
    args = parser.parse_args()
    if args.classify_only == args.join_only:
        if args.classify_only == False:
            print("You probably shouldn't do this! Specify -c, -H, or -j in stages.")
            time.sleep(5)
            print("Run with --help for more info.")
            time.sleep(10)
            print("Maybe you know better, so I'll continue in 20 seconds. Cancel with ctrl+c.")
            time.sleep(20)
            args.classify_only = True
            args.join_only = True
            main(args)
        else:
            print("You can't set --classify-only and --join-only together. What do you really want to do?\nTry again.")
    else:
        main(args)
