"""
Find  introductions in the protocols using BERT. Used in tandem with resegment.py
"""
import pandas as pd
from lxml import etree
from transformers import AutoModelForSequenceClassification, BertTokenizerFast
from pyriksdagen.utils import protocol_iterators, elem_iter
import torch
from tqdm import tqdm
from torch.utils.data import DataLoader
import argparse
from pyriksdagen.dataset import IntroDataset
from functools import partial
import os

def extract_elem(protocol, elem):
	return elem.text, elem.get("{http://www.w3.org/XML/1998/namespace}id"), protocol

def extract_note_seg(protocol):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()
    data = []
    for tag, elem in elem_iter(root):
        if tag == 'note':
            data.append(extract_elem(protocol, elem))
        elif tag == 'u':
            data.extend(list(map(partial(extract_elem, protocol), elem)))
    return data

def predict_intro(df, cuda):
    model = AutoModelForSequenceClassification.from_pretrained("jesperjmb/parlaBERT")
    if cuda:
        model = model.to('cuda')
    test_dataset = IntroDataset(df)
    test_loader = DataLoader(test_dataset, batch_size=64, num_workers=4)

    intros = []
    with torch.no_grad():
        for texts, xml_ids, file_path in tqdm(test_loader, total=len(test_loader)):

            if cuda:
                output = model( input_ids=texts["input_ids"].squeeze(dim=1).to('cuda'),
                                token_type_ids=texts["token_type_ids"].squeeze(dim=1).to('cuda'),
                                attention_mask=texts["attention_mask"].squeeze(dim=1).to('cuda'))
            else:
                output = model( input_ids=texts["input_ids"].squeeze(dim=1),
                            token_type_ids=texts["token_type_ids"].squeeze(dim=1),
                            attention_mask=texts["attention_mask"].squeeze(dim=1))

            preds = torch.argmax(output[0], dim=1)
            intros.extend([[file_path, xml_id] for file_path, xml_id, pred in zip(file_path, xml_ids, preds) if pred == 1])
    return pd.DataFrame(intros, columns=['file_path', 'id'])

def main(args):
    # Create folder iterator for reasonably large batches
    protocols = protocol_iterators("corpus/protocols/", start=args.start, end=args.end)
    protocols = [os.path.split(p) for p in protocols]
    protocol_df = pd.DataFrame(protocols, columns=['folder', 'file'])
    protocol_df = protocol_df.sort_values(by=['folder', 'file'])
    folders = sorted(set(protocol_df['folder']))

    intros = []
    for folder in folders:
        files = protocol_df.loc[protocol_df['folder'] == folder, 'file'].tolist()
        data = []
        for file in tqdm(files, total=len(files)):
            data.extend(extract_note_seg(os.path.join(folder, file)))
        df = pd.DataFrame(data, columns=['text', 'id', 'file_path'])
        print(df)
        df = predict_intro(df, cuda=args.cuda)
        intros.append(df)

    df = pd.concat(intros)
    df.to_csv('input/segmentation/intros.csv', index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=1920, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    parser.add_argument("--cuda", action="store_true", help="Set this flag to run with cuda.")
    args = parser.parse_args()
    main(args)
