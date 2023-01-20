"""
Draw a random sample of the scanned image URLs
"""
import pandas as pd
from tqdm import tqdm
from lxml import etree
from pyriksdagen.utils import protocol_iterators
import multiprocessing
import argparse

def get_page_urls(protocol):
	parser = etree.XMLParser(remove_blank_text=True)
	root = etree.parse(protocol, parser).getroot()
	data = []
	for elem in root.iter():
		if 'pb' in elem.tag:
			data.append([protocol, elem.attrib.get('facs')])
	return pd.DataFrame(data, columns=['file', 'url'])

def main(args):
	page_url_df = pd.read_csv('input/segmentation/page_urls.csv')
	protocols = sorted([p for p in protocol_iterators("corpus/protocols/",
						start=args.start, end=args.end)
						if p not in page_url_df['file']])

	data = []
	with multiprocessing.Pool() as pool:
		for df in tqdm(pool.imap(get_page_urls, protocols), total=len(protocols)):
			data.append(df)
	df = pd.concat(data)

	df['year'] = df['file'].apply(lambda x: int(x.split('/')[2][:4]))
	df['decade'] = df['year'] // 10 * 10

	data = [page_url_df]
	for decade in sorted(set(df['decade'])):
		dfd = df[df['decade'] == decade]
		data.append(dfd.sample(args.n))
	df = pd.concat(data)
	df.to_csv('input/segmentation/page_urls.csv', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--n", type=int, default=5)
    args = parser.parse_args()
    main(args)
