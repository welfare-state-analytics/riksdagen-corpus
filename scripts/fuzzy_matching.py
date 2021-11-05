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

def in_name(name, mp_db):
	matched_mps = mp_db[mp_db["name"].str.contains(name)]
	return matched_mps

def subnames_in_mpname(name, mp_db):
	if len(subnames := name.split()) <= 1: return []
	matched_mps = [mp_db.loc[i] for i,row in mp_db.iterrows() if all([n in row["name"] for n in subnames])]
	return matched_mps

# mop_subnames in person_name
def mpsubnames_in_name(name, mp_db):
	matched_mps = [mp_db.loc[i] for i,row in mp_db.iterrows() \
	if all([n in name.split() for n in row["name"].split()])]
	return matched_mps

def firstname_lastname(name, mp_db):
	if len(subnames := name.split()) <= 1: return []
	matched_mps = [mp_db.loc[i] for i,row in mp_db.iterrows() \
	if subnames[0] == row["name"].split()[0] and subnames[-1] == row["name"].split()[-1]]
	return matched_mps

def two_lastnames(name, mp_db):
	if len(subnames := name.split()) <= 1: return []
	matched_mps = [mp_db.loc[i] for i,row in mp_db.iterrows() \
	if name.split()[-1] == row["name"].split()[-1] and name.split()[-2] == row["name"].split()[-2]]
	return matched_mps

# Broken
def fuzzy_name(name, mp_db):
	matched_mps = [mp_db.loc[i] for i,row in mp_db.iterrows() \
	if textdistance.levenshtein.distance(row["name"],name)]
	return matched_mps

def match_mp(person, mp_db, variables, matching_funs):
	"""
	Pseudocode:
	- inputs:
		- person with cleaned name and party_abbrev
		- mp_db with cleaned name and filtered by chamber for efficiency
		- variables list of lists with variable combinations to match by
		- matching_funs list of functions to match/filter names by
	- check if it is a talman/minister and use other matching function if true
	- filter mp_db by gender if persons gender is available
	- use matching_funs in combination with variables until a unique match is found
	- if there at any step is a match, return the persons mp_db id

	"""
	if 'talman' in person["other"].lower():
		return (['talman_id', 'talman', person, 'talman']) # for debugging

	elif 'statsråd' in person["other"].lower() or 'minister' in person["other"].lower():
		return (['minister_id', 'minister', person, 'minister']) # for debugging)

	if person["gender"] != '': # filter by gender if available
		mp_db = mp_db[mp_db["gender"] == person["gender"]]
	
	for fun in matching_funs:
		matched_mps = fun(person["name"], mp_db)
		if len(matched_mps) == 0:
			continue # restart if no match was found
		if len(matched_mps) == 1: 
			return ([pd.DataFrame(matched_mps).iloc[0]["id"], 'name', person, str(fun)])

		# Iterates over combinations of variables to find a unique match
		for v in variables:
			matched_mps = mp_db.iloc[np.where(mp_db[v] == person[v])[0]]
			if len(matched_mps) >= 2:
				if len(matched_mps.drop_duplicates(variables[-1])) == 1: 
					return ([matched_mps.iloc[0]["id"], f'{v} DUPL', person, str(fun)])
			if len(matched_mps) == 1:
				return ([matched_mps.iloc[0]["id"], f'{v}', person, str(fun)])

	return (['unknown', 'missing/multiple', person, 'missing/multiple'])

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

# Shuffle protocols for debugging
protocols = sorted(list(set(data["protocol"])))
random.seed(15)
random.shuffle(protocols)

results = []
reasons = {}
functions = {}

matching_funs = [in_name, subnames_in_mpname, mpsubnames_in_name,
				 firstname_lastname, two_lastnames, fuzzy_name]

protocols = protocols[:50]

for protocol in progressbar(protocols):
	df = data[data["protocol"] == protocol]
	year, chamber = df.iloc[0][["year", "chamber"]] # Weird hacky syntax
	mp_db = mop[(mop["start"] <= year) & (mop["end"] >= year)]
	
	if year < 1971:
		mp_db_split = mp_db[mp_db["chamber"] == chamber]
	else:
		mp_db_split = mp_db

	for i,row in df.iterrows():
		match, reason, person, fun = match_mp(row, mp_db_split, variables, matching_funs)

		# if no match in bichameral era, check other chamber
		if match == 'unknown' and year < 1971:
			mp_db_rest = mp_db[mp_db["chamber"] != chamber]
			match, reason, person, fun = match_mp(row, mp_db_rest, variables, matching_funs)
		results.append(match)
		reasons[reason] = reasons.get(reason, 0) + 1
		functions[fun] = functions.get(fun, 0) + 1
		# Debugging output
		#print(f'intro: {df.loc[i, "intro"]}')
		#print(f'id: {match}, reason: {reason}')
		#print(f'name: {person["name"]}, gender: {person["gender"]}, party: {person["party"]} specifier: {person["specifier"]}, other: {person["other"]}')
		#print(f'protocol: {protocol}')
		#print('                      ')

results = np.array(results)
print('____________________________________')
print(f'Acc upper bound: {1.0 - sum(results == "unknown") / len(results)}')
print('____________________________________')
for reason in reasons:
	print(f'Reason "{reason}": {reasons[reason] / len(results)}')
print('____________________________________')
for fun in functions:
	print(f'Function "{fun}": {functions[fun] / len(results)}')

