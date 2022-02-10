'''
Script for processing raw wikidata tables.
'''
import numpy as np
import pandas as pd
import os, json
from pyriksdagen.mp import add_id
import unicodedata
from datetime import datetime

#government = pd.read_csv(os.path.join('corpus', 'government.csv'))
individual = pd.read_csv(os.path.join('corpus', 'individual.csv'))
location = pd.read_csv(os.path.join('corpus', 'location.csv'))
member = pd.read_csv(os.path.join('corpus', 'member.csv'))
minister = pd.read_csv(os.path.join('corpus', 'minister.csv'))
name = pd.read_csv(os.path.join('corpus', 'name.csv'))
party = pd.read_csv(os.path.join('corpus', 'party_affiliation.csv'))
prime_minister = pd.read_csv(os.path.join('corpus', 'prime_minister.csv'))
speaker = pd.read_csv(os.path.join('corpus', 'speaker.csv'))

# Drop 1 character names
name["name"] = name["name"].apply(lambda x: ' '.join([i for i in x.split() if len(i) > 1]))
name = name.loc[name["name"] != ''].reset_index(drop=True)

# Map gender to english
individual["gender"] = individual["gender"].map({'kvinna':'woman', 'man':'man'})

# Drop parties never present in riksdagen
with open('corpus/party_mapping.json', 'r') as f:
	party_map = json.load(f)
party["party_abbrev"] = party["party"].map(party_map)
party = party.dropna().reset_index(drop=True)

# Prime ministers
prime_minister = prime_minister.merge(individual, on='wiki_id', how='left')
prime_minister = prime_minister.merge(location, on='wiki_id', how='left')
prime_minister = prime_minister.merge(name, on='wiki_id', how='left')

# Ministers
minister = minister.merge(individual, on='wiki_id', how='left')
minister = minister.merge(location, on='wiki_id', how='left')
minister = minister.merge(name, on='wiki_id', how='left')
minister = minister.append(prime_minister) # add prime ministers
minister["role"] = minister["role"].str.replace('Sveriges ', '')

# Speakers
speaker = speaker.merge(individual, on='wiki_id', how='left')
speaker = speaker.merge(location, on='wiki_id', how='left')
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
member = member.merge(individual, on='wiki_id', how='left')
member = member.merge(location, on='wiki_id', how='left')
member = member.merge(name, on='wiki_id', how='left')

# Clean values
member["role"] = member["role"].str.extract(r'([A-Za-zÀ-ÿ]*ledamot)')

# Impute missing party values for members
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

# Save files used for matching
member.to_csv('input/matching/member.csv', index=False)
minister.to_csv('input/matching/minister.csv', index=False)
speaker.to_csv('input/matching/speaker.csv', index=False)
