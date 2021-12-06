import numpy as np
import textdistance
import pandas as pd

def clean_names(names):
	if type(names) == str:
		names = names.replace(',','', regex=False) # Allard, Henry --> Allard Henry
		names = names.replace('.','') # A.C. Lindblad --> AC Lindblad
		names = names.replace('-',' ') # Carl-Eric Lindblad --> Carl Eric Lindblad
		names = names.lower()
	else:
		names = names.str.replace(',','', regex=False) # Allard, Henry --> Allard Henry
		names = names.str.replace('.','', regex=False) # A.C. Lindblad --> AC Lindblad
		names = names.str.replace('-',' ', regex=False) # Carl-Eric Lindblad --> Carl Eric Lindblad
		names = names.str.lower()
	return names

def in_name(name, mp_db):
	return mp_db[mp_db["name"].str.contains(name)]

def fuzzy_name(name, mp_db):
	indices = [i for i,row in mp_db.iterrows() \
	if textdistance.levenshtein.distance(row["name"],name)]
	return mp_db.loc[indices]

def subnames_in_mpname(name, mp_db):
	if len(subnames := name.split()) <= 1: return []
	indices = [i for i,row in mp_db.iterrows() if all([n in row["name"] for n in subnames])]
	return mp_db.loc[indices]

def mpsubnames_in_name(name, mp_db):
	indices = [i for i,row in mp_db.iterrows() \
	if all([n in name.split() for n in row["name"].split()])]
	return mp_db.loc[indices]

def firstname_lastname(name, mp_db):
	if len(subnames := name.split()) <= 1: return []
	indices = [i for i,row in mp_db.iterrows() \
	if subnames[0] == row["name"].split()[0] and subnames[-1] == row["name"].split()[-1]]
	return mp_db.loc[indices]

def firstname_lastname_reversed(name, mp_db):
	if len(subnames := name.split()) <= 1: return []
	indices = [i for i,row in mp_db.iterrows() \
	if subnames[0] == row["name"].split()[-1] and subnames[-1] == row["name"].split()[0]]
	return mp_db.loc[indices]

def two_lastnames(name, mp_db):
	if len(subnames := name.split()) <= 1: return []
	indices = [i for i,row in mp_db.iterrows() \
	if name.split()[-1] == row["name"].split()[-1] and name.split()[-2] == row["name"].split()[1:]]
	return mp_db.loc[indices]

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
	senander = False
	if isinstance(person, dict):
		person["name"] = clean_names(person.get("name", ""))
		if "senander" in person["name"]:
			senander = False
		for key in ["other", "gender", "name", "party_abbrev", "specifier"]:
			if key not in person:
				person[key] = ""
		for key in person:
			person[key] = [person[key]]
		person = pd.DataFrame.from_dict(person)

		person = person.astype(str)
		person = person.iloc[0]

	if 'talman' in person["other"].lower():
		return (['talman_id', 'talman', person, 'talman']) # for debugging

	elif 'statsråd' in person["other"].lower() or 'minister' in person["other"].lower():
		return (['minister_id', 'minister', person, 'minister']) # for debugging)

	# statskalender file currently lacks gender
	if person["gender"] != '' and "gender" in list(mp_db.columns): # filter by gender if available
		mp_db = mp_db[mp_db["gender"] == person["gender"]]
	#print(mp_db)
	for fun in matching_funs:
		matched_mps = fun(person["name"], mp_db)
		if senander:
			print(fun)
			print(matched_mps)
		if len(matched_mps) == 0:
			if fun == matching_funs[-1]:
				return (['unknown', 'missing', person, 'missing'])
			continue # restart if no match was found
		if len(matched_mps) == 1: 
			return ([matched_mps.iloc[0]["id"], 'name', person, str(fun)])

		# Iterates over combinations of variables to find a unique match
		for v in variables:
			matched_mps_new = matched_mps.iloc[np.where(matched_mps[v] == person[v])[0]]
			if senander:
				print(matched_mps_new)

			if len(matched_mps_new) >= 2:
				if len(matched_mps_new.drop_duplicates(variables[-1])) == 1: 
					return ([matched_mps_new.iloc[0]["id"], f'{v} DUPL', person, str(fun)])
			if len(matched_mps_new) == 1:
				return ([matched_mps_new.iloc[0]["id"], f'{v}', person, str(fun)])

	return (['unknown', 'multiple', person, 'multiple'])