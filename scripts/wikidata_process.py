'''
Script for processing raw wikidata tables into files used for corpus speech matching.
'''
import numpy as np
import pandas as pd
import os, json
from pyriksdagen.mp import add_id
from pyriksdagen.match_mp import clean_names
import unicodedata
from datetime import datetime

def main():
	government = pd.read_csv('corpus/metadata/government.csv')
	person = pd.read_csv('corpus/metadata/person.csv')
	location_specifier = pd.read_csv('corpus/metadata/location_specifier.csv')
	member = pd.read_csv('corpus/metadata/member_of_parliament.csv')
	minister = pd.read_csv('corpus/metadata/minister.csv')
	name = pd.read_csv('corpus/metadata/name.csv')
	party = pd.read_csv('corpus/metadata/party_affiliation.csv')
	speaker = pd.read_csv('corpus/metadata/speaker.csv')
	party_map = pd.read_csv('corpus/metadata/party_abbreviation.csv')

	# Change end dates on year level to include whole year
	member["end"] = member["end"].str.replace('-01-01', '-12-31')
	minister["end"] = minister["end"].str.replace('-01-01', '-12-31')
	speaker["end"] = speaker["end"].str.replace('-01-01', '-12-31')

	### Process corpus data
	# Drop parties never present in riksdagen
	party_map = {row["party"]:row["abbreviation"] for _, row in party_map.iterrows()}
	party["party_abbrev"] = party["party"].map(party_map)
	party = party.dropna().reset_index(drop=True)

	# Name
	name["name"] = name["name"].str.replace('"','')
	name["name"] = name["name"].apply(clean_names)
	name = name.loc[name["name"] != ''].reset_index(drop=True)

	### Create dbs for matching
	# Minister
	# Impute end dates for ministers currently in office
	government.loc[government['start'] == max(government['start']), 'end'] = '2022-12-31'
	start_d = dict(zip(government['government'], government['start']))
	end_d = dict(zip(government['government'], government['end']))
	idx = minister['start'].isna()
	minister.loc[idx, 'start'] = minister.loc[idx, 'government'].map(start_d)
	idx = minister['end'].isna()
	minister.loc[idx, 'end'] = minister.loc[idx, 'government'].map(end_d)

	# Ministers
	minister = minister.merge(person, on='wiki_id', how='left')
	minister = minister.merge(location_specifier, on='wiki_id', how='left')	
	minister = minister.merge(name[['wiki_id', 'name']], on='wiki_id', how='left')
	minister["role"] = minister["role"].str.replace('Sveriges ', '')

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
	member["role"] = member["role"].str.extract(r'([A-Za-zÀ-ÿ]*ledamot)')

	# Impute missing party values for members (not used for other files atm)
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
	files_to_modify = [f for f in os.listdir('corpus/metadata') if f.endswith('.csv')]
	for file in files_to_modify:
		df = pd.read_csv(f'corpus/metadata/{file}')
		if file == 'person.csv':
			df.insert(0, 'person_id', person["wiki_id"])
		else:
			df = df.rename(columns={'wiki_id':'person_id'})			
		df.to_csv(f'corpus/metadata/{file}', index=False)

	# Also on aggregated files
	member = member.rename(columns={'wiki_id':'person_id'})
	minister = minister.rename(columns={'wiki_id':'person_id'})
	speaker = speaker.rename(columns={'wiki_id':'person_id'})
	
	# Save files used for matching
	member = member.drop_duplicates()
	minister = minister.drop_duplicates()
	speaker = speaker.drop_duplicates()
	member.to_csv('input/matching/member_of_parliament.csv', index=False)
	minister.to_csv('input/matching/minister.csv', index=False)
	speaker.to_csv('input/matching/speaker.csv', index=False)

if __name__ == '__main__':
	main()