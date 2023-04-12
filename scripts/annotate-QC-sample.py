#!/usr/bin/env python3
"""
This script helps you populate a quality control annotations csv.

Use after generating a sample with ./sample_pages_new.py
"""
from lxml import etree
from selenium import webdriver
import selenium.webdriver.support.ui as ui
import argparse, os, contextlib, sys
import pandas as pd

segment_classes = ["note", "u", 'seg', "both"]
class_possibilities = segment_classes + ['']
segments_with_speaker = ["u"]

tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

mp_names = pd.read_csv("corpus/metadata/name.csv")
mp_affil = pd.read_csv("corpus/metadata/member_of_parliament.csv")

note_types = {
	"i": "inline",
	"m": "margin",
	"h": "head",
	"None": None
}




def write_df(df, csv_path):
	print(f"Writing changes to {csv_path}.")
	df.to_csv(csv_path, index=False)
	#df.to_csv("input/quality-control/write-testing.csv") # for debug




def get_elem(protocol, elem_id):
	elem = None
	protocol_year = protocol.split('-')[1]
	parser = etree.XMLParser(remove_blank_text=True)
	root = etree.parse(f"corpus/protocols/{protocol_year}/{protocol}.xml", parser).getroot()

	return root.xpath(f".//*[@xml:id='{elem_id}']")




def print_who_info(who):
	print("\n", f"Speaker: {who}")
	print("\n\tNAMES\n", mp_names[mp_names.wiki_id == who].to_string())
	print("\n\tACTIVE\n", mp_affil[mp_affil.wiki_id == who].to_string(), "\n")



def ck_speaker(e):
	confirm_opts = ['c', 'r', 'm']
	speaker = 'None'
	new_speaker = None

	if 'who' in e.attrib:
		print(f"Element is attributed to speaker --| {e.get('who')} |--.")
		speaker = e.get('who')
		print_who_info(speaker)
		new_speaker = input("Press enter to accept or add a new speaker ID now: ")
	else:
		print(f"Element is not assigned to a speaker.")
		new_speaker = input("Press enter to confirm this segment has no speaker or enter a speaker ID now: ")

	if len(new_speaker) > 0:
		confirm = 'abC'
		while confirm not in confirm_opts:
			print("You entered a new speaker for this segment")
			print_who_info(new_speaker)
			confirm = input("What do you want to do?\n\tc: confirm\n\tr: revert to " + speaker + "\n\tm: mistake - start function over\n")
		if confirm == "c":
			return new_speaker
		elif confirm == "r":
			return speaker
		elif confirm == "m":
			ck_speaker(e)
	else:
		return speaker




def get_note_type():
	nt = "Abc"	
	while nt not in note_types:
		print("What type of note is it?\n\ti: inline\n\tm: margin\n\th: head\n\tNone: use if other types don't apply\n")
		nt = input("Enter one of the above types: ")

	note_type = note_types[nt]

	return note_type




def ck_segmentation(e):
	seg = etree.QName(e).localname
	newseg = 'abc'
	speaker = None

	print(f"Element is segmented as --| {seg} |--")
	while newseg not in class_possibilities:
		newseg = input(f"Press enter to accept or type the correct segmentation class (must be one of {segment_classes}):")
		if len(newseg) == 0:
			newseg = ''
		print(f'you entered {newseg}')

	if len(newseg) > 0:
		seg = newseg

	if seg == "u":
		speaker = ck_speaker(e)
	elif seg == "seg":
		if e.getparent() is not None:
			speaker = ck_speaker(e.getparent())
		else:
			print("\n\n\nOh no!! seg elements should have a parent -- something is really wrong.\n\n....quitting...\n\n\n")
			sys.exit()
		seg = "u" 

	seg_type = None
	if seg == "note":
		if "type" in e.attrib:
			t = e.get("type")
			if t == "speaker":
				seg_type = 'intro'
			elif t == "date":
				seg_type = 'margin'
		if not seg_type:
			seg_type = get_note_type()
	elif seg == "both":
		seg = "note, seg"

	return seg, seg_type, speaker




