"""
New version of matching algorithm with fuzzy matching implemented.

Notes from data exploration:
	- Found name "Fr. Julin", Fr. stands for Fröken?
	- Problems with year filtering:
		1. imputed data causes overlaps
		2. year is taken from first filename, i.e. 196767 --> 1976 causing lots of years being wrong.
			this should not be solved by buffers (until we have matched mop entries on individual level)as it causes overlaps.
			solution atm would be to use 1. docDate, 2. some other date.
			docDate seems unreliable (can be wrong or completely missing) but is probably the best option atm.
			some other date could be to scrape "date" tags together with intros and give intros the latest "date" tag.
			pretty good solution for now is probably to use docDate and substitute it for filename[:4] if it is missing or potentially contains conflicts
	- Observed lots of Unknown for first couple of ~100 protocols, investigate why

"""
import textdistance
import numpy as np
import pandas as pd
import json
import re
from progressbar import progressbar
from itertools import combinations
import random

from pyriksdagen.segmentation import (
    detect_mp_new
)

def clean_names(names):
	names = names.str.replace('.','', regex=False) # A.C. Lindblad --> AC Lindblad
	names = names.str.replace('-',' ', regex=False) # Carl-Eric Lindblad --> Carl Eric Lindblad
	names = names.str.lower()
	return names

def match_mp(person, mp_db, variables, fuzzy):
	"""
	Pseudocode:
	- input person (name cleaned and party_abbrev) and mp_db (name cleaned and chamber filtered)
	- check if it is a talman/minister and use other matching function if true
	- filter mp_db by gender if persons gender is available
	- find matches of persons name in mp_db
	- if no match, perform fuzzy matching of name
	- if 2 matches, check if they are the same person with overlapping year variable
	- if multiple, start matching with combinations of variables
	- if there at any step is a match, return the persons mp_db id
	
	TODO:
	Improve name matching (both input data and how to handle middle names, etc.)

	"""
	if 'talman' in person["other"].lower():
		return (['talman_id', 'talman', person]) # for debugging

	elif 'statsråd' in person["other"].lower() or 'minister' in person["other"].lower():
		return (['minister_id', 'minister', person]) # for debugging)

	if person["gender"] != '': # filter by gender if available
		mp_db = mp_db[mp_db["gender"] == person["gender"]]
	
	# Filter and match by name
	matched_mps = mp_db[mp_db["name"].str.contains(person["name"])]
	if len(matched_mps) == 0: # fuzzy matching
		indices = [i for i,name in enumerate(mp_db["name"]) if fuzzy(name, person["name"]) == 1]
		matched_mps = mp_db.iloc[indices]
	if len(matched_mps) == 0: return (['unknown', 'missing', person])
	if len(matched_mps) == 1: return ([matched_mps.iloc[0]["id"], 'name', person])
	if len(matched_mps) >= 2: mp_db = matched_mps
	if len(matched_mps) == 2 and all(mp_db.iloc[0][variables[-1]] == mp_db.iloc[1][variables[-1]]): 
		return ([mp_db.iloc[0]["id"], 'heuristic', person]) # heuristic
	
	# Iterates over combinations of variables to find a unique match
	for v in variables:
		matched_mps = mp_db.iloc[np.where(mp_db[v] == person[v])[0]]
		if len(matched_mps) == 1:
			return ([matched_mps.iloc[0]["id"], f'{v}', person])

	return (['unknown', 'multiple', person])

# Import mp_db
mop = pd.read_csv('corpus/members_of_parliament.csv')
mop["name"] = clean_names(mop["name"])

# Import patterns
patterns = pd.read_json("input/segmentation/detection.json", orient="records", lines=True)
expressions = []
for _, pattern in patterns.iterrows():
    exp, t = pattern["pattern"], pattern["type"]
    exp = re.compile(exp)
    expressions.append((exp, t))

# Import and clean detected intros
with open('corpus/party_mapping.json') as f:
  party_map = json.load(f)
data = pd.read_csv('output.csv').sort_values(by="protocol").reset_index()
results = list(map(lambda x: detect_mp_new(x, expressions), data["intro"]))
data["other"] = list(map(lambda x: x.get("other", ""), results))
data["gender"] = list(map(lambda x: x.get("gender", ""), results))
data["party"] = list(map(lambda x: x.get("party", ""), results))
data["party_abbrev"] = list(map(lambda x: party_map.get(x, ""), data["party"]))
data["specifier"] = list(map(lambda x: x.get("specifier", ""), results))
data["name"] = list(map(lambda x: x.get("name", ""), results))
data["name"] = clean_names(data["name"])

# Create objects to match by
variables = ['party_abbrev', 'specifier', 'name']
variables = sum([list(map(list, combinations(variables, i))) for i in range(len(variables) + 1)], [])[1:]
fuzzy = textdistance.Levenshtein()

# Shuffle protocols for debugging
protocols = sorted(list(set(data["protocol"])))
random.seed(15)
random.shuffle(protocols)

results = []

protocols = protocols[:100]

for protocol in progressbar(protocols):
	df = data[data["protocol"] == protocol]
	year, chamber = df.iloc[0][["year", "chamber"]] # Weird hacky syntax
	mp_db = mop[(mop["start"] <= year) & (mop["end"] >= year)]
	
	if year < 1971:
		mp_db_split = mp_db[mp_db["chamber"] == chamber]
	else:
		mp_db_split = mp_db

	for i,row in df.iterrows():
		match, reason, person = match_mp(row, mp_db_split, variables, fuzzy)

		# if no match in bichameral era, check other chamber
		if match == 'unknown' and year < 1971:
			mp_db_split = mp_db[mp_db["chamber"] != chamber]
			match, reason, person = match_mp(row, mp_db_split, variables, fuzzy)
		results.append(match)

		# Debugging output
		print(f'intro: {df.loc[i, "intro"]}')
		print(f'id: {match}, reason: {reason}')
		print(f'name: {person["name"]}, gender: {person["gender"]}, party: {person["party"]} specifier: {person["specifier"]}, other: {person["other"]}')
		print(f'protocol: {protocol}')
		print('                      ')

results = np.array(results)
print('________________________________')
print(f'Acc upper bound: {1.0 - sum(results == "unknown") / len(results)}')

