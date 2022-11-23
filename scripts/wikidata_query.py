from SPARQLWrapper import SPARQLWrapper, JSON
import numpy as np
import pandas as pd
import os, argparse
import time
import re
from pyriksdagen.wikidata import query2df, separate_name_location, move_party_to_party_df
from pathlib import Path

def main(args):
	# Change query path to be from module!
	if args.queries:
		queries = args.queries
	else:
		queries = sorted([q.stem for q in Path("pyriksdagen/data/queries").glob('*.rq')])
	input_folders = ['name_location_specifier', 'alias', "member_of_parliament", "party_affiliation"]

	# Query for and store cleaned versions of metadata
	d = {}
	for q in queries:
		print(f"Query {q} started.")
		df = query2df(q, args.source)

		# Format values
		if 'riksdagen_id' in df.columns:
			df['riksdagen_id'] = df['riksdagen_id'].astype(str)

		if 'gender' in df.columns:
			df["gender"] = df["gender"].map({'kvinna':'woman', 'man':'man'})

		if q == 'minister':
			df["role"] = df["role"].str.replace('Sveriges', '').str.strip()

		if q == 'member_of_parliament':
			df["role"] = df["role"].str.extract(r'([A-Za-zÀ-ÿ]*ledamot)')

		# Store files needing additional preprocessing in input
		folder = 'corpus' if not q in input_folders else 'input'
		if folder == 'input':
			d[q] = df

		df.to_csv(f'{folder}/metadata/{q}.csv', index=False)

	# Process name and location files
	if d:
		for key in d.keys():
			if key not in queries:
				d['key'] = pd.read_csv(f'input/metadata/{key}.csv')
		name, loc = separate_name_location(d['name_location_specifier'], d['alias'])
		name.to_csv(f'corpus/metadata/name.csv', index=False)
		loc.to_csv(f'corpus/metadata/location_specifier.csv', index=False)

		mp_df, party_df = move_party_to_party_df(d['member_of_parliament'], d['party_affiliation'])
		mp_df.to_csv(f'corpus/metadata/member_of_parliament.csv', index=False)
		party_df.to_csv(f'corpus/metadata/party_affiliation.csv', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-q', '--queries', default=None, nargs='+', help='One or more sparql query files (separated by space)')
    parser.add_argument('-s', '--source', default=None, nargs='+', help='One or more of member_of_parliament | minister | speaker (separated by space)')
    args = parser.parse_args()
    main(args)
