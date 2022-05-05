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
from pyriksdagen.wikidata import *

queries = [q.replace('.rq', '') for q in os.listdir("scripts/pyriksdagen/data/queries")]

d = {}
for q in sorted(queries):
	print(f"Query {q} started.")
	df = query2df(q)

	if q in ['name_location_specifier', 'alias']:
		d[q] = df

	else:
		df.to_csv(f'corpus/metadata/{q}.csv', index=False)

if d:
	for key in d.keys():
		if key not in queries:
			d['key'] = pd.read_csv(f'corpus/metadata/{key}.csv')
	name, loc = separate_name_location(d['name_location_specifier'], d['alias'])
	name.to_csv(f'corpus/metadata/name.csv', index=False)
	loc.to_csv(f'corpus/metadata/location_specifier.csv', index=False)

#if __name__ == "__main__":
#    parser = argparse.ArgumentParser(description=__doc__)
#    default = queries = sorted([q for q in os.listdir(os.path.join('input', 'queries')) if q.endswith('.rq')])
#    parser.add_argument('-q', '--queries', default=default, nargs='+', help='One or more sparql query files (separated by space)')
#    args = parser.parse_args()
#    main(args)
