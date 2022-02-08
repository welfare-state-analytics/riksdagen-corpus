'''
Script for processing raw wikidata tables.
'''
import numpy as np
import pandas as pd
import os, json
from pyriksdagen.mp import add_id
import unicodedata

def join_metadata(db, meta_db):
	db = db.reset_index().merge(meta_db, on='wiki_id', how='left').set_index('index')
	return db	

path_wiki = 'input/wikidata/raw'

alias = pd.read_csv(os.path.join(path_wiki, 'alias.csv'))
#government = pd.read_csv(os.path.join(path_wiki, 'government.csv'))
individual = pd.read_csv(os.path.join(path_wiki, 'individual.csv'))
member = pd.read_csv(os.path.join(path_wiki, 'member.csv'))
minister = pd.read_csv(os.path.join(path_wiki, 'minister.csv'))
name = pd.read_csv(os.path.join(path_wiki, 'name.csv'))
party = pd.read_csv(os.path.join(path_wiki, 'party_affiliation.csv'))
#prime_minister = pd.read_csv(os.path.join(path_wiki, 'prime_minister.csv'))
speaker = pd.read_csv(os.path.join(path_wiki, 'speaker.csv'))

with open('corpus/party_mapping.json', 'r') as f:
	party_map = json.load(f)

### Party
# Drop parties never present in riksdagen
party = party.loc[party["party"].apply(lambda x: x in party_map)]

# Drop conflicting individual level party values
# Matching would work without it but could bias results by arbitrarily mapping to the wrong party
party = party.groupby('wiki_id').filter(lambda x: len(set(x["party"])) == 1)
party = party.reset_index(drop=True)

# Skip using individual party start-end for now
party = party.drop(["start", "end"], axis=1)

# Member
# Impute missing party values with unique individual level values
member = join_metadata(member, name)
member = join_metadata(member, individual)
member = join_metadata(member, alias)

# Already contains party, impute only missing values
idx = member["party"].isnull()
missing = member.loc[idx]
missing = missing.reset_index().merge(party, on='wiki_id', how='left').set_index('index')
member.loc[idx, "party"] = missing["party_y"]

# Rename for backwards compatability
member = member.rename(columns={'role':'chamber'})
member["chamber"] = member["chamber"].map({	'ledamot av Sveriges riksdag':'Enkammarriksdagen',
									 		'förstakammarledamot':'Första kammaren',
									 		'andrakammarledamot':'Andra kammaren'})

# Minister
minister["role"] = minister["role"].str.replace('Sveriges ', '')
minister = join_metadata(minister, name)
minister = join_metadata(minister, individual)
minister = join_metadata(minister, party)
minister = join_metadata(minister, alias)

# Speaker
speaker = join_metadata(speaker, name)
speaker = join_metadata(speaker, individual)
speaker = join_metadata(speaker, party)
speaker = join_metadata(speaker, alias)

### Add ids
# Member
add_id(member)
member["id"] = member["id"] + '_w'

# Speaker
speaker_map = {
	'första kammarens vice talman':'fk_vice_talman',
	'första kammarens talman':'fk_talman',
	'andra kammarens vice talman':'ak_vice_talman',
	'förste vice talman i första kammaren':'fk_1_vice_talman',
	'andra kammarens andre vice talman':'ak_2_vice_talman',
	'andre vice talman i första kammaren':'fk_2_vice_talman',
	'Sveriges riksdags talman':'talman',
	'andra kammarens talman':'ak_talman',
	'andra kammarens förste vice talman':'ak_1_vice_talman'
	}

speaker["id"] = pd.Series(str)
for i, row in speaker.iterrows():
	name = unicodedata.normalize("NFD", row["name"])
	name = name.encode("ascii", "ignore").decode("utf-8")
	name = name.lower().replace(" ", "_")
	name = name.replace(".", "").replace("(", "").replace(")", "").replace(":", "")
	speaker.loc[i, "id"] = speaker_map.get(row["role"]) + '_' + name + '_w'

# Minister
minister["id"] = pd.Series(str)
for i, row in minister.iterrows():
	name = unicodedata.normalize("NFD", row["name"])
	name = name.encode("ascii", "ignore").decode("utf-8")
	name = name.lower().replace(" ", "_")
	name = name.replace(".", "").replace("(", "").replace(")", "").replace(":", "")
	role = unicodedata.normalize("NFD", row["role"])
	role = role.encode("ascii", "ignore").decode("utf-8")
	role = role.lower().replace(" ", "_")
	role = role.replace(".", "").replace("(", "").replace(")", "").replace(":", "")	
	minister.loc[i, "id"] = name + '_' + role + '_w'

member.to_csv('corpus/members_of_parliament_w.csv', index=False)
minister.to_csv('corpus/ministers_w.csv', index=False)
speaker.to_csv('corpus/speakers_w.csv', index=False)