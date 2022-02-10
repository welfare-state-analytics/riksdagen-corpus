import numpy as np
import textdistance
import pandas as pd

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

def fuzzy_name(name, db):
	indices = [i for i,row in db.iterrows() \
	if textdistance.levenshtein.distance(row["name"],name)]
	return db.loc[indices]

# NEW functions to replace both in_name, subnames_in_mpname, and mpsubnames_in_name
def subnames_in_mpname(name, db):
	indices = [i for i,row in db.iterrows() if
			   all(any(n == subname for n in row["name"].split())
			   for subname in name.split())]
	return db.loc[indices]

def mpsubnames_in_name(name, db):
	indices = [i for i,row in db.iterrows() if
			   all(any(n == subname for n in name.split())
			   for subname in row["name"].split())]
	return db.loc[indices]

def firstname_lastname(name, db):
	if len(subnames := name.split()) <= 1: return []
	indices = [i for i,row in db.iterrows() \
	if subnames[0] == row["name"].split()[0] and subnames[-1] == row["name"].split()[-1]]
	return db.loc[indices]

def firstname_lastname_reversed(name, db):
	if len(subnames := name.split()) <= 1: return []
	indices = [i for i,row in db.iterrows() \
	if subnames[0] == row["name"].split()[-1] and subnames[-1] == row["name"].split()[0]]
	return db.loc[indices]

def two_lastnames(name, db):
	if len(subnames := name.split()) <= 1: return []
	indices = [i for i,row in db.iterrows() \
	if name.split()[-1] == row["name"].split()[-1] and name.split()[-2] == row["name"].split()[1:]]
	return db.loc[indices]

def lastname(name, db):
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
	person["name"] = clean_names(person.get("name", ""))
	for key in ["name", "party_abbrev", "specifier"]:
		if key not in person:
			person[key] = ""
	for key in person:
		person[key] = [person[key]]
	person = pd.DataFrame.from_dict(person)
	person = person.astype(str)
	person = person.iloc[0]

	# statskalender file currently lacks gender
	if 'gender' in person:
		db = db[db["gender"] == person["gender"]]

	for fun in matching_funs:
		matched_mps = fun(person["name"], db)

		if len(matched_mps) == 0:
			if fun == matching_funs[-1]:
				return
			continue # restart if no match was found
		
		if len(set(matched_mps["id"])) == 1:
			return matched_mps["id"].iloc[0]

		# Iterates over combinations of variables to find a unique match
		for v in variables:
			if 'name' not in v:
				continue
			matched_mps_new = matched_mps.iloc[np.where(matched_mps[v] == person[v])[0]]
			if len(set(matched_mps["id"])) == 1:
				return matched_mps["id"].iloc[0]
