"""
Find undetected introductions in the protocols. After finding an intro,
tag the next paragraph as an utterance.
"""
from pyparlaclarin.refine import format_texts
from pyriksdagen.db import load_patterns
from pyriksdagen.refine import (
    detect_mps,
    find_introductions,
    update_ids,
    update_hashes,
)
from pyriksdagen.utils import infer_metadata
from pyriksdagen.utils import protocol_iterators

from lxml import etree
import pandas as pd
import os, progressbar, argparse
from functools import partial
import multiprocessing
from tqdm import tqdm

def detect_intros(protocol, intro_df):
	intro_ids = intro_df.loc[intro_df['file_path'] == protocol, 'id'].tolist()
	parser = etree.XMLParser(remove_blank_text=True)
	root = etree.parse(protocol, parser).getroot()
	for elem in root.iter():
		xml_id = elem.get("{http://www.w3.org/XML/1998/namespace}id")
		if xml_id in intro_ids:
			elem.attrib['type'] = 'speaker'

	b = etree.tostring(
		root, pretty_print=True, encoding="utf-8", xml_declaration=True
	)

	f = open(protocol, "wb")
	f.write(b)
	f.close()


def main(args):
	protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end))    )    
	df = pd.read_csv('input/segmentation/intros.csv')
	detect_fun = partial(detect_intros, intro_df=df)
	with multiprocessing.Pool() as pool:
		for _ in tqdm(pool.imap(detect_fun, protocols), total=len(protocols)):
			pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    args = parser.parse_args()
    main(args)
