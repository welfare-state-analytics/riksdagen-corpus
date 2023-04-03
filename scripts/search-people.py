#!/usr/bin/env python3
"""
Search for MPs and Ministers by name, year, and chamber.
	example usage:
		In a förstakamer protocol from 1872 there's an unidendified Anders Andersson.
		Search for MPs called Anders Andersson, returns individuals with a mandate in fk during the year 1872.
	Modes:
		interactive mode -- search multiple times using the prompt w/out reloading the data.
		one off mode     -- search once, loads DB each time.
"""
from argparse import RawTextHelpFormatter
import argparse, sys
import pandas as pd

chamber_roles = {
	'fk': "förstakammarledamot",
	'ak': "andrakammarledamot",
	'ek': "ledamot"
}




def load_data():
	names = pd.read_csv("corpus/metadata/name.csv")
	MPs = pd.read_csv("corpus/metadata/member_of_parliament.csv")
	MPs['start'] = MPs['start'].astype(str)
	MPs['end'] = MPs['end'].astype(str)
	MPs["start_year"] = MPs.apply(lambda x: x['start'][:4], axis=1)
	MPs["end_year"] = MPs.apply(lambda x: x['end'][:4], axis=1)
	MPs['start_year'] = pd.to_numeric(MPs['start_year'], errors='coerce')
	MPs['end_year'] = pd.to_numeric(MPs['end_year'], errors='coerce')
	ministers = pd.read_csv("corpus/metadata/minister.csv")
	ministers['start'] = ministers['start'].astype(str)
	ministers['end'] = ministers['end'].astype(str)
	ministers["start_year"] = ministers.apply(lambda x: x['start'][:4], axis=1)
	ministers["end_year"] = ministers.apply(lambda x: x['end'][:4], axis=1)
	ministers['start_year'] = pd.to_numeric(ministers['start_year'], errors='coerce')
	ministers['end_year'] = pd.to_numeric(ministers['end_year'], errors='coerce')
	print(ministers)
	return {"names":names,"MPs":MPs,"ministers":ministers}




def parse_params(params_raw):
	can_parse = True
	params = {
		'name': None,
		'Ename': None,
		'year': None,
		'cham': None
	}
	Ps = params_raw.split('-')
	Ps = [p for p in Ps if len(p) > 0]
	for p in Ps:
		if p.startswith("n") and params['name'] == None:
			params['name'] = p[2:].strip()
		elif p.startswith("e") and params['Ename'] == None:
			params['Ename'] = p[2:].strip()
		elif p.startswith("y") and params['year'] == None:
			params['year'] = int(p[2:])
		elif p.startswith("k") and params['cham'] == None:
			params['cham'] = p[2:].strip()
		else:
			can_parse = False
			print("BAD PARSE")
	return can_parse, params




def search_data(query_params, data):
	if query_params['name'] != None:
		names_df = data['names'][data['names'].name.str.contains(query_params['name'])]
	elif query_params['Ename'] != None:
		names_df = data['names'][data['names'].name == query_params['Ename']]

	print(f"There are {len(names_df)} name matches for your query...")

	if len(names_df) > 0:
		of_interest = []
		mp_matches_ids = None
		nameQids = names_df.wiki_id.unique()

		if query_params['year'] != None and query_params['cham'] != None:
			MP_matches = data['MPs'][(data['MPs']['wiki_id'].isin(nameQids)) & (data['MPs']['start_year'] <= query_params['year']) & (data['MPs']['end_year'] >= query_params['year']) & (data['MPs']['role'] == chamber_roles[query_params['cham']])]
			mp_matches_ids = MP_matches['wiki_id'].unique()
		elif query_params['cham'] == None:
			MP_matches = data['MPs'][(data['MPs']['wiki_id'].isin(nameQids)) & (data['MPs']['start_year'] <= query_params['year']) & (data['MPs']['end_year'] >= query_params['year'])]
			mp_matches_ids = MP_matches['wiki_id'].unique()

		# TO DO: add logic to handle  no date/no chamber and + chamber/no year

		if len(mp_matches_ids) == 0:
			print("... no MPs match all your search criteria.")
		else:
			print(f"... {len(mp_matches_ids)} MPs match other criteria.")
			for ID in mp_matches_ids:
				if ID not in of_interest:
					of_interest.append(ID)

		minister_matches_ids = None
		if query_params['year'] != None:
			minister_matches = data['ministers'][(data['ministers']['wiki_id'].isin(nameQids)) & (data['ministers']['start_year'] <= query_params['year']) & (data['ministers']['end_year'] >= query_params['year'])]
			minister_matches_ids = minister_matches['wiki_id'].unique()
			print(minister_matches)

		if len(minister_matches_ids) == 0:
			print("... no ministers match your search criteria")
		else:			
			print(f"... and {len(minister_matches_ids)} ministers match other criteria.")
			for ID in minister_matches_ids:
				if ID not in of_interest:
					of_interest.append(ID)

		for ID in of_interest:
			print("\n", f"~~~~WIKI_ID: {ID}")
			id_mp_df = data['MPs'][data['MPs'].wiki_id == ID]
			id_minister_df = data['ministers'][data['ministers'].wiki_id == ID]
			print("\n\tNAMES\n", data['names'][data['names'].wiki_id == ID].to_string())
			#print(id_mp_df, id_minister_df)
			if not id_mp_df.empty:
				print("\n\tMP ROLES\n", id_mp_df.to_string())
			else:
				print("This person held no MP roles in the specified time")
			if not id_minister_df.empty:
				print("\n\tMINISTERIAL ROLES\n", id_minister_df.to_string())
			else:
				print("This person held no ministerial roles in the specified time")
			print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")


	else:
		print("No name matches. Try again.")





def main(args):
	data = load_data()	
	if args.interactive_mode:
		options = ['s', 'search', 'exit']
		to_do = None
		while to_do not in options:
			to_do = input(f"What do you want to do?:\nChoose an option.\nOptions: {options}\n\n ")
			print(f"So you wan to {to_do}, eh?. OK")
			if to_do == "exit":
				print("kthxbye")
				sys.exit()
			elif to_do == "s" or to_do == "search":
				search_params = input("Enter search parameters: ")
				print(f"You entered {search_params}...\n\n")
				can_parse, params = parse_params(search_params)
				if can_parse:
					search_data(params, data)
				else:
					print("\nInvalid Query. Try again!\n")
			to_do = None
			print('\n\n')

	else:
		print("one-off search")
		params = {
			'name': args.name,
			'Ename': args.name_exact,
			'year': args.year,
			'cham': args.chamber
		}
		search_data(params, data)




if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__,  formatter_class=RawTextHelpFormatter)
	parser.add_argument("-i", "--interactive-mode", action="store_true", help="Set this to run multiple searches, otherwise you run a one-off search and have to reload the names data again. If you set this, no other arguments are necessary -- you will be prompted to enter the rest of the query.")
	parser.add_argument("-n", "--name", type=str, default=None, help="A (partial) name string to search for.")
	parser.add_argument("-e", "--name-exact", type=str, default=None, help="A name string to match exactly")
	parser.add_argument("-y", "--year", type=int, default=None, help="Year in which your unknown person was active.")
	parser.add_argument("-k", "--chamber", type=str, default=None, choices=["fk","ak","ek"], help="Chamber of protocol in which your unknown person appears")
	args = parser.parse_args()
	main(args)
