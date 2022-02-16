'''
Script for processing raw wikidata tables.
'''
import numpy as np
import pandas as pd
import os, json
from pyriksdagen.mp import add_id
from pyriksdagen.match_mp import clean_names
import unicodedata
from datetime import datetime

government = pd.read_csv('corpus/metadata/government.csv')
person = pd.read_csv('corpus/metadata/person.csv')
location_specifier = pd.read_csv('corpus/metadata/location_specifier.csv')
member = pd.read_csv('corpus/metadata/member_of_parliament.csv')
minister = pd.read_csv('corpus/metadata/minister.csv')
name = pd.read_csv('corpus/metadata/name.csv')
party = pd.read_csv('corpus/metadata/party_affiliation.csv')
speaker = pd.read_csv('corpus/metadata/speaker.csv')
party_map = pd.read_csv('corpus/metadata/party_abbreviation.csv')

### Process corpus data
# Drop parties never present in riksdagen
party_map = {row["party"]:row["abbreviation"] for _, row in party_map.iterrows()}
party["party_abbrev"] = party["party"].map(party_map)
party = party.dropna().reset_index(drop=True)

# Name
name["name"] = name["name"].str.replace('"','')
name["name"] = name["name"].apply(clean_names)
name = name.loc[name["name"] != ''].reset_index(drop=True)

# Map gender to english
person["gender"] = person["gender"].map({'kvinna':'woman', 'man':'man'})

### Create dbs for matching
# Minister
government[["start", "end"]] = government[["start", "end"]].apply(pd.to_datetime, errors="coerce")
government.loc[government["start"] == max(government["start"]), "end"] = datetime.strptime('2022-12-31', '%Y-%m-%d')
government = government.rename(columns={'start':'gov_start', 'end':'gov_end'})

# Ministers
minister = minister.merge(person, on='wiki_id', how='left')
minister = minister.merge(location_specifier, on='wiki_id', how='left')
minister = minister.merge(name, on='wiki_id', how='left')
minister = minister.merge(government, on='government', how='left')
minister["role"] = minister["role"].str.replace('Sveriges ', '')

# Impute end dates for ministers currently in office
idx = np.where(minister["gov_start"] == max(minister["gov_start"]))[0]
idy = minister["end"].isna()
idx = [i for i in idx if i in idy]
minister.loc[idx, "end"] = '2022-12-31'

# No idea why but name is missing here, debug later
minister.loc[minister["wiki_id"] == 'Q60971016'] = 'Gerhard Larsson'

# Speakers
speaker = speaker.merge(person, on='wiki_id', how='left')
speaker = speaker.merge(location_specifier, on='wiki_id', how='left')
speaker = speaker.merge(name, on='wiki_id', how='left')
speaker["role"] = speaker["role"].map({
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

# Members
member = member.merge(person, on='wiki_id', how='left')
member = member.merge(location_specifier, on='wiki_id', how='left')
member = member.merge(name, on='wiki_id', how='left')

# Clean values
member["role"] = member["role"].str.extract(r'([A-Za-zÀ-ÿ]*ledamot)')

# Impute missing party values for members (not used for others atm)
idx = member["party"].isnull()
missing = member.loc[idx]
missing = missing.merge(party, on='wiki_id', how='left')
member.loc[idx, "party"] = missing["party_y"]

# Impute end dates for members currently in office
idx = member["end"].isna()
idy = member["start"].str[:4] >= '2014'
idx = [i for i in idx if i in idy]
member.loc[idx, "end"] = '2022-12-31'

# Drop missing dates
member = member.loc[~member["start"].isna()].reset_index(drop=True)
member = member.loc[~member["end"].isna()].reset_index(drop=True)
member.loc[~member["start"].str.contains('http')].reset_index(drop=True)
member.loc[~member["end"].str.contains('http')].reset_index(drop=True)

# Map party_abbrev and chamber
member["party_abbrev"] = member["party"].map(party_map)
member["chamber"] = member["role"].map({'ledamot':'Enkammarriksdagen',
                                         'förstakammarledamot':'Första kammaren',
                                         'andrakammarledamot':'Andra kammaren'})

# Switch from wiki_id to person_id
person["person_id"] = person["wiki_id"] # Temporary id
d = {row["wiki_id"]:row["person_id"] for _, row in person.iterrows()}
files_to_modify = ['person', 'location_specifier', 'member_of_parliament', 'minister', 'name', 'party_affiliation', 'speaker']

for file in files_to_modify:
	df = pd.read_csv(f'corpus/metadata/{file}.csv')
	df['person_id'] = df['wiki_id'].map(d)
#	if file != 'person':
#		df.drop('wiki_id', axis=1)
	df.to_csv(f'corpus/metadata/{file}.csv', index=False)

# Also on aggregated files
member['person_id'] = member['wiki_id']
minister['person_id'] = minister['wiki_id']
speaker['person_id'] = speaker['wiki_id']
member.drop('wiki_id', axis=1)
minister.drop('wiki_id', axis=1)
speaker.drop('wiki_id', axis=1)

# Save files used for matching
member = member.drop_duplicates()
minister = minister.drop_duplicates()
speaker = speaker.drop_duplicates()
member.to_csv('input/matching/member_of_parliament.csv', index=False)
minister.to_csv('input/matching/minister.csv', index=False)
speaker.to_csv('input/matching/speaker.csv', index=False)
