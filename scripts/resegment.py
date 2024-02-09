"""
Find introductions in the protocols. After finding an intro,
tag the next paragraph as an utterance.
"""
from pyparlaclarin.refine import format_texts
from pyriksdagen.db import load_patterns
from pyriksdagen.refine import (
    find_introductions,
)
from pyriksdagen.utils import infer_metadata
from pyriksdagen.utils import protocol_iterators, elem_iter,XML_NS

from lxml import etree
import pandas as pd
import os, progressbar, argparse

from transformers import pipeline

intro_classifier = pipeline("text-classification", model="jesperjmb/parlaBERT", top_k=None)
LABEL_MAP = {"LABEL0": "u", "LABEL1": "intro"}
BATCH_SIZE = 16

def get_labels(texts):
    labels = []
    texts = [t if t is not None else "" for t in texts]
    for i in progressbar.progressbar(range(0, len(texts), BATCH_SIZE)):
        texts_i = texts[i:i+BATCH_SIZE]
        raw_labels = intro_classifier(texts_i, truncation=True, max_length=512)
        for t, label_dict in zip(texts_i, raw_labels):
            label_dict = [l for l in label_dict if l["label"] == "LABEL_0"][0]
            if label_dict["score"] >= 0.5:
                labels.append("u")
            else:
                labels.append("intro")

    # TODO: return a dict
    return labels

def get_text(elem):
    if elem.text is None:
        return ""
    else:
        return " ".join(elem.text.split())

def main(args):
    if args.protocol:
        protocols = [args.protocol]
    else:
        start_year = args.start
        end_year = args.end
        protocols = list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end))

    parser = etree.XMLParser(remove_blank_text=True)

    paragraphs = []
    for protocol in progressbar.progressbar(protocols):
        root = etree.parse(protocol, parser).getroot()
        for tag, elem in elem_iter(root):
            if tag == "u":
                for seg in elem:
                    paragraphs.append(get_text(seg))
            elif tag != "pb":
                paragraphs.append(get_text(elem))

    labels = get_labels(paragraphs)

    # TODO: actually change the tags in the ParlaClarin files
    b = etree.tostring(
        root, pretty_print=True, encoding="utf-8", xml_declaration=True
    )
    with open(protocol, "wb") as f:
        f.write(b)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=1920, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    parser.add_argument("-p", "--protocol",
                        type=str,
                        default=None,
                        help="operate on a single protocol")
    args = parser.parse_args()
    main(args)
