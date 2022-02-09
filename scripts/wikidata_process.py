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
#prime_minister = pd.read_csv(os.path.join('corpus', 'prime_minister.csv'))
speaker = pd.read_csv(os.path.join('corpus', 'speaker.csv'))

# Drop parties never present in riksdagen
with open('corpus/party_mapping.json', 'r') as f:
	party_map = json.load(f)
party["party_abbrev"] = party["party"].map(party_map)
party = party.dropna().reset_index(drop=True)

# Ministers
minister["role"] = minister["role"].str.replace('Sveriges ', '')
minister = minister.merge(individual, on=['wiki_id'])
minister = minister.merge(location, on=['wiki_id'])
minister = minister.merge(name, on=['wiki_id'])

# Speakers
speaker = speaker.merge(individual, on=['wiki_id'])
speaker = speaker.merge(location, on=['wiki_id'])
speaker = speaker.merge(name, on=['wiki_id'])

# Members
member = member.merge(individual, on=['wiki_id'])
member = member.merge(location, on=['wiki_id'])
member = member.merge(name, on=['wiki_id'])

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
