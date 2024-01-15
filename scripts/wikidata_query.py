"""
Query wikidata for metadata, process it and save it in corpus/metadata
"""
from SPARQLWrapper import SPARQLWrapper, JSON
import numpy as np
import pandas as pd
import os, argparse
import time
import re
from pyriksdagen.wikidata import (
	query2df,
	separate_name_location,
	move_party_to_party_df,
	elongate_external_ids,
)
from pyriksdagen.db import clean_person_duplicates
from pathlib import Path

def track_missing_id(df, l, id_map=None):
	no_id = df.loc[pd.isna(df["swerik_id"])]
	for i, r in no_id.iterrows():
		tmpdf = df.loc[(df['government'] == r['government']) & (df['role'] == r['role']) & (df['wiki_id'] == r['wiki_id']) & (pd.notnull(df["swerik_id"]))]
		if tmpdf.empty:
			found = False
			if not id_map.empty:
				tmpidmap = id_map.loc[id_map['wiki_id'] == r['wiki_id']].copy()
				if not tmpidmap.empty:
					tmpidmap.reset_index(drop=True, inplace=True)
					swerik_id = tmpidmap.at[0, "swerik_id"]
					df.at[i, "swerik_id"] = swerik_id
					found = True
			if found == False:
				if r['wiki_id'] not in l:
					l.append(r['wiki_id'])

	df = df.loc[pd.notnull(df['swerik_id'])].copy()
	df.drop(columns=["wiki_id"], inplace=True)
	return df.reset_index(drop=True), l

def main(args):
	# Change query path to be from module!
	if args.queries:
		queries = args.queries
	else:
		queries = sorted([q.stem for q in Path("pyriksdagen/data/queries").glob('*.rq')])
	input_folders = ['name_location_specifier', 'alias', "member_of_parliament", "party_affiliation"]

	# Query for and store cleaned versions of metadata
	d = {}
	no_swerik_id = []
	id_map = None
	if  "wiki_id" in queries:
		print(f"Query Wiki ID started.")
		id_map = query2df("wiki_id", args.source)
		print(type(id_map))
		id_map = id_map.drop_duplicates()
		id_map.to_csv(f'corpus/metadata/wiki_id.csv', index=False)

	for q in queries:
		if q == "wiki_id":
			continue
		print(f"Query {q} started.")
		df = query2df(q, args.source)
		print(df, len(df))
		# Format values
		if 'riksdagen_id' in df.columns:
			df['riksdagen_id'] = df['riksdagen_id'].astype(str)

		if 'gender' in df.columns:
			df["gender"] = df["gender"].map({'kvinna':'woman', 'man':'man'})

		if q == 'minister':
			df["role"] = df["role"].str.replace('Sveriges', '').str.strip()
			df, no_swerik_id = track_missing_id(df, no_swerik_id, id_map=id_map)

		if q == 'member_of_parliament':
			df["role"] = df["role"].str.extract(r'([A-Za-zÀ-ÿ]*ledamot)')
			df, no_swerik_id = track_missing_id(df, no_swerik_id, id_map=id_map)

		if q == 'speaker':
			df, no_swerik_id = track_missing_id(df, no_swerik_id, id_map=id_map)

		if q == "external_identifiers":
			df = elongate_external_ids(df)

		# Store files needing additional preprocessing in input
		folder = 'corpus' if not q in input_folders else 'input'
		if folder == 'input':
			d[q] = df

		if q == 'person':
			df = clean_person_duplicates(df)
			
		df = df.drop_duplicates()
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

	if len(no_swerik_id) > 0:
		print("Some entities returned in the queries seem not to have a swerik ID. Check and add an ID, then requery.")
	with open("input/metadata/no_swerik_id_query_results.txt", "w+") as outf:
		[outf.write(f"{_}\n") for _ in no_swerik_id]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-q', '--queries', default=None, nargs='+', help='One or more sparql query files (separated by space)')
    parser.add_argument('-s', '--source', default=None, nargs='+', help='One or more of member_of_parliament | minister | speaker (separated by space)')
    args = parser.parse_args()
    main(args)
