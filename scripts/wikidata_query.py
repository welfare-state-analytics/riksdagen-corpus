'''
Creates csv files from wikidata queries, with cleaning limited to simple reformatting (no assumptions).
'''
from SPARQLWrapper import SPARQLWrapper, JSON
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
		df.to_csv('test.csv', index=False)

		# Drop columns
		df = df[[c for c in df.columns if c.endswith('.value')]]
		df.columns = df.columns.str.replace('.value', '', regex=False)

		# Rename columns
		try:
			df["wiki_id"] = df["wiki_id"].str.replace(r'(.*?\/)', '',  regex=True)
		except:
			pass
		df = df.rename(columns={'wiki_idLabel':'name'}) # name.rq
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
			df = df[['wiki_id'] + [col for col in df.columns if col != 'wiki_id']]
			df = df.sort_values(by='wiki_id')

		# Store currently unused data in input
		if query in ['motion.rq', 'interpellation.rq']:
			df.to_csv(f"input/metadata{query.replace('.rq', '.csv')}", index=False)

		# Separate name_location_specifier to 2 files
		elif query != 'name_location_specifier.rq':
			df.to_csv(f"corpus/metadata/{query.replace('.rq', '.csv')}", index=False)	

		else:
			# Make all names into rows
			name = df
			name["wiki_idAlt"] = name["wiki_idAlt"].apply(lambda x: x.split(',') if isinstance(x, str) else [])
			name["name"] = name.apply(lambda x: [x["name"]] + x["wiki_idAlt"], axis=1)
			name = name.drop("wiki_idAlt", axis=1)
			name = name.set_index('wiki_id')["name"].apply(pd.Series).stack().reset_index(level=-1, drop=True).astype(str).reset_index()
			wiki_id = name["wiki_id"]

			# Separate locations from names
			name = name[0].str.split(' [io] ', expand=True)
			name = name.apply(lambda x: x.str.replace('och', '').str.strip())
			name = name.rename(columns={0:'name'})
			name["wiki_id"] = wiki_id
			name["name"] = name["name"].str.replace(r'\(([^\)]+)\)', '', regex=True).str.strip()

			location = []
			for i, row in name.iterrows():
				for j in range(len(name.columns)-2):
					if row[j+1] != None:
						location.append([row["wiki_id"], row[j+1]])
			location = pd.DataFrame(location, columns=['wiki_id', 'location'])

			# Extend both files with name_in_riksdagen list
			alias = pd.read_csv('corpus/metadata/alias.csv')
			idx = alias["alias"].str.split(' i ').apply(lambda x: len(x) == 2)
			alias = alias.loc[idx].reset_index(drop=True)
			wiki_id = alias["wiki_id"]
			alias = alias["alias"].str.split(' i ', expand=True).rename(columns={0:'name', 1:'location'})
			alias["wiki_id"] = wiki_id

			name = name[['wiki_id', 'name']].append(alias[["wiki_id", "name"]])
			name = name.loc[~name["name"].isna()].drop_duplicates()
			location = location.append(location[["wiki_id", "location"]]).drop_duplicates()
			name.to_csv('corpus/metadata/name.csv', index=False)
			location.to_csv('corpus/metadata/location_specifier.csv', index=False)
			os.remove('corpus/metadata/alias.csv')

		print(f'Query {query} finished.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    default = queries = sorted([q for q in os.listdir(os.path.join('input', 'queries')) if q.endswith('.rq')])
    parser.add_argument('-q', '--queries', default=default, nargs='+', help='One or more sparql query files (separated by space)')
    args = parser.parse_args()
    main(args)
