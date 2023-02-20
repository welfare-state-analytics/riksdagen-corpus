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

TEI_NS = "{http://www.tei-c.org/ns/1.0}"

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
    xml_id = f"{xml_ns}id"

    default = elem.tag.split(TEI_NS)[-1]
    if default == "seg":
        default = "u"
    if f"{xml_ns}id" not in elem.attrib:
        return default
    
    xml_id = elem.attrib[xml_id]
    return d.get(xml_id, default)

def get_filename_classifier(filename):
    df = pd.read_csv(filename)
    print("Generate dict...")
    d = {str(key): value for key, value in zip(df["id"], df["preds"])}
    print("done")
    return (lambda paragraph: preclassified(d, paragraph))

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)

    if args.classfile is not None:
        classifier = get_filename_classifier(args.classfile)
    elif args.method == "random":
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

    for protocol_path in progressbar.progressbar(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end))):
        print(protocol_path)
        metadata = infer_metadata(protocol_path)
        root = etree.parse(protocol_path, parser).getroot()

        root = reclassify(root, classifier, exclude=["date", "speaker"])
        root = format_texts(root)
        b = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        with open(protocol_path, "wb") as f:
            f.write(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--method", type=str, default="w2v")
    parser.add_argument("--classfile", type=str, default=None)
    args = parser.parse_args()
    main(args)
