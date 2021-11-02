"""
New version of matching algorithm with fuzzy matching implemented:
TODO:
	- Add handling of names better (middle names optional, etc.)
	- Switch from filtering with chamber to matching with it (in case speaker is in "wrong" chamber)
	- Implement talman and minister matching
	- Factor code into functions
	- Protocols often have very few intros detected, look into potential bug (may be correct)

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

from pyriksdagen.segmentation import (
    detect_mp_new
)

def clean_names(names):
	names = names.str.replace('.','', regex=False) # A.C. Lindblad --> AC Lindblad
	names = names.str.replace('-',' ', regex=False) # Carl-Eric Lindblad --> Carl Eric Lindblad
	names = names.str.lower()
	return names

def match_intro(row, mop, fuzzy, matches):
	"""
	Matches and returns id for a single individual.
	Args: row = single individual from dataframe with columns for detected values.
				missing values are '' and name should be cleaned.
		  mop = members of parliament filtered by year and chamber.
		  fuzzy = distance object from textdistance package.
		  matches = object for summarizing results
	"""
	name, gender, party_abbrev, specifier, other = row[["name","gender","party_abbrev","specifier","other"]]

	# Matching algoritm:
	if 'talman' in other.lower():
		matches["talman"] += 1
		return 'talman_id' # for debugging

	elif 'statsråd' in other.lower() or 'minister' in other.lower():
		matches["minister"] += 1
		return 'minister_id'  # for debugging
		
	else:

		# filter by gender
		if gender != '':
			mop = mop[mop["gender"] == gender]

		# match by name
		idx = [j for j,m in mop.iterrows() if name in m["name"]]

		# if unique match, return mop id
		if len(idx) == 1:
			matches["name"] += 1
			return mop.loc[idx,"id"]

		# if no matches, perform fuzzy and proceed from there
		if len(idx) == 0:
			idx = [i for i,m in mop.iterrows() if fuzzy(name, m["name"]) == 1]
			
			# if unique match, return mop id
			if len(mop) == 1:
				matches["fuzzy"] += 1
				return mop.loc[idx,"id"]

			# if still no match, return unknown
			elif len(mop) == 0:
				matches["no_match"] += 1
				return 'unknown'

		# if multiple potential matches, filter by more variables
		if len(idx) > 1:
			mop = mop.loc[idx]

			# match by specifier
			mop_id = mop.loc[mop["specifier"] == specifier, "id"]
			if len(mop_id) == 1:
				matches["party_specifier"] += 1
				return mop_id

			# match by party
			mop_id = mop.loc[mop["party_abbrev"] == party_abbrev, "id"]
			if len(mop_id) == 1:
				matches["party"] += 1
				return mop_id

			# match by party + specifier
			mop_id = mop.loc[(mop["specifier"] == specifier) & (mop["party_abbrev"] == party_abbrev), "id"]
			if len(mop_id) == 1:
				matches["specifier"] += 1
				return mop_id
		
		# If 2 entries for same individual overlap in mop
		if len(mop) == 2:
			mop.iloc[0,["name","gender","party_abbrev","specifier"]] ==\
			mop.iloc[1,["name","gender","party_abbrev","specifier"]]
			return mop.iloc[0,"id"]

		# Still multiple candidate matches left
		matches["indistinguishable"] += 1
		return 'unknown'
		
fuzzy = textdistance.Levenshtein(external=False) 

# Output object for summarizing results
matches = pd.DataFrame(np.zeros((1,9)), dtype = int)
matches.columns = ["name", "fuzzy", "no_match", "indistinguishable", "party_specifier", "party", "specifier", "talman", "minister"]

# Import patterns
patterns = pd.read_json("input/segmentation/detection.json", orient="records", lines=True)
expressions = []

for _, pattern in patterns.iterrows():
    exp, t = pattern["pattern"], pattern["type"]
    exp = re.compile(exp)
    expressions.append((exp, t))

# Import data
members_of_parliament = pd.read_csv('corpus/members_of_parliament.csv')
members_of_parliament["name"] = clean_names(members_of_parliament["name"])

with open('corpus/party_mapping.json') as f:
  party_map = json.load(f)

# Sort by protocol id, not sure where we want the final outputs,
# but at least iterate over protocols to filter mop more efficiently.
# could sort by year,chamber,protocol to filter more efficiently
intros = pd.read_csv('output.csv').sort_values(by="protocol").reset_index()
protocols = sorted(list(set(intros["protocol"])))

# For testing
import random
random.shuffle(protocols)

p = 0
for protocol in progressbar(protocols):
	df = intros[intros["protocol"] == protocol][:]
	
	year, chamber = df.iloc[0][["year", "chamber"]] # Weird hacky syntax
	
	# Filter mop on protocol level
	mop = members_of_parliament.query(f'{year} >= start and {year} <= end') # skips buffer to avoid overlaps
	mop = mop[mop["chamber"] == chamber]

	results = list(map(lambda x: detect_mp_new(x, expressions), df["intro"]))
	df["other"] = list(map(lambda x: x.get("other", ""), results))
	df["gender"] = list(map(lambda x: x.get("gender", ""), results))
	df["party"] = list(map(lambda x: x.get("party", ""), results))
	df["party_abbrev"] = list(map(lambda x: party_map.get(x, ""), df["party"]))
	df["specifier"] = list(map(lambda x: x.get("specifier", ""), results))
	df["name"] = list(map(lambda x: x.get("name", ""), results))
	df["name"] = clean_names(df["name"])

	for i,row in df.iterrows():		
		x = match_intro(row, mop, fuzzy, matches)
	
	p += 1
	if p % 500 == 0:
		print(matches)

matches.to_csv('matches.csv', index=False)
