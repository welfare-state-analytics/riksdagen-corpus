import numpy as np
import pandas as pd
import re
import textdistance
from unidecode import unidecode
from nltk.metrics.distance import edit_distance

def multiple_replace(text, i_start=192, i_end=383):
	d = [chr(c) for c in range(i_start, i_end+1)]
	d = {c:unidecode(c) for c in d if c not in 'åäöÅÄÖ'}
	regex = re.compile("(%s)" % "|".join(map(re.escape, d.keys())))
	return regex.sub(lambda mo: d[mo.string[mo.start():mo.end()]], text) 

def clean_names(names):
	if type(names) == str:
		names = names.replace(',','') # Allard, Henry --> Allard Henry
		names = names.replace('.','') # A.C. Lindblad --> AC Lindblad
		names = names.replace('-',' ') # Carl-Eric Lindblad --> Carl Eric Lindblad
		names = names.lower()
	else:
		names = names.str.replace(',','', regex=False) # Allard, Henry --> Allard Henry
		names = names.str.replace('.','', regex=False) # A.C. Lindblad --> AC Lindblad
		names = names.str.replace('-',' ', regex=False) # Carl-Eric Lindblad --> Carl Eric Lindblad
		names = names.str.lower()
	return names

def name_equals(name, db):
	matches = db[db["name"] == name]
	return matches

def name_almost_equals(name, db):
	def _rough_equality(s1, s2):
		perfect_matches = 0
		s1, s2 = s1.replace(".", ""), s2.replace(".", "")
		l1 = s1.split()
		l2 = s2.split()
		if len(l1) != len(l2):
			return False
		for w1, w2 in zip(l1, l2):
			shorter_len = min(len(w1), len(w2))
			w1, w2 = w1.lower(), w2.lower()
			if w1 == w2:
				perfect_matches += 1
			if edit_distance(w1, w2) <= 1:
				if w1[0] == w2[0]:
					perfect_matches += 1
			elif w1[:shorter_len] != w2[:shorter_len]:
				return False
		return perfect_matches >= 1

	matches = db[db["name"].apply(lambda x: _rough_equality(name, x))]
	return matches

def names_in(name, db):
	names = name.split()
	matches = db[db["name"].apply(lambda x:
		len([n for n in names if n in x.split()]) == len(names))]
	return matches

def names_in_rev(name, db):
	names = name.split()
	matches = db[db["name"].apply(lambda x:
		len([n for n in x.split() if n in names]) == len(x.split()))]
	return matches

def fuzzy_name(name, db):
	d = textdistance.levenshtein
	matches = db[db["name"].apply(lambda x: d(name, x) == 1)]
	return matches

### Depreceated functions below
# NEW functions to replace both in_name, subnames_in_mpname, and mpsubnames_in_name
def subnames_in_mpname(name, db):
	if debug:
		print(name, len(name))
	indices = [i for i,row in db.iterrows() if
			   all(any(n == subname for n in row["name"].split())
			   for subname in name.split())]
	return db.loc[indices]

def mpsubnames_in_name(name, db):
	if debug:
		print(name, len(name))
	indices = [i for i,row in db.iterrows() if
			   all(any(n == subname for n in name.split())
			   for subname in row["name"].split())]
	return db.loc[indices]

def firstname_lastname(name, db):
	if debug:
		print(name, len(name))
	if len(subnames := name.split()) <= 1: return []
	indices = [i for i,row in db.iterrows() \
	if subnames[0] == row["name"].split()[0] and subnames[-1] == row["name"].split()[-1]]
	return db.loc[indices]

def firstname_lastname_reversed(name, db):
	if debug:
		print(name, len(name))
	if len(subnames := name.split()) <= 1: return []
	indices = [i for i,row in db.iterrows() \
	if subnames[0] == row["name"].split()[-1] and subnames[-1] == row["name"].split()[0]]
	return db.loc[indices]

def two_lastnames(name, db):
	if debug:
		print(name, len(name))
	if len(subnames := name.split()) <= 1: return []
	indices = [i for i,row in db.iterrows() \
	if name.split()[-1] == row["name"].split()[-1] and name.split()[-2] == row["name"].split()[1:]]
	return db.loc[indices]

def lastname(name, db):
	if debug:
		print(name, len(name))
	return db[db["name"].str.split().str[-1] == name]

def match_mp(person, db, variables, matching_funs):
	"""
	Pseudocode:
	- inputs:
		- person with cleaned name and party_abbrev
		- db with cleaned name and filtered by chamber for efficiency
		- variables list of lists with variable combinations to match by
		- matching_funs list of functions to match/filter names by
	- check if it is a talman/minister and use other matching function if true
	- filter db by gender if persons gender is available
	- use matching_funs in combination with variables until a unique match is found
	- if there at any step is a match, return the persons db id

	"""
	p = person.copy() # avoids spooky behaviour
	p["name"] = clean_names(p.get("name", ""))
	for key in ["name", "party_abbrev", "specifier"]:
		if key not in p:
			p[key] = ""
	for key in p:
		p[key] = [p[key]]
	p = pd.DataFrame.from_dict(p)
	p = p.astype(str)
	p = p.iloc[0]

	# statskalender file currently lacks gender
	if 'gender' in p:
		db = db[db["gender"] == p["gender"]]

	for fun in matching_funs:
		matched_mps = fun(p["name"], db)
		
		if len(matched_mps) == 0:
			if fun == matching_funs[-1]:
				return
			continue # restart if no match was found
		
		if len(set(matched_mps["id"])) == 1:
			return matched_mps["id"].iloc[0]

		# Iterates over combinations of variables to find a unique match
		for v in variables:
			
			matched_mps_new = matched_mps.iloc[np.where(matched_mps[v] == p[v])[0]]

			if len(set(matched_mps_new["id"])) == 1:
				return matched_mps_new["id"].iloc[0]
			
