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
	return {"names":names,"MPs":MPs,"ministers":ministers}




def parse_search_params(params_raw):
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




def dump_people_info(Qids, data):
	for ID in Qids:
		print("\n", f"~~~~WIKI_ID: {ID}")
		id_mp_df = data['MPs'][data['MPs'].wiki_id == ID]
		id_minister_df = data['ministers'][data['ministers'].wiki_id == ID]
		print("\n\tNAMES\n", data['names'][data['names'].wiki_id == ID].to_string())
		if not id_mp_df.empty:
			print("\n\tMP ROLES\n", id_mp_df.to_string())
		else:
			print("This person held no MP roles in the specified time (if specified).")
		if not id_minister_df.empty:
			print("\n\tMINISTERIAL ROLES\n", id_minister_df.to_string())
		else:
			print("This person held no ministerial roles in the specified time (if specified).")
		print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")




def search_data(query_params, data):
	if query_params['name'] != None:
		names_df = data['names'][data['names'].name.str.contains(query_params['name'])]
	elif query_params['Ename'] != None:
		names_df = data['names'][data['names'].name == query_params['Ename']]

	print(f"There are {len(names_df)} name matches for your query...")

	if len(names_df) > 0:
		nameQids = names_df.wiki_id.unique()
		if query_params['year'] == None and query_params['cham'] == None:
			dump_people_info(nameQids, data)
		else:
			of_interest = []
			mp_matches_ids = None
			minister_matches_ids = None

			if query_params['year'] != None and query_params['cham'] != None:
				MP_matches = data['MPs'][(data['MPs']['wiki_id'].isin(nameQids)) & 
											(data['MPs']['start_year'] <= query_params['year']) & 
											(data['MPs']['end_year'] >= query_params['year']) & 
											(data['MPs']['role'] == chamber_roles[query_params['cham']])
										]
				mp_matches_ids = MP_matches['wiki_id'].unique()
				minister_matches = data['ministers'][(data['ministers']['wiki_id'].isin(nameQids)) & 
														(data['ministers']['start_year'] <= query_params['year']) & 
														(data['ministers']['end_year'] >= query_params['year']) &
														(data['ministers']['role'] == chamber_roles[query_params['cham']])
													]
				minister_matches_ids = minister_matches['wiki_id'].unique()
			elif query_params['cham'] == None:
				MP_matches = data['MPs'][(data['MPs']['wiki_id'].isin(nameQids)) & 
											(data['MPs']['start_year'] <= query_params['year']) & 
											(data['MPs']['end_year'] >= query_params['year'])
										]
				mp_matches_ids = MP_matches['wiki_id'].unique()
				minister_matches = data['ministers'][(data['ministers']['wiki_id'].isin(nameQids)) & 
														(data['ministers']['start_year'] <= query_params['year']) & 
														(data['ministers']['end_year'] >= query_params['year'])
													]
				minister_matches_ids = minister_matches['wiki_id'].unique()

			elif query_params['year'] == None:
				pass
				MP_matches = data['MPs'][(data['MPs']['wiki_id'].isin(nameQids)) & 
											(data['MPs']['role'] == chamber_roles[query_params['cham']])
										]
				mp_matches_ids = MP_matches['wiki_id'].unique()
				minister_matches = data['ministers'][(data['ministers']['wiki_id'].isin(nameQids)) & 
														(data['ministers']['role'] == chamber_roles[query_params['cham']])
													]
				minister_matches_ids = minister_matches['wiki_id'].unique()


			if not mp_matches_ids.any():
				print("... no MPs match all your search criteria.")
			else:
				print(f"... {len(mp_matches_ids)} MPs match other criteria.")
				for ID in mp_matches_ids:
					if ID not in of_interest:
						of_interest.append(ID)

			if not minister_matches_ids.any():
				print("... no ministers match your search criteria")
			else:			
				print(f"... and {len(minister_matches_ids)} ministers match other criteria.")
				for ID in minister_matches_ids:
					if ID not in of_interest:
						of_interest.append(ID)

			dump_people_info(of_interest, data)
	else:
		print("No name matches. Try again.")




def main(args):
	data = load_data()	
	if args.interactive_mode:
		options = ['s', 'search','l', 'lookup', 'e', 'exit']
		to_do = None
		while to_do not in options:
			to_do = input(f"What do you want to do?:\nChoose an option.\nOptions: {options}\n\n ")
			if to_do == 'e' or to_do == "exit":
				print("You want to exit :(")
				print("\n\tkthxbye\n")
				sys.exit()
			elif to_do == "s" or to_do == "search":
				print("You want to search. Use the following arguments (just like running the one-off mode).")
				print("\t-n NAME -y YEAR -k CHAMBER")
				search_params = input("Enter search parameters: ")
				print(f"You entered {search_params}...\n\n")
				can_parse, params = parse_search_params(search_params)
				if can_parse:
					search_data(params, data)
				else:
					print("\nInvalid Query. Try again!\n")
			elif to_do == "l" or to_do == "lookup":
				print("You want to lookup people by their wiki-id. Like this:")
				print("\tQ1234 Q5678")
				Qids_raw = input("Enter wiki IDs: ")
				Qids = Qids_raw.split(' ')
				dump_people_info(Qids, data)

			to_do = None
			print('\n\n')

	else:
		if args.wiki_ids:
			dump_people_info(args.wiki_ids, data)
		else:
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
	parser.add_argument("-q", "--wiki-ids", nargs="+", help="Wiki ID lookup (if you use this argument, no others will be considered).")
	args = parser.parse_args()
	main(args)
