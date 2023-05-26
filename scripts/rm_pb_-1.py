#!/usr/bin/env python3
from pyriksdagen.utils import protocol_iterators
from tqdm import tqdm
from lxml import etree
import argparse



def rm_pb(protocol):
	tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
	xml_ns = "{http://www.w3.org/XML/1998/namespace}"
	parser = etree.XMLParser(remove_blank_text=True)
	root = etree.parse(protocol, parser).getroot()
	pbm1 = root.findall(f"{tei_ns}pb[@n='-1']")

	if len(pbm1) > 0:
		for pb in pbm1:
			pb.getparent().remove(pb)

	b = etree.tostring(
		root, pretty_print=True, encoding="utf-8", xml_declaration=True
	)
	f = open(protocol, "wb")
	f.write(b)




def main(args):
	protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
	for p in tqdm(protocols, total=len(protocols)):
		rm_pb(p)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("-s", "--start", type=int, default=1920, help="Start year")
	parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
	args = parser.parse_args()
	main(args)
