'''
Generates metadata files from wikidata.
TODO: 	1. ~1/3 of party metadata is missing atm, gather from other wikidata objects.
Note: - It seems like ministers after 1970 have same start/end date in observation query,
#		probably due to them getting replacements. So should maybe drop these observations?
'''
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import os, json

def query2df(query: str):
	sparql.setQuery(query)	
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	results = pd.json_normalize(results['results']['bindings'])
	return results

def clean_columns(df):
	"Standard cleaning removing unnecesary columns, etc."
	df = df.fillna('')
	df = df[[col for col in df.columns if col.endswith('.value')]]
	df.columns = [col.split('.')[0] for col in df.columns]
	df["url"] = df["wiki_id"]
	df["wiki_id"] = list(map(lambda x: x.split('/')[-1], df["wiki_id"]))
	df = df.rename(columns={'wiki_idLabel':'name'})
	df.columns = df.columns.str.replace('Label', '')
	return df

def check_unique(df):
	"Find conflicting information on individual level"
	conflicts = {}
	if len(set(df["wiki_id"])) != len(df):
		variables = [var for var in df.columns if var not in ['wiki_id', 'url']]
		for var in variables:
			x = df.groupby('wiki_id')[var].apply(lambda x: len(set(x)))
			if multiples := x.loc[x > 1].index.tolist():
				conflicts[var] = multiples
	return conflicts

def clean_dates(df, dates: list):
	"Transforms multiple columns: ISO 8601(?) --> YYYY-MM-DD"
	for d in dates:
		df[d] = list(map(lambda x: x.split('T')[0], df[d]))

def check_dates(df):
	"Find missing dates on entry level (and remove these entries)"
	missing_start_ids = []
	missing_end_ids = []
	drops = 0
	for i, row in df.iterrows():
		missing = 0
		if row["start"] == '':
			missing_start_ids.append(row["wiki_id"])
			missing = 1
		# Requires start date not to be missing in order to check end
		elif len(row["end"]) != 10 and int(row["start"][:4]) < 2018:
			missing_end_ids.append(row["wiki_id"])
			missing = 1
		if missing == 1:
			df.drop(i, inplace=True)
			drops += 1
	df.reset_index(drop=True)
	print(f'{drops} observations dropped due to missing start/end values.')
	return (missing_start_ids, missing_end_ids)

def individual():
	"Individual level data"
	with open(os.path.join(path_queries, 'individual.rq'), 'r') as f:
		q = f.read()
	df = query2df(q)
#	df.to_csv('test.csv', index=False)
#	df = pd.read_csv('test.csv')
	df = clean_columns(df)
	df = df.replace({'chamber':{'ledamot av Sveriges riksdag':'Enkammarriksdagen',\
	'förstakammarledamot':'Första kammaren', 'andrakammarledamot':'Andra kammaren'}})

	# Reduce dates to year to avoid conflicting information
	clean_dates(df, ['born', 'dead'])
	
	# Remove dates which still have conflicts
	conflicts = check_unique(df)
	for var, values in conflicts.items():
		for value in values:
			df.loc[df["wiki_id"] == value, var] = ''

	df = df.drop_duplicates()
	assert len(df) == len(set(df["wiki_id"])), 'Data contains conflicting information'
	df.to_csv('corpus/individual.csv', index=False)

# Entry level
def observation():
	"Observation level data"
	with open('corpus/party_mapping.json', 'r') as f:
		party_map = json.load(f)
	with open(os.path.join(path_queries, 'observation.rq'), 'r') as f:
		q = f.read()
	df = query2df(q)
	#df.to_csv('test.csv', index=False)
	#df = pd.read_csv('test.csv')
	df = clean_columns(df)
	df = df.replace({'chamber':{'ledamot av Sveriges riksdag':'Enkammarriksdagen',\
	'förstakammarledamot':'Första kammaren', 'andrakammarledamot':'Andra kammaren'}})
	clean_dates(df, ['start', 'end'])
	df["party_abbrev"] = [party_map.get(party, '') for party in df["party"]]
	df.loc[df["district"].str.contains('http'), "district"] = ''

	# Find ids of missing dates and remove the observations
	missing_start_ids, missing_end_ids = check_dates(df)

	# Check for missing values after cleaning
	variables = [var for var in df.columns if var not in ['wiki_id', 'url', 'party']]
	for var in variables:
		missing = round(len(df.loc[df[var] == '']) / len(df), 3)
		if missing > 0.05:
			print(f'{missing}\t missing in {var}')

	df.to_csv('corpus/observation.csv', index=False)

