from SPARQLWrapper import SPARQLWrapper, JSON
import numpy as np
import pandas as pd
from importlib_resources import files

def impute_query_string(source=None):
	# Defaults to all individuals
	if not source:
		source = ["member_of_parliament", "minister", "speaker"]
	
	strings = []
	for src in source:
		# Specific individual wikidata object
		if src.startswith('Q'):
			s = f"VALUES ?wiki_id {{ wd:{src} }}"
		# Category of wikidata objects
		else:
			s = files('pyriksdagen.data.queries').joinpath(f'{src}.txt').read_text()
		strings.append(s)
	return "\n} UNION {\n".join(strings)

def get_query_string(query_name):
	try:
		s = files('pyriksdagen.data.queries').joinpath(f'{query_name}.rq').read_text()
	except FileNotFoundError:
		print(f"File {query_name} not found")
	return s

def reduce_date_precision(date, precision):
	'''
	Truncates date to accurate length given precision level
	'''
	# Decade
	if int(precision) == 8:
		return str(int(date[:4]) // 10 * 10)
	# Year
	if int(precision) == 9:
		return date[:4]
	# Month
	if int(precision) == 10:
		return date[:7]
	# Day
	if int(precision) == 11:
		return date[:10]

def fix_dates(df):
	'''
	Converts date precision for all relevant cols and removes the precision columns
	'''
	for c in df.columns:
		if 'Precision' in c:
			base_name = c.replace('Precision', '')
			df.loc[df[base_name].notna(), base_name] =\
			df.loc[df[base_name].notna()].apply(lambda x: reduce_date_precision(x[base_name], x[c]), axis=1)
			df = df.drop(c, axis=1)
	return df

def clean_sparql_df(df, query_name):
	df = df.copy()

	# Clean columns
	df = df.rename(columns={'wiki_idLabel.value':'name'}) # avoid duplicate colnames
	df = df.rename(columns={'government.value':'government_id.value'})
	df = df.rename(columns={'party.value':'party_id.value'})
	df = df[[c for c in df.columns if c.endswith('.value') or c == 'name']]
	
	df.columns = df.columns.str.replace('.value', '', regex=False)
	df.columns = df.columns.str.replace('Label', '', regex=False)
	df = fix_dates(df) # use and drop date precision columns

	# Format values
	for colname in df.columns:
		if "_id" in colname:
			df[colname] = df[colname].str.split('/').str[-1]

	# Drop pseudo missing values of form "http://www.wikidata.org/.well-known..."
	idx, idy = np.where(df.astype(str).applymap(lambda x: 'http' in x))
	for x, y in zip(idx, idy):
		df.loc[x][y] = ''

	# Sort columns
	first_cols = [c for c in ['wiki_id', 'start', 'end'] if c in df.columns]
	other_cols = sorted([c for c in df.columns if c not in first_cols])
	df = df[first_cols+other_cols]

	# Sort rows
	first_cols.reverse()
	df = df.sort_values(by=list(first_cols+other_cols))
	return df

def query2df(query_name, source=None):
	query = get_query_string(query_name)
	source = impute_query_string(source)
	query = query.replace('PLACEHOLDER', source)
	sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
	sparql.setQuery(query)	
	sparql.setReturnFormat(JSON)
	try:
		results = sparql.query().convert()
	except:
		print(f"Query {query_name} failed")
	df = pd.json_normalize(results['results']['bindings'])
	df = clean_sparql_df(df, query_name)
	return df

def separate_name_location(name_location_specifier, alias):
	alias = alias[['wiki_id', 'alias']].rename(columns={'alias':'name'})		
	primary_df = name_location_specifier[['wiki_id', 'name']]
	secondary_df = name_location_specifier[['wiki_id', 'alias']].rename(columns={'alias':'name'})
	primary_df['primary_name'] = True
	secondary_df['primary_name'] = False
	alias['primary_name'] = False
	df = pd.concat([primary_df, secondary_df, alias]).dropna().drop_duplicates().reset_index(drop=True)

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
			drop_duplicates(subset=['wiki_id', 'name', 'primary_name'])

	loc =	pd.concat([df[['wiki_id', col]].rename(columns={col:'location'}) for col in loc_cols]).\
			dropna().drop_duplicates()

	# Sort values
	name = name[['wiki_id'] + sorted([col for col in name.columns if col != 'wiki_id'])]
	name = name.sort_values(by=list(name.columns))
	loc = loc[['wiki_id'] + sorted([col for col in loc.columns if col != 'wiki_id'])]
	loc = loc.sort_values(by=list(loc.columns))
	return name, loc

def move_party_to_party_df(mp_df, party_df):
	mp_parties = mp_df[party_df.columns]
	mp_parties = mp_parties[mp_parties['party_id'].notnull()]

	mp_parties = mp_parties.sort_values(["wiki_id", "start"])
	party_df = pd.concat([mp_parties, party_df])
	party_df = party_df.drop_duplicates()

	mp_df_cols = [col for col in mp_df.columns if col not in ["party", "party_id"]]

	return mp_df[mp_df_cols], party_df

