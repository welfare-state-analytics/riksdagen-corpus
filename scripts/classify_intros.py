import pandas as pd
from lxml import etree
from transformers import AutoModelForSequenceClassification, BertTokenizerFast
from pyriksdagen.utils import protocol_iterators, elem_iter
import torch
from tqdm import tqdm
from torch.utils.data import DataLoader
import argparse
from dataset import IntroDataset

def extract_elem(elem):
	return elem.text, elem.get("{http://www.w3.org/XML/1998/namespace}id")

def extract_note_seg(protocol):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()
    data = []
    for tag, elem in elem_iter(root):
        if tag == 'note':
            data.append(extract_elem(elem))
        elif tag == 'u':
            data.extend(list(map(extract_elem, elem)))
    return data


def main(args):
    model = AutoModelForSequenceClassification.from_pretrained("jesperjmb/parlaBERT")
    tokenizer = BertTokenizerFast.from_pretrained('KB/bert-base-swedish-cased')

    # Get prediction data
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
    data = []
    for protocol in protocols:
        data.extend(extract_note_seg(protocol))
    df = pd.DataFrame(data, columns=['text', 'id'])

    df = df.loc[:500]

    test_dataset = IntroDataset(df)
    test_loader = DataLoader(test_dataset, batch_size=16)

    intros = []
    with torch.no_grad():
        for texts, xml_ids in tqdm(test_loader, total=len(test_loader)):
            output = model( input_ids=texts["input_ids"].squeeze(dim=1),
                            token_type_ids=texts["token_type_ids"].squeeze(dim=1),
                            attention_mask=texts["attention_mask"].squeeze(dim=1))
            preds = torch.argmax(output[0], dim=1).numpy()
            intros.extend([xml_id for xml_id, pred in zip(xml_ids, preds) if pred == 1])
    print(intros)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    args = parser.parse_args()
    main(args)
