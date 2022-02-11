'''
Matches corpus metadata to riksdagen open data.
'''

import numpy as np
import pandas as pd
from progressbar import progressbar
from pyriksdagen.match_mp import (
	clean_names, name_equals, names_in, names_in_rev, fuzzy_name
	)


def format_and_filter(db, rd):
	db["name"] = db["name"].apply(clean_names)
	db["born"] = db["born"].str[:4].astype(float)
	db["riksdagen_id"] = pd.Series(str)
	db["end"] = db["end"].str.replace('-01-01', '-12-31')
	db["start"] = pd.to_datetime(db["start"])
	db["end"] = pd.to_datetime(db["end"])
	db = db[db["start"] >= min(rd["From"])]
	return db


def match_mp(person, database, variables, matching_funs):
	start_date, end_date = person[["From", "Tom"]]
	d = {'start':start_date, 'end':end_date}
	for key, value in d.items():
		if key == 'start':
			db = database[database["start"] >= end_date]
		elif key == 'end':
			db = database[database["end"] <= start_date]
		if len(db) == 0:
			continue

		# Filter db
		db = db[db["gender"] == person["Kön"]]
		db = db[db["born"] == person["Född"]] # add leeway?

		# Match by name
		for fun in matching_funs:
			matched_mps = fun(person["name"], db)
			if not matched_mps.empty:
				if len(set(matched_mps["wiki_id"])) == 1:
					return (matched_mps["wiki_id"].iloc[0], person["Id"])
	
	return (None, person["Id"])

def main():
	# Riksdagen
	riksdagen = pd.read_csv('input/riksdagen-open-data/person.csv')
	variables = ["Förnamn", "Efternamn", "Id", "Kön", "Född", "From", "Tom", "Uppdragsroll"]
	rd = riksdagen[variables].drop_duplicates().reset_index(drop=True)

	# Format columns
	roles = set(rd["Uppdragsroll"])
	speaker_roles = {r:'speaker' for r in roles if 'talman' in r}
	minister_roles = {r:'minister' for r in roles if 'minister' in r or 'statsråd' in r}
	mp_roles = {r:'member' for r in roles if r not in speaker_roles and r not in minister_roles}
	d = {}
	for roles in [speaker_roles, minister_roles, mp_roles]:
		d.update(roles)

	rd["role"] = rd["Uppdragsroll"].map(d)
	rd["name"] = clean_names(rd["Förnamn"] + ' ' + rd["Efternamn"])
	rd["Född"] = rd["Född"].astype(float)
	rd["From"] = pd.to_datetime(rd["From"])
	rd["Tom"] = pd.to_datetime(rd["Tom"])

	# Dbs
	mp_db = pd.read_csv('input/matching/member.csv')
	minister_db = pd.read_csv('input/matching/minister.csv')
	speaker_db = pd.read_csv('input/matching/speaker.csv')

	# Impute end dates for members currently in office
	# Not sure if needed
	idx = mp_db["end"].isna()
	idy = mp_db["start"].str[:4] >= '2014'
	idx = [i for i in idx if i in idy]
	mp_db.loc[idx, "end"] = '2022-12-31'

	# Spooky stuff
	mp_db.loc[mp_db["end"].str.contains('http'), "end"] = np.nan

	# Format variables
	mp_db = format_and_filter(mp_db, rd)
	minister_db = format_and_filter(minister_db, rd)
	speaker_db = format_and_filter(speaker_db, rd)

	matching_funs = [name_equals, names_in, names_in_rev, fuzzy_name]
	results = []
	for i in progressbar(range(len(rd))):
		person = rd.loc[i]

		if person["role"] == 'member':
			corpus_id, rd_id = match_mp(person, mp_db, variables, matching_funs)
			
		elif person["role"] == 'minister':
			corpus_id, rd_id = match_mp(person, minister_db, variables, matching_funs)
			
		elif person["role"] == 'speaker':
			corpus_id, rd_id = match_mp(person, speaker_db, variables, matching_funs)
			
		results.append([corpus_id, rd_id])
	df = pd.DataFrame(results, columns=['id', 'riksdagen_id'])
	df = df.drop_duplicates().dropna()

	for i in set(df["id"]):
		mappings = set(df.loc[df["id"] == i, "riksdagen_id"])
		if len(mappings) > 1:
			print(f'corpus member {i} mapped to multiple riksdagen members {mappings}')

	for i in set(df["riksdagen_id"]):
		mappings = set(df.loc[df["riksdagen_id"] == i, "id"])
		if len(mappings) > 1:
			print(f'riksdagen member {i} mapped to multiple corpus members {mappings}')

	print('\n')
	print('Proportion of riksdagen individuals connected:')
	print(round(len(set(df["riksdagen_id"])) / len(set(riksdagen["Id"])), 2))

main()
