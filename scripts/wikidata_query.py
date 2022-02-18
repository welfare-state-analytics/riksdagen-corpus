'''
Creates csv files from wikidata queries, with cleaning limited to simple reformatting (no assumptions).
'''
from SPARQLWrapper import SPARQLWrapper, JSON
import numpy as np
import pandas as pd
import os, argparse
import time
import re

def query2df(query: str):
	'''TODO: Change delimiter=";" to avoid splitting names incorrectly'''
	sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
	sparql.setQuery(query)	
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	results = pd.json_normalize(results['results']['bindings'])
	return results

def try_query(query: str, max_tries=3):
	for i in range(3):
		try:
			df = query2df(query)
			return df
		except:
			time.sleep(3)
	raise ValueError('Query timeout/forbidden.')

def main(args):
	for query in args.queries:
		with open(os.path.join('input', 'queries', query), 'r') as f:
			df = query2df(f.read())
		
		# Drop columns
		df = df[[c for c in df.columns if c.endswith('.value')]]
		df.columns = df.columns.str.replace('.value', '', regex=False)

		# Format url -> id
		try:
			df["wiki_id"] = df["wiki_id"].str.replace(r'(.*?\/)', '',  regex=True)
		except:
			pass

		# Rename columns
		df = df.rename(columns={'wiki_idLabel':'name'})
		df.columns = df.columns.str.replace('Label', '', regex=False)

		# Map values
		if 'gender' in df.columns:
			df["gender"] = df["gender"].map({'kvinna':'woman', 'man':'man'})

		if query == 'minister.rq':
			df["role"] = df["role"].str.replace('Sveriges', '').str.strip()

		# Format dates
		date_cols = [c for c in df.columns if c in ['start', 'end', 'born', 'dead', 'date']]
		for col in date_cols:
			df[col] = df[col].str.replace(r'T.+', '',  regex=True)

		if 'riksdagen_id' in df.columns:
			df['riksdagen_id'] = df['riksdagen_id'].astype(str)

		# Sort values
		if 'wiki_id' in df.columns:
			df = df[['wiki_id'] + sorted([col for col in df.columns if col != 'wiki_id'])]
		df = df.sort_values(by=list(df.columns))

		# Store currently unused data in input
		if query in ['motion.rq', 'interpellation.rq']:
			df.to_csv(f"input/metadata/{query.replace('.rq', '.csv')}", index=False)

		# Separate name_location_specifier to 2 files
		elif query != 'name_location_specifier.rq':
			df.to_csv(f"corpus/metadata/{query.replace('.rq', '.csv')}", index=False)	

		else:
			# Stack dfs on eachother with indicator of primary name
			alias = pd.read_csv('corpus/metadata/alias.csv')
			alias['name'] = alias['alias'] # trickery
			df = df.append(alias)
			df = pd.concat([
				df[['wiki_id', 'name']].assign(primary_name=np.ones(len(df), dtype=bool)),
				df[['wiki_id', 'alias']].assign(primary_name=np.zeros(len(df), dtype=bool)).rename(columns={'alias':'name'})
				])
			df = df.dropna(subset=['name']).reset_index(drop=True)

			# Split names and location specifiers
			names = df['name'].str.split(' [io] ', expand=True)
			loc_cols = [i for i in range(len(df.columns)-1)]
			names.columns = ['name']+loc_cols
			df = df.drop('name', axis=1)
			df = df.join(names, how='left')
			
			# Cleaning
			df = df[~df['name'].str.contains(',')]
			df[loc_cols] = df[loc_cols].apply(lambda x: x.str.replace('och','').str.strip())
			df['name'] = df['name'].str.replace(r'\([^()]*\)', '', regex=True)
			df['name'] = df['name'].apply(lambda x: ' '.join(x.split()))
			
			# Drop duplicates
			name = 	df[['wiki_id', 'name', 'primary_name']].\
					sort_values(by=['primary_name'], ascending=False).\
					drop_duplicates(subset=['wiki_id', 'primary_name'])
			
			loc =	pd.concat([df[['wiki_id', col]].rename(columns={col:'location'}) for col in loc_cols]).\
					dropna().drop_duplicates()
			
			# Sort values
			name = name[['wiki_id'] + sorted([col for col in name.columns if col != 'wiki_id'])]
			name = name.sort_values(by=list(name.columns))
			loc = loc[['wiki_id'] + sorted([col for col in loc.columns if col != 'wiki_id'])]
			loc = loc.sort_values(by=list(loc.columns))
			name.to_csv('corpus/metadata/name.csv', index=False)
			loc.to_csv('corpus/metadata/location_specifier.csv', index=False)
			os.remove('corpus/metadata/alias.csv')

		print(f'Query {query} finished.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    default = queries = sorted([q for q in os.listdir(os.path.join('input', 'queries')) if q.endswith('.rq')])
    parser.add_argument('-q', '--queries', default=default, nargs='+', help='One or more sparql query files (separated by space)')
    args = parser.parse_args()
    main(args)
