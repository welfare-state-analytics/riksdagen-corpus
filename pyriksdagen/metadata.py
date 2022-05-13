### DEBUGGING
# 1. Checkout member/minister/speaker to see if its a data or algorithm


from SPARQLWrapper import SPARQLWrapper, JSON
import numpy as np
import pandas as pd
import os, argparse
import time
import re
from importlib_resources import files
from unidecode import unidecode
from pyriksdagen.match_mp import multiple_replace
from functools import partial
import datetime

def increase_date_precision(date, start=True):
	if pd.isna(date):
		return date
	# Year
	if len(date) == 4 and start:
		return date + '-01-01'
	if len(date) == 4 and not start:
		return date + '-12-31'
	# Month
	if len(date) == 7 and start:
		return date + '-01'
	if len(date) == 7 and start:
		last_day = calendar.monthrange(int(date[0]), int(date[1]))[1]
		return date + f'-{last_day}'
	# Day
	if len(date) == 10:
		return date

def check_date_overlap(start1, end1, start2, end2):
	latest_start = max(start1, start2)
	earliest_end = min(end1, end2)
	delta = (earliest_end - latest_start).days + 1
	overlap = max(0, delta)
	if overlap > 0:
		return True
	else:
		return False

def impute_member_date(db, gov_db, from_gov='Regeringen Löfven I'):
	gov_start = gov_db.loc[gov_db['government'] == from_gov, 'start'].iloc[0]
	idx = 	(db['source'] == 'member_of_parliament') &\
			(db['start'] > gov_start) &\
			(db['end'].isna())
	db.loc[idx, 'end'] = gov_db['end'].max()
	return db

def impute_minister_date(db, gov_db):
	def _impute_minister_date(minister, gov_db):
		if pd.isna(minister['start']):
			minister['start'] = gov_db.loc[gov_db['government'] == minister['government'], 'start'].iloc[0]
		if pd.isna(minister['end']):
			minister['end'] = gov_db.loc[gov_db['government'] == minister['government'], 'end'].iloc[0]
		return minister

	# Impute missing minister dates using government dates
	db.loc[db['source'] == 'minister'] =\
	db.loc[db['source'] == 'minister'].apply(partial(_impute_minister_date, gov_db=gov_db), axis=1)
	return db

def impute_speaker_date(db):
	idx = 	(db['source'] == 'speaker') &\
			(db['end'].isna()) &\
			(db['role'].str.contains('kammare') == False)
	db.loc[idx, 'end'] = db.loc[idx, 'start'] + datetime.timedelta(days = 365*4)
	return db

def impute_date(db):
	db[["start", "end"]] = db[["start", "end"]].astype(str)
	db['start'] = db['start'].apply(increase_date_precision, start=True)
	db['end'] = db['end'].apply(increase_date_precision, start=False)
	db[["start", "end"]] = db[["start", "end"]].apply(pd.to_datetime, format='%Y-%m-%d')
	
	if 'source' not in db.columns:
		return db

	# Impute current governments end date
	gov_db = pd.read_csv('corpus/metadata/government.csv')
	gov_db[["start", "end"]] = gov_db[["start", "end"]].apply(pd.to_datetime, format='%Y-%m-%d')
	idx = gov_db['start'].idxmax()
	gov_db.loc[idx, 'end'] = gov_db.loc[idx, 'start'] + datetime.timedelta(days = 365*4)

	sources = set(db['source'])
	if 'member_of_parliament' in sources:
		db = impute_member_date(db, gov_db)
	if 'minister' in sources:
		db = impute_minister_date(db, gov_db)
	if 'speaker' in sources:
		db = impute_speaker_date(db)
	return db

def impute_party(db, party):
	if 'party' not in db.columns:
		db['party'] = pd.Series(dtype=str)
	data = []
	for i, row in db[db['party'].isnull()].iterrows():	
		parties = party[party['wiki_id'] == row['wiki_id']]
		if len(set(parties['party'])) == 1:
			db.loc[i,'party'] = parties['party'].iloc[0]
		if len(set(parties['party'])) >= 2:
			for j, sow in parties.iterrows():
				try:
					res = check_date_overlap(row['start'], sow['start'], row['end'], sow['end'])
				except:
					print("Impute dates on Corpus using impute_date() before imputing parties!\n")
					raise
				if res:
					m = row.copy()
					m['party'] = sow['party']
					data.append(m)
	db = pd.concat([db, pd.DataFrame(data)]).reset_index(drop=True)
	return db

def abbreviate_party(db, party):
	party = {row['party']:row['abbreviation'] for _, row in party.iterrows()}
	db["party_abbrev"] = db["party"].fillna('').map(party)
	return db

def clean_name(db):
	latin_characters = [chr(c) for c in range(192,383+1)]
	latin_characters = {c:unidecode(c) for c in latin_characters if c not in 'åäöÅÄÖ'}
	replace_fun = partial(multiple_replace, latin_characters)
	db['name'] = db['name'].str.lower()
	db['name'] = db['name'].astype(str).apply(replace_fun)
	db['name'] = db['name'].str.replace('-', ' ', regex=False)
	db['name'] = db['name'].str.replace(r'[^a-zåäö\s\-]', '', regex=True)
	return db

class Corpus(pd.DataFrame):
	def __init__(self, *args, **kwargs):
		super(Corpus, self).__init__(*args, **kwargs)

	@property
	def _constructor(self):
		return Corpus

	def _load_metadata(self, file, source=False):
		df = pd.read_csv(f"corpus/metadata/{file}.csv")
		if source:
			df['source'] = file
		return df

	def add_mps(self):
		df = self._load_metadata('member_of_parliament', source=True)
		return Corpus(pd.concat([self, df]))
	        
	def add_ministers(self):
		df = self._load_metadata('minister', source=True)
		return Corpus(pd.concat([self, df]))

	def add_speakers(self):
		df = self._load_metadata('speaker', source=True)
		return Corpus(pd.concat([self, df]))

	def add_persons(self):
		df = self._load_metadata('person')
		return self.merge(df, on='wiki_id', how='left')

	def add_location_specifiers(self):
		df = self._load_metadata('location_specifier')
		return self.merge(df, on='wiki_id', how='left')

	def add_names(self):
		df = self._load_metadata('name')
		return self.merge(df, on='wiki_id', how='left')
	
	def impute_dates(self):
		return impute_date(self)

	def impute_parties(self):
		df = self._load_metadata('party_affiliation')
		df = impute_date(df)
		return impute_party(self, df)

	def abbreviate_parties(self):
		df = self._load_metadata('party_abbreviation')
		return abbreviate_party(self, df)

	def clean_names(self):
		return clean_name(self)

