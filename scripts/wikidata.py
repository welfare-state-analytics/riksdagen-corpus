'''
Creates csv files from wikidata queries, with cleaning limited to simple reformatting (no assumptions).
'''
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import os
import time

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

	df.to_csv(os.path.join(path_wikidata, 'raw', query.replace('.rq', '.csv')), index=False)
	print(f'Query {query} finished.')