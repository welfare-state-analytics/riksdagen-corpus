import pandas as pd
import re
from .match_mp import multiple_replace
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
	return True if overlap > 0 else False


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
		parties = party[party['swerik_id'] == row['swerik_id']]
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
	idx = db['name'].notna()
	db.loc[idx, 'name'] = db.loc[idx, 'name'].str.lower()
	db.loc[idx, 'name'] = db.loc[idx, 'name'].astype(str).apply(multiple_replace)
	db.loc[idx, 'name'] = db.loc[idx, 'name'].str.replace('-', ' ', regex=False)
	db.loc[idx, 'name'] = db.loc[idx, 'name'].str.replace(r'[^a-zåäö\s\-]', '', regex=True)
	return db


def infer_chamber(db):
	def _infer_chamber(role):
		d = {'första': 1, 'andra': 2}
		match = re.search(r'([a-zåäö]+)\s*(?:kammar)', role)
		return d[match.group(1)] if match else 0
	db['chamber'] = db['role'].apply(_infer_chamber).astype(dtype=pd.Int8Dtype())
	return db


def format_member_role(db):
	db['role'] = db['role'].str.extract(r'(ledamot)')
	return db


def format_minister_role(db):
	db["role"] = db["role"].str.replace('Sveriges ', '').str.lower()
	return db


def format_speaker_role(db):
	def _format_speaker_role(role):
		match = re.search(r'(andre |förste |tredje )?(vice )?talman', role)
		return match.group(0)
	db['role'] = db['role'].apply(_format_speaker_role)
	return db


class Corpus(pd.DataFrame):
	"""
	Store corpus metadata as a single pandas DataFrame where
	the column 'source' indicates the type of the row
	"""
	def __init__(self, *args, **kwargs):
		super(Corpus, self).__init__(*args, **kwargs)

	@property
	def _constructor(self):
		return Corpus

	def _load_metadata(self, file, source=False):
		df = pd.read_csv(f"corpus/metadata/{file}.csv")

		# Adjust to new structure where party information
		# is not included in member_of_parliament.csv
		if file == "member_of_parliament":
			print(df)
			columns = list(df.columns) + ["party"]
			party_df = pd.read_csv(f"corpus/metadata/party_affiliation.csv")
			party_df = party_df[party_df["start"].notnull()]
			party_df = party_df[party_df["end"].notnull()]
			df = df.merge(party_df, on=["swerik_id", "start", "end"], how="left")
			df = df[columns]
			print(df)
			print(df[df["party"].notnull()])
		if source:
			df['source'] = file
		return df

	def add_mps(self):
		df = self._load_metadata('member_of_parliament', source=True)
		df = infer_chamber(df)
		df = format_member_role(df)
		return Corpus(pd.concat([self, df]))
	        
	def add_ministers(self):
		df = self._load_metadata('minister', source=True)
		df = format_minister_role(df)
		return Corpus(pd.concat([self, df]))

	def add_speakers(self):
		df = self._load_metadata('speaker', source=True)
		df = infer_chamber(df)
		df = format_speaker_role(df)
		return Corpus(pd.concat([self, df]))

	def add_persons(self):
		df = self._load_metadata('person')
		return self.merge(df, on='swerik_id', how='left')

	def add_location_specifiers(self):
		df = self._load_metadata('location_specifier')
		return self.merge(df, on='swerik_id', how='left')

	def add_names(self):
		df = self._load_metadata('name')
		return self.merge(df, on='swerik_id', how='left')
	
	def impute_dates(self):
		return impute_date(self)

	def impute_parties(self):
		df = self._load_metadata('party_affiliation')
		df = impute_date(df)
		return impute_party(self, df)

	def abbreviate_parties(self):
		df = self._load_metadata('party_abbreviation')
		return abbreviate_party(self, df)

	def add_twitter(self):
		df = self._load_metadata('twitter')
		return self.merge(df, on='swerik_id', how='left')

	def clean_names(self):
		return clean_name(self)



def load_Corpus_metadata():
	"""
	Populates Corpus object
	"""
	corpus = Corpus()

	corpus = corpus.add_mps()
	corpus = corpus.add_ministers()
	corpus = corpus.add_speakers()

	corpus = corpus.add_persons()
	corpus = corpus.add_location_specifiers()
	corpus = corpus.add_names()

	corpus = corpus.impute_dates()
	corpus = corpus.impute_parties()
	corpus = corpus.abbreviate_parties()
	corpus = corpus.add_twitter()
	corpus = corpus.clean_names()

	# Clean up speaker role formatting
	corpus["role"] = corpus["role"].replace({
		'Sveriges riksdags talman':'speaker',
		'andra kammarens andre vice talman':'ak_2_vice_speaker',
		'andra kammarens förste vice talman':'ak_1_vice_speaker',
		'andra kammarens talman':'ak_speaker',
		'andra kammarens vice talman':'ak_1_vice_speaker',
		'andre vice talman i första kammaren':'fk_2_vice_speaker',
		'första kammarens talman':'fk_speaker',
		'första kammarens vice talman':'fk_1_vice_speaker',
		'förste vice talman i första kammaren':'fk_1_vice_speaker'
		})

	# Temporary ids
	corpus['person_id'] = corpus['swerik_id']

	# Drop individuals with missing names
	corpus = corpus[corpus['name'].notna()]

	# Remove redundancy and split file
	corpus = corpus.drop_duplicates()
	corpus = corpus.dropna(subset=['name', 'start', 'end'])
	corpus = corpus.sort_values(['swerik_id', 'start', 'end', 'name'])

	return corpus
