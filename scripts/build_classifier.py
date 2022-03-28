"""
Build a neural network to classify paragraphs into utterances and notes.
Uses pre-trained word embeddings. A feedforward network is then trained
to give each word the odds of that it belongs to each category. The odds
are summed up and a prior is added for the classification of a full para-
graph. 
"""
import os
import fasttext
import numpy as np
import tensorflow as tf
from pathlib import Path
import argparse
from lxml import etree
import pandas as pd
import progressbar
from sklearn.utils import shuffle

def get_ps(datapath, split="train"):
    print("Read data from", datapath)
    df = pd.read_csv(datapath)
    df = shuffle(df, random_state=123)
    print(set(df["tag"]))
    df = df.replace("intro","note")
    df = df[(df["tag"] == "note") | (df["tag"] == "seg")]
    for _, row in df.iterrows():
        tag = row["tag"]
        text = row["text"]
        yield tag, " ".join(text.split())

def get_pairs(datapath, split):
    for tag, text in get_ps(datapath, split):
        words = text.split()
        for word in words:
            yield (word, tag)

def get_set(ft, datapath, split, classes=dict(), upper_limit=1300):
    x = []
    y = []

    for w, c in get_pairs(datapath, split):
        classes[c] = classes.get(c, 0) + 1
        if classes[c] < upper_limit:
            x.append(w)
            y.append(c)

    class_keys = list(classes.keys())
    y = [class_keys.index(y_ix) for y_ix in y]

    for ix, x_ix in enumerate(x):
        x[ix] = ft.get_word_vector(x_ix)

    x = tf.constant(x)
    y = tf.constant(y)
    print("dataset", x.shape, y.shape)
    dset = tf.data.Dataset.from_tensor_slices((x, y))

    return dset, class_keys


def get_paragraphs(class_numbers, datapath, traintest="test/", upper_limit=100):
    print("Get paragraphs")
    print("class_numbers, datapath, traintest")
    print(class_numbers, datapath, traintest)
    current_class = None
    classified_paragraphs = []

    for current_class, text in get_ps(datapath, traintest):
        classified_paragraphs.append((text, current_class))

    return classified_paragraphs[:upper_limit]


def get_model(dim, classes):
    model = tf.keras.Sequential()
    model.add(tf.keras.Input(shape=(dim,)))
    model.add(tf.keras.layers.Dense(25, activation="relu"))
    model.add(tf.keras.layers.Dense(classes))

    sloss = tf.keras.losses.SparseCategoricalCrossentropy(
        from_logits=True, reduction="auto", name="sparse_categorical_crossentropy"
    )
    model.compile(optimizer="adam", metrics=["accuracy"], loss=sloss)

    return model


def print_confusion_matrix(y_true, y_pred):
    con_mat = tf.math.confusion_matrix(labels=y_true, predictions=y_pred).numpy()
    con_mat_norm = np.around(
        con_mat.astype("float") / con_mat.sum(axis=1)[:, np.newaxis], decimals=2
    )

    print("Confusion matrix")
    print(con_mat)
    print("Normalized confusion matrix")
    print(con_mat_norm)


def classify_paragraph(s, model, ft, dim, prior=tf.math.log([0.8, 0.2])):
    words = s.split()
    V = len(words)
    x = np.zeros((V, dim))

    for ix, word in enumerate(words):
        vec = ft.get_word_vector(word)
        x[ix] = vec

    pred = model.predict(x, batch_size=V)
    # print(pred)
    return tf.reduce_sum(pred, axis=0) + prior


def main(args):
    print("Load word vectors...")
    dim = 300
    ft = fasttext.load_model("cc.sv." + str(dim) + ".bin")
    dim = ft.get_word_vector("hej").shape[0]
    print("Done.")
    classes = dict(seg=0, note=1)
    dataset, class_keys = get_set(ft, args.datapath, "train", classes=classes, upper_limit=10000)
    dataset = dataset.shuffle(10000, reshuffle_each_iteration=False)
    test_dataset = dataset.take(1000)
    train_dataset = dataset.skip(1000)
    train_dataset = train_dataset.batch(32)
    test_dataset = test_dataset.batch(32)

    model = get_model(dim, len(class_keys))
    print(train_dataset)
    print(test_dataset)
    model.fit(train_dataset, validation_data=test_dataset, epochs=args.epochs)

    #y_pred = model.predict_classes(test_dataset)
    y_pred = np.argmax(model.predict(test_dataset), axis=-1)

    y_true = test_dataset.map(lambda x, y: y)
    y_true = y_true.flat_map(lambda x: tf.data.Dataset.from_tensor_slices(x))
    y_true = np.array(list(y_true.as_numpy_iterator()))

    print_confusion_matrix(y_true, y_pred)

    class_numbers = {wd: ix for ix, wd in enumerate(class_keys)}
    print(class_numbers)
    numbers_classes = {ix: wd for ix, wd in enumerate(class_keys)}
    classified_paragraphs = get_paragraphs(class_numbers, args.datapath, upper_limit=100)

    real_classes = []
    pred_classes = []

    for paragraph, real_class in progressbar.progressbar(classified_paragraphs):
        real_ix = class_numbers[real_class]
        real_classes.append(real_ix)

        preds = classify_paragraph(paragraph, model, ft, dim)

        pred_ix = int(np.argmax(preds))
        pred_class = numbers_classes[pred_ix]
        print(paragraph[:100], real_class, pred_class)
        pred_classes.append(pred_ix)
        #print("real:", real_class, "pred:", pred_class, "correct:", real_class == pred_class)

    print_confusion_matrix(real_classes, pred_classes)

    model.save("segment-classifier/")


if __name__ == "__main__":
    argsparser = argparse.ArgumentParser(description=__doc__)
    argsparser.add_argument("--datapath", type=str, default="input/curation/")
    argsparser.add_argument("--epochs", type=int, default=25)
    args = argsparser.parse_args()
    main(args)
