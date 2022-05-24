'''
TODO:
1. Fix targeted querying
2. Update wikidata_process
'''

from SPARQLWrapper import SPARQLWrapper, JSON
import numpy as np
import pandas as pd
import os, argparse
import time
import re
from pyriksdagen.wikidata import query2df, separate_name_location

# Change query path to be from module!
queries = sorted([q.replace('.rq', '') for q in os.listdir("pyriksdagen/data/queries")])
input_folders = ['name_location_specifier', 'alias']

# Query for and store cleaned versions of metadata
d = {}
for q in queries:
	print(f"Query {q} started.")
	df = query2df(q)

	# Format values
	if 'riksdagen_id' in df.columns:
		df['riksdagen_id'] = df['riksdagen_id'].astype(str)

	if 'gender' in df.columns:
		df["gender"] = df["gender"].map({'kvinna':'woman', 'man':'man'})

	if q == 'minister':
		df["role"] = df["role"].str.replace('Sveriges', '').str.strip()

	if q == 'member_of_parliament':
		df["role"] = df["role"].str.extract(r'([A-Za-zÀ-ÿ]*ledamot)')

	folder = 'corpus' if not q in input_folders else 'input'
	#df.to_csv(f'{folder}/metadata/{q}.csv', index=False)

	# Store files which need additional processing
	if folder == 'input':
		d[q] = df

# Process name and location files
if d:
	for key in d.keys():
		if key not in queries:
			d['key'] = pd.read_csv(f'input/metadata/{key}.csv')
	name, loc = separate_name_location(d['name_location_specifier'], d['alias'])
	#name.to_csv(f'corpus/metadata/name.csv', index=False)
	#loc.to_csv(f'corpus/metadata/location_specifier.csv', index=False)

#if __name__ == "__main__":
#    parser = argparse.ArgumentParser(description=__doc__)
#    default = queries = sorted([q for q in os.listdir(os.path.join('input', 'queries')) if q.endswith('.rq')])
#    parser.add_argument('-q', '--queries', default=default, nargs='+', help='One or more sparql query files (separated by space)')
#    args = parser.parse_args()
#    main()