def twitter():
	"Creates few-many mapped dictionary of wiki_id-twitter(s)"
	with open(os.path.join(path_queries, 'twitter.rq'), 'r') as f:
		q = f.read()
	df = query2df(q)
	df = clean_columns(df)
	df = df.drop_duplicates()

	d = {}
	for _, key, value in df[["wiki_id", "twitter"]].itertuples():
		if key not in d:
			d[key] = [value]
		else:
			d[key].append(value)

	with open('corpus/twitter.json', 'w') as f:
		json.dump(d, f, ensure_ascii=False, indent=4)

def minister():
	'''
	Creates nested json of structure: cabinet > individual > role > [start, end].
	Individual level data like born is currently moved to the individual file as some ministers
	have not been members of any chamber. Not sure if this is the best solution.
	TODO: - Missing party information.
	'''
	with open(os.path.join(path_queries, 'minister.rq'), 'r') as f:
		q = f.read()
	ministers = query2df(q)
	#ministers.to_csv('test.csv', index=False)
	#ministers = pd.read_csv('test.csv')
	ministers = clean_columns(ministers)
	clean_dates(ministers, ['start', 'end', 'born', 'dead'])

	# Move individual level data to individual level file
	individual = pd.read_csv('corpus/individual.csv')
	x = ministers[individual.columns].drop_duplicates()
	assert check_unique(x) == {}, "Conflicting data for ministers on individual level"
	if idx := list(set(x["wiki_id"]) - set(individual["wiki_id"])):
		for i in idx:
			individual = individual.append(x.loc[x["wiki_id"] == i])
		individual.to_csv('corpus/individual.csv', index=False)
	dropcols = [var for var in individual.columns if var not in ['wiki_id', 'url', 'name']]
	ministers = ministers.drop(dropcols, axis=1)

	c = {}
	governments = set(ministers["government"])
	for gov in governments:
		cabinet = ministers.loc[ministers["government"] == gov]
		idx = set(cabinet["wiki_id"])
		b = {}
		for i in idx:
			person = cabinet.loc[cabinet["wiki_id"] == i]
			a = {}
			for _, obs in person.iterrows():
				role, start, end = list(obs[["role", "start", "end"]])
				a.update({role:(start, end)})
			b.update({i:roles})
		c.update({gov:cab})

	with open('corpus/ministers.json', 'w') as f:
		json.dump(d, f, ensure_ascii=False, indent=4)

def government():
	"Government date mapping"
	with open(os.path.join(path_queries, 'government.rq'), 'r') as f:
			q = f.read()
	governments = query2df(q)
	governments.rename(columns={'government.value':'wiki_id.value'}, inplace=True)
	governments = clean_columns(governments)
	clean_dates(governments, ['start', 'end'])
	governments.to_csv('corpus/government.csv', index=False)

def party():
	"Query is broken in a very scary way"
	with open(os.path.join(path_queries, 'party.rq'), 'r') as f:
		q = f.read()
	party = query2df(q)
#	party.to_csv('test.csv', index=False)
#	party = pd.read_csv('test.csv')
	party = clean_columns(party)
	clean_dates(party, ['start', 'end'])

	# Problem, connection between start and party missing and mixed up
	p = party.loc[(party["start"] == '') & (party["end"] == '')]
	print(check_unique(p))
	x = party.loc[party["wiki_id"] == 'Q1040479'] # Example
	print(x)

def name():
	with open(os.path.join(path_queries, 'name.rq'), 'r') as f:
		q = f.read()
	names = query2df(q)
	#names.to_csv('test.csv', index=False)
	#names = pd.read_csv('test.csv')
	names = clean_columns(names)

	d = {}
	idx = set(names["wiki_id"])
	for i in idx:
		x = names.loc[names["wiki_id"] == i]
		n = set(x["name_in_riksdagen"].tolist() + x["name"].tolist()) # drop duplicates
		d[i] = [ni for ni in n if ' i ' in ni.lower()] # removes non specifier names

	with open('corpus/names.json', 'w') as f:
		json.dump(d, f, ensure_ascii=False, indent=4)

sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
path_queries = 'input/queries'

#individual()
#observation()
#twitter()
#minister()
#government()
party() # broken
#name()
### Party WIP

