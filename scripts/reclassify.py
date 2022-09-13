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
    return (lambda paragraph: classify_paragraph(paragraph.text, model, ft, dim))

def preclassified(d, elem):
    xml_ns = "{http://www.w3.org/XML/1998/namespace}"
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
    xml_id = f"{xml_ns}id"
    if f"{xml_ns}id" not in elem.attrib:
        return elem.tag.split(tei_ns)[-1]
    
    xml_id = elem.attrib[xml_id]
    classification = d[xml_id]
    if classification == 0:
        return "note"
    else:
        return "u"

def get_filename_classifier(filename):
    df = pd.read_csv(filename)
    print("Generate dict...")
    d = {str(row["id"]): row["preds"] for _, row in df.iterrows()}
    print("done")
    return (lambda paragraph: preclassified(d, paragraph))

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)

    if False:
        classifier = random_classifier
    elif args.method == "w2v":
        # Do imports here because they take a loong time
        from tensorflow import keras
        import fasttext, fasttext.util
        dim = 300
        fasttext.util.download_model('sv', if_exists='ignore')
        ft = fasttext.load_model("cc.sv." + str(dim) + ".bin")
        model = keras.models.load_model('input/segment-classifier/')
        classifier = get_neural_classifier(model, ft, dim)
    elif args.method == "bert":
        classifier = get_filename_classifier(args.classfile)

    for protocol_path in progressbar.progressbar(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end))):
        print(protocol_path)
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
    parser.add_argument("--method", type=str, default="w2v")
    parser.add_argument("--classfile", type=str, default=None)
    args = parser.parse_args()
    main(args)
