from pyriksdagen.refine import update_hashes
from pyparlaclarin.read import speeches_with_name
from lxml import etree
from pathlib import Path
import seaborn as sbn
from matplotlib import pyplot as plt
import numpy as np


def clean(word):
    word = word.lower()
    return word


def get_distribution(manual=True):
    d = {}
    parser = etree.XMLParser(remove_blank_text=True)

    corpus = Path(".") / "corpus"
    i = 0
    for folder in corpus.glob("*"):
        print(folder)
        if folder.is_dir():
            for protocol in folder.glob("*.xml"):
                f = protocol.open()
                root = etree.parse(f, parser).getroot()
                f.close()

                for speech in speeches_with_name(root):
                    for wd in speech.split():
                        wd = clean(wd)
                        d[wd] = d.get(wd, 0) + 1
        if i >= 5:
            break
        else:
            i += 1

    return {k: v for k, v in d.items() if v >= 5 and v <= 1000}


if __name__ == "__main__":
    # begin the unittest.main()
    d = get_distribution()
    v = np.array(list(d.values()))
    print(v, type(v))
    sbn.set_theme()
    g = sbn.histplot(v, bins=20, log_scale=(True, True))
    plt.show()
