"""
Draw a random sample of the introductions
"""
from pyriksdagen.utils import protocol_iterators
import pandas as pd
from lxml import etree
from pyriksdagen.utils import elem_iter
import os
import datetime
from multiprocessing import Pool
from tqdm import tqdm
import argparse

def extract_intros(protocol):
	parser = etree.XMLParser(remove_blank_text=True)
	root = etree.parse(protocol, parser).getroot()
	xml_ns = "{http://www.w3.org/XML/1998/namespace}"
	git_prefix = 'https://github.com/welfare-state-analytics/riksdagen-corpus/blob/main'
	git_link = os.path.join(git_prefix, protocol)

	data = []
	new_speaker = False
	for tag, elem in elem_iter(root):
		if elem.attrib.get("type", None) == "speaker":
			new_speaker = True
			intro = elem.text.strip()
			uuid = elem.attrib.get(f'{xml_ns}id')

		if new_speaker and 'who' in elem.attrib:
			new_speaker = False
			who = elem.attrib["who"]
			data.append([uuid, who, intro, git_link])
	df = pd.DataFrame(data, columns=['uuid', 'who', 'intro', 'github'])
	return df


def sample(df, n=1, by='year', random_state=None):
	stratas = sorted(set(df[by]))
	data = []
	for strata in stratas:
		df_strata = df[df[by] == strata]
		data.append(df_strata.sample(n, random_state=random_state))
	return pd.concat(data).reset_index(drop=True)


def main(args):
	protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))

	# Extract intros
	data = []
	with Pool() as pool:
		for intros in tqdm(pool.imap(extract_intros, protocols), total=len(protocols)):
			data.append(intros)
	df = pd.concat(data).reset_index(drop=True)

	# Stratified sampling by year
	df['year'] = df['github'].str.extract(r'(?:\/)(\d{4,8})(?:\/)')
	df['year'] = df['year'].str[:4].astype(int)
	df = sample(df, n=args.n, random_state=args.seed)
	df.to_csv(f"input/accuracy/intro_sample_{str(datetime.date.today())}.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--n", type=int, default=5)
    args = parser.parse_args()
    main(args)