def main(args):
	csv_path = f"input/quality-control/sample_{args.decade}.csv"
	df = pd.read_csv(csv_path)

	driver = None
	if args.tabs:
		driver = webdriver.Firefox()
		driver.get(f'https://{args.username}:{args.password}@betalab.kb.se/')
	else:
		kbdriver = webdriver.Firefox()
		kbdriver.get(f'https://{args.username}:{args.password}@betalab.kb.se/')
		ghdriver = webdriver.Firefox()
		ghdriver.get(f'https://github.com/')
		
	input("Organize your windows and press enter to continue...")

	if not "checked" in df:
		print("No 'checked' column...adding it.")
		df['checked'] = None

	# to do: potentially make opening/closing tabs more efficient
	#	i.e. don't close tabs if next row uses same protocol.
	#        ...well...
	#	It doesn't use too much resources or time to open/close
	#	tabs...
	for ridx, row in df.iterrows():
		if not row['checked'] == True:
			print("Working on", row['protocol_id'], row['elem_id'], "    ::    ", ridx, "of", len(df))
			## open tabs
			if driver:
				driver.execute_script("window.open('');")
				driver.switch_to.window(driver.window_handles[1])
				driver.get(row['facs'])
				driver.execute_script("window.open('');")
				driver.switch_to.window(driver.window_handles[2])
				driver.get(row['github'])
			else:
				kbdriver.execute_script("window.open('');")
				kbdriver.switch_to.window(kbdriver.window_handles[1])
				kbdriver.get(row['facs'])
				ghdriver.execute_script("window.open('');")
				ghdriver.switch_to.window(ghdriver.window_handles[1])
				ghdriver.get(row['github'])
				
	
			## do stuff
			E = get_elem(row['protocol_id'], row['elem_id'])
			if len(E) != 1:
				print(f"The element id {row['elem_id']} should find exactly 1 element, but it found {len(E)}. Something is probably wrong. Quitting.")
				sys.exit()
			e = E[0]
				
			segmentation, seg_type, speaker = ck_segmentation(e)

			comment = input("Enter any comments about this row: ")
			
			## update DF and write to csv
			df.at[ridx, 'segmentation'] = segmentation
			df.at[ridx, 'seg_type'] = seg_type
			df.at[ridx, 'speaker'] = speaker
			df.at[ridx, 'comments'] = comment
			df.at[ridx, 'checked'] = True
			write_df(df, csv_path)	
			print("Row finished, moving on...\n")
		
			## close tabs
			if driver:
				driver.switch_to.window(driver.window_handles[2])
				driver.close()
				driver.switch_to.window(driver.window_handles[1])
				driver.close()
				driver.switch_to.window(driver.window_handles[0])
			else:
				kbdriver.switch_to.window(kbdriver.window_handles[1])
				kbdriver.close()
				kbdriver.switch_to.window(kbdriver.window_handles[0])
				ghdriver.switch_to.window(ghdriver.window_handles[1])
				ghdriver.close()
				ghdriver.switch_to.window(ghdriver.window_handles[0])
	if driver:
		driver.close()		
	else:
		kbdriver.close()
		ghdriver.close()
	
	print("No już, finito. Here's the dataframe:")
	print(df)





if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__, epilog="You need to specify a decade by its first year with -d")
	parser.add_argument("-d", "--decade", type=int, default=None, help="Start year of the decade (the one in the file name of input/quality-control/sample_<YEAR>.csv).")
	parser.add_argument("-u", "--username", type=str, default=None, help="Username for betalab (you only need this if its not set in your environemnt variables -- $KBLPASS).")
	parser.add_argument("-p", "--password", type=str, default=None, help="Password for betalab (you only need this if its not set in your environemnt variables -- $KBLUSER).")
	parser.add_argument("-t", "--tabs", action="store_true", help="Set this if you want to open kblab and github in browser tabs, otherwise this script will open separate windows for each one.")
	args = parser.parse_args()

	if args.decade:
		if not args.password and not args.username:
			if "KBLUSER" in os.environ and "KBLPASS" in os.environ:
				args.password = os.environ.get("KBLPASS")
				args.username = os.environ.get("KBLUSER")
				main(args)
			else:
				print("\nSomehow you need to provide a kblabb username and password. Use args or set environment variables.\n")
				parser.print_help()
		else:
			main(args)
	else:
		print("\nThis script wants the -d.\n")
		parser.print_help()
