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

segment_classes = ["note", "u"]
class_possibilities = segment_classes + ['']
segments_with_speaker = ["note", "utterance"]
tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"




def write_df(df, csv_path):
	print(f"Writing changes to {csv_path}.")
	#df.to_csv(csv_path)
	df.to_csv("input/quality-control/write-testing.csv")




def get_elem(protocol, elem_id):

	elem = None
	protocol_year = protocol.split('-')[1]
	parser = etree.XMLParser(remove_blank_text=True)
	root = etree.parse(f"corpus/protocols/{protocol_year}/{protocol}.xml", parser).getroot()

	return root.xpath(f".//*[@xml:id='{elem_id}']")




def ck_segmentation(e):

	seg = etree.QName(e).localname
	newseg = 'abc'

	print(f"Element is segmented as --| {seg} |--")
	while newseg not in class_possibilities:
		newseg = input(f"Press enter to accept or type the correct segmentation class (must be one of {segment_classes}):")
		if len(newseg) == 0:
			newseg == ''
		print(f'you entered {newseg}')

	if len(newseg) > 0:
		seg = newseg

	comment = None
	if seg == "note":
		if "type" in e.attrib:
			if e.get("type") == "speaker":
				comment = 'intro'

	return seg, comment




def ck_speaker(e):

	speaker = None
	new_speaker = None

	if 'who' in e.attrib:
		print(f"Element is attributed to speaker --| {e.get('who')} |--.")
		speaker = e.get('who')
		new_speaker = input("Press enter to accept or add a new speaker ID now: ")
	else:
		print(f"Element is not assigned to a speaker.")
		new_speaker = input("Press enter to confirm this segment has no speaker or enter a speaker ID now: ")

	if len(new_speaker) > 0:
		speaker = new_speaker

	# to do: ck speaker against database of speaker IDs to make sure it exists / no typos
	
	return speaker




def main(args):
	csv_path = f"input/quality-control/sample_{args.decade}.csv"
	df = pd.read_csv(csv_path)

	driver = webdriver.Firefox()
	driver.get(f'https://{args.username}:{args.password}@betalab.kb.se/')

	input("Organize your windows and press enter to continue...")

	if not "checked" in df:
		print("No 'checked' column...adding it.")
		df['checked'] = None


	for ridx, row in df.iterrows():
		if not row['checked'] == True:
			print("Working on", row['protocol_id'], row['elem_id'])
			## open tabs
			driver.execute_script("window.open('');")
			driver.switch_to.window(driver.window_handles[1])
			driver.get(row['facs'])
			driver.execute_script("window.open('');")
			driver.switch_to.window(driver.window_handles[2])
			driver.get(row['github'])

			## do stuff
			E = get_elem(row['protocol_id'], row['elem_id'])
			if len(E) != 1:
				print(f"The element id {row['elem_id']} should find exactly 1 element, but it found {len(E)}. Something is probably wrong. Quitting.")
				sys.exit()
			e = E[0]
				
			segmentation, comment = ck_segmentation(e)
			speaker = None
			if segmentation in segments_with_speaker:
				speaker = ck_speaker(e)

			new_comment = input("Enter any comments about this row: ")
			if commment:
				if len(new_comment) > 0:
					comment = f"{comment}: {new_comment}" 
			else:
				if len(new_comment) > 0:
					comment = new_comment

			## update DF and write to csv
			df.at[ridx, 'segmentation'] = segmentation
			df.at[ridx, 'speaker'] = speaker
			df.at[ridx, 'comments'] = comment
			df.at[ridx, 'checked'] = True
			write_df(df, csv_path)	
			print("Row finished, moving on...\n")
		
			## close tabs
			driver.switch_to.window(driver.window_handles[2])
			driver.close()
			driver.switch_to.window(driver.window_handles[1])
			driver.close()
			driver.switch_to.window(driver.window_handles[0])
	driver.close()		
			
	print("No już, finito. Here's the dataframe:")
	print(df)





if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__, epilog="You need to specify a decade by its first year with -d")
	parser.add_argument("-d", "--decade", type=int, default=None, help="Start year of the decade (the one in the file name of input/quality-control/sample_<YEAR>.csv).")
	parser.add_argument("-u", "--username", type=str, default=None, help="Username for betalab (you only need this if its not set in your environemnt variables -- $KBLPASS).")
	parser.add_argument("-p", "--password", type=str, default=None, help="Password for betalab (you only need this if its not set in your environemnt variables -- $KBLUSER).")
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
