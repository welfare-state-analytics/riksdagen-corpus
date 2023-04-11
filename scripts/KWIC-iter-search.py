#!/usr/bin/env python3
"""
Iterates over the protocols in the specified range and searches for keywords or regex patterns.
KWIC results are saved as a csv and / or printed to stdout.
"""
from argparse import RawTextHelpFormatter
from datetime import datetime
from lxml import etree
from pyriksdagen.utils import elem_iter, protocol_iterators
from tqdm import tqdm
import argparse, re
import pandas as pd


tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"




def format_text(text):
	lines = text.split('\n')
	return ' '.join([l.strip() for l in lines])




def append_matches(matches, counter, rows, protocol, elem_id, elem_type, who, txt, context, facs, line_number):
	for m in matches:
		counter += 1
		s = m.start()
		e = m.end()
		left = txt[s-context:s]
		right = txt[e:e+context]
		prot = protocol.split('/')[-1][:-4]
		gh = f"https://github.com/welfare-state-analytics/riksdagen-corpus/blob/{args.branch}/{protocol}/#L{line_number}"
		if args.print or args.print_only:
			tqdm.write(f'{prot}: {txt[s-context:s]} --| {m.group(0)} |-- {txt[e:e+context]}')
		row = [protocol, elem_id, elem_type, who, s, e, left, m.group(0), right, facs, gh]
		rows.append(row)	
	return rows, counter




def main(args):
	dts = datetime.now().strftime("%Y%m%d-%H%M%S")
	if args.keyword:
		pattern = re.compile(rf'\b\S*{args.keyword}\S*\b', re.IGNORECASE)
	if args.regex_keyword:
		pattern = re.compile(rf'{args.regex_keyword}')

	search_u = True
	search_note = True

	if args.segment != False and args.note != False:
		search_u = args.segment
		search_note = args.note

	protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
	if args.chamber:
		protocols = [p for p in protocols if args.chamber in p]

	rows = []
	match_counter = 0

	for protocol in tqdm(protocols, total=len(protocols)):
		parser = etree.XMLParser(remove_blank_text=True)
		root = etree.parse(protocol, parser).getroot()
		facs = None
		for tag, elem in elem_iter(root):	
			if tag == "u" and search_u:
				who = elem.attrib.get("who")
				for subelem in elem:
					line_number = subelem.sourceline
					subelem_id = subelem.attrib.get(f'{xml_ns}id')
					txt = format_text(subelem.text)
					matches = re.finditer(pattern, txt)
					rows, match_counter = append_matches(matches, match_counter, rows, protocol, elem_id, "seg", who, txt, args.context, facs, line_number) 
			elif tag == "note" and search_note:
				line_number =  elem.sourceline
				elem_id = elem.attrib.get(f'{xml_ns}id')
				txt = format_text(elem.text)				
				matches = re.finditer(pattern, txt)
				rows, match_counter = append_matches(matches, match_counter, rows, protocol, elem_id, "note", None, txt, args.context, facs, line_number)
			elif tag == "pb":
				facs = elem.attrib.get("facs")

	if not args.print_only:
		print("Writing file...")
		df = pd.DataFrame(rows, columns = ["protocol", "elem_id", "elem_type", "who", "match_start", 
									"match_end", "left_context", "match", "right_context", "facs", "github"])
		df.to_csv(f"input/KWIC/{args.out_file}_{dts}.csv", index=False)


	print(f"\n\n\tFinito -- {match_counter} matches\n\n")




if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__,  formatter_class=RawTextHelpFormatter)
	parser.add_argument("-s", "--start", type=int, default=1867, help="Start year")
	parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
	parser.add_argument("-c", "--chamber", type=str, choices=["fk", "ak"], default=None,
			help="Search return results from a specific chamber in the bicameral period.\n(Default:None, means you search both chambers. If you set this, no ek results will be returned.)")
	parser.add_argument("-S", "--segment", action="store_true", help="Search only in utterance segments.")
	parser.add_argument("-n", "--note", action="store_true", help="Search only in notes.")
	parser.add_argument("-k", "--keyword", type=str, default=None, help="Search term.")
	parser.add_argument("-r", "--regex-keyword", type=str, default=None, help="Regular expression search term.\nWrap expression in single quotes, e.g. '\\bHerr\\S*\\b'.")
	parser.add_argument("-C", "--context", type=int, default=45, 
			help="N characters to the left & right of match in results file.")
	parser.add_argument("-o", "--out-file", type=str, default="KWIC-results", 
			help="Name of output file @ input/KWIC/")
	parser.add_argument("-b", "--branch", type=str, default="dev", help="Github branch (for links in the output csv).")
	parser.add_argument("-p", "--print", action="store_true", help="Print matches to stdout.")
	parser.add_argument("-P", "--print-only", action="store_true", help="Print matches to stdout; no output file.")
	args = parser.parse_args()
	if args.keyword == None and args.regex_keyword == None:
		print("\n\tYou have to search for a keyword or a regex-keyword.\n\n")
		parser.print_help()
	elif args.keyword != None and args.regex_keyword != None:
		print("\n\tYou can't set keyword *AND* a regex-keyword\n\n")
		parser.print_help()
	else:
		main(args)
