"""
Run the classification into utterances and notes.
"""
from pyparlaclarin.refine import reclassify, format_texts, random_classifier

from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.utils import infer_metadata, protocol_iterators
from lxml import etree
import pandas as pd
import os, progressbar, sys
import argparse
import numpy as np

def classify_paragraph(s, model, ft, dim, prior=np.log([0.8, 0.2])):
    if s is None:
        return "note"
    words = s.split()
    V = len(words)
    x = np.zeros((V, dim))

    for ix, word in enumerate(words):
        vec = ft.get_word_vector(word)
        x[ix] = vec

    pred = model.predict(x, batch_size=V)
    biases = model.predict(np.zeros(x.shape), batch_size=V)
    # print(pred)
    prediction = np.sum(pred, axis=0) + prior

    if prediction[0] < prediction[1]:
        #print("note", s.strip()[:100])
        return "note"
    else:
        #print("u", s.strip()[:100])
        return "u"

def get_neural_classifier(model, ft, dim):
    return (lambda paragraph: classify_paragraph(paragraph, model, ft, dim))

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)

    if False:
        classifier = random_classifier
    else:
        # Do imports here because they take a loong time
        from tensorflow import keras
        import fasttext, fasttext.util
        dim = 300
        fasttext.util.download_model('sv', if_exists='ignore')
        ft = fasttext.load_model("cc.sv." + str(dim) + ".bin")
        model = keras.models.load_model('input/segment-classifier/')
        classifier = get_neural_classifier(model, ft, dim)

    for protocol_path in progressbar.progressbar(list(protocol_iterators("corpus/", start=args.start, end=args.end))):
        metadata = infer_metadata(protocol_path)
        root = etree.parse(protocol_path, parser).getroot()

        root = reclassify(root, classifier, exclude=["date", "speaker"])
        root = format_texts(root)
        b = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        f = open(protocol_path, "wb")
        f.write(b)
        f.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    args = parser.parse_args()
    main(args)
