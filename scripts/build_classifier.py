import os
import fasttext
import numpy as np
import tensorflow as tf

classdict = {
    "BEGINSPEECH": "speech",
    "CONTINUESPEECH": "speech",
    "BEGINDESCRIPTION": "note",
    "CONTINUEDESCRIPTION": "note",
    "ENDSPEECH": None,
    "ENDDESCRIPTION": None,
}


def get_files(traintest="train/", indices=[0]):
    folder = "input/curation/"
    for decennium in os.listdir(folder):
        decennium_path = folder + decennium + "/"
        if os.path.isdir(decennium_path):
            for index in indices:
                fpath = decennium_path + traintest + str(index) + "/annotated.txt"
                yield open(fpath).read()


def get_pairs(indices):
    strings = get_files(indices=indices)
    current_class = None
    for string in strings:
        words = string.split()

        for word in words:
            if word in classdict:
                current_class = classdict[word]
            elif current_class is not None:
                yield (word, current_class)


def get_set(ft, indices=[0]):
    x = []
    y = []
    classes = dict()

    for w, c in get_pairs(indices):
        classes[c] = classes.get(c, 0) + 1
        if classes[c] < 1300:
            x.append(w)
            y.append(c)

    class_keys = list(classes.keys())
    y = [class_keys.index(y_ix) for y_ix in y]

    for ix, x_ix in enumerate(x):
        x[ix] = ft.get_word_vector(x_ix)

    x = tf.constant(x)
    y = tf.constant(y)
    dset = tf.data.Dataset.from_tensor_slices((x, y))

    return dset, class_keys


def get_paragraphs(class_numbers, traintest="test/"):
    current_class = None
    classified_paragraphs = []

    for string in get_files(traintest=traintest, indices=[0, 1]):
        paragraphs = string.split("\n\n")

        for paragraph in paragraphs:
            current_paragraph = []
            words = paragraph.split()

            for word in words:
                if word in classdict:
                    p = " ".join(current_paragraph)
                    if current_class is not None and len(p) > 0:
                        classified_paragraphs.append((p, current_class))
                    current_paragraph = []
                    if classdict[word] is not None:
                        current_class = class_numbers[classdict[word]]
                    else:
                        current_class = None
                else:
                    current_paragraph.append(word)

            last_p = " ".join(current_paragraph)
            if len(last_p) > 0 and current_class is not None:
                classified_paragraphs.append((last_p, current_class))

    return classified_paragraphs


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
    biases = model.predict(np.zeros(x.shape), batch_size=V)
    # print(pred)
    return tf.reduce_sum(pred, axis=0) + prior


def main():
    print("Load word vectors...")
    dim = 300
    ft = fasttext.load_model("cc.sv." + str(dim) + ".bin")
    dim = ft.get_word_vector("hej").shape[0]
    print("Done.")

    dataset, class_keys = get_set(ft, indices=[0, 1])
    dataset = dataset.shuffle(10000, reshuffle_each_iteration=False)
    test_dataset = dataset.take(500)
    train_dataset = dataset.skip(500)
    train_dataset = train_dataset.batch(32)
    test_dataset = test_dataset.batch(32)

    model = get_model(dim, len(class_keys))
    model.fit(train_dataset, validation_data=test_dataset, epochs=25)

    y_pred = model.predict_classes(test_dataset)
    y_true = test_dataset.map(lambda x, y: y)
    y_true = y_true.flat_map(lambda x: tf.data.Dataset.from_tensor_slices(x))
    y_true = np.array(list(y_true.as_numpy_iterator()))

    print_confusion_matrix(y_true, y_pred)

    class_numbers = {wd: ix for ix, wd in enumerate(class_keys)}
    classified_paragraphs = get_paragraphs(class_numbers)

    real_classes = []
    pred_classes = []

    for paragraph, real_class in classified_paragraphs:
        real_classes.append(real_class)
        preds = classify_paragraph(paragraph, model, ft, dim)
        ix = int(np.argmax(preds))
        pred_classes.append(ix)
        print("real:", real_class, "pred:", ix, "correct:", real_class == ix)

    print_confusion_matrix(real_classes, pred_classes)

    model.save("segment-classifier/")


if __name__ == "__main__":
    main()
