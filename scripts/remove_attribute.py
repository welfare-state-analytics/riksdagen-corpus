'''
Remove depreceated xml elements
'''
from pyriksdagen.utils import protocol_iterators, elem_iter
from lxml import etree
from tqdm import tqdm
import multiprocessing
from functools import partial
import argparse


def remove_attribute(protocol, key, value):
	parser = etree.XMLParser(remove_blank_text=True)
	root = etree.parse(protocol, parser).getroot()
	for elem in root.iter():
		# Remove key if not value is supplies, else remove value conditional on key
		if not value or (value and elem.attrib.get(key) == value):
			elem.attrib.pop(key, None)

	b = etree.tostring(
		root, pretty_print=True, encoding="utf-8", xml_declaration=True
	)
	f = open(protocol, "wb")
	f.write(b)
	f.close()


def main(args):
	protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
	remove_func = partial(remove_attribute, key=args.key, value=args.value)
	with multiprocessing.Pool() as pool:
		for _ in tqdm(pool.imap(remove_func, protocols), total=len(protocols)):
			pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("-k", "--key", type=str)
    parser.add_argument("-v", "--value", type=str, default=None)
    args = parser.parse_args()
    main(args)
