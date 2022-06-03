import pandas as pd
from lxml import etree
import multiprocessing
import argparse
from tqdm import tqdm
import argparse
from functools import partial
import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForNextSentencePrediction
from pyriksdagen.utils import protocol_iterators
from pyriksdagen.dataset import MergeDataset
import os


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


def main(args):
    # Gather prediction data
    intro_df = pd.read_csv('input/segmentation/intros.csv')
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
    find_func = partial(find_consequtive_intros, intro_df=intro_df)

    data = []
    with multiprocessing.Pool() as pool:
        print('Start gathering prediction data')
        for df in tqdm(pool.imap(find_func, protocols), total=len(protocols)):
            data.append(df)
    df = pd.concat(data)

    model = AutoModelForNextSentencePrediction.from_pretrained("jesperjmb/MergeIntrosNSP").to("cuda")
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
    df.to_csv('input/segmentation/join_intros.csv', index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    args = parser.parse_args()
    main(args)
