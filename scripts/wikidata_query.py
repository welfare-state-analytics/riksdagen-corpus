'''
Creates csv files from wikidata queries, with cleaning limited to simple reformatting (no assumptions).
'''
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import os
import time
import re

def query2df(query: str):
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
	raise

sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
path_wikidata = 'input/wikidata'
queries = sorted([q for q in os.listdir(os.path.join(path_wikidata, 'queries')) if q.endswith('.rq')])

for query in queries:
	with open(os.path.join(path_wikidata, 'queries', query), 'r') as f:
		df = try_query(f.read())
	
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

	# Format dates
	date_cols = [c for c in df.columns if c in ['start', 'end', 'born', 'dead']]
	for col in date_cols:
		df[col] = df[col].str.replace(r'T.+', '',  regex=True)

	if query != 'name_location.rq':
		df.to_csv(os.path.join(path_wikidata, 'raw', query.replace('.rq', '.csv')), index=False)
	
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
		alias = pd.read_csv(os.path.join(path_wikidata, 'raw', 'alias.csv'))
		idx = alias["alias"].str.split(' i ').apply(lambda x: len(x) == 2)
		alias = alias.loc[idx].reset_index(drop=True)
		wiki_id = alias["wiki_id"]
		alias = alias["alias"].str.split(' i ', expand=True).rename(columns={0:'name', 1:'location'})
		alias["wiki_id"] = wiki_id

		name = name.append(alias[["wiki_id", "name"]]).drop_duplicates()
		location = location.append(location[["wiki_id", "location"]]).drop_duplicates()
		name.to_csv(os.path.join(path_wikidata, 'raw', 'name.csv'), index=False, columns=['wiki_id', 'name'])
		location.to_csv(os.path.join(path_wikidata, 'raw', 'location.csv'), index=False)
		os.remove(os.path.join(path_wikidata, 'raw', 'alias.csv'))

	print(f'Query {query} finished.')