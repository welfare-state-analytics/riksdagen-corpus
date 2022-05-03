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
import calendar

def impute_date_precision(date, start=True):
	if not date:
		return ''

	date = date.split('-')
	if len(date) == 1 and start:
		return '-'.join([date[0], '01', '01'])

	if len(date) == 2 and start:
		return '-'.join([date[0], date[1], '01'])
	
	if len(date) == 1 and not start:
		return '-'.join([date[0], '01', '31'])

	if len(date) == 2 and not start:
		day = calendar.monthrange(int(date[0]), int(date[1]))[1]
		return '-'.join([date[0], date[1], str(day)])

	if len(date) == 3:
		return '-'.join(date)


def check_date_overlap(start1, end1, start2, end2):
	latest_start = max(start1, start2)
	earliest_end = min(end1, end2)
	delta = (earliest_end - latest_start).days + 1
	overlap = max(0, delta)
	if overlap > 0:
		return True
	else:
		return False

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
	party = party[~party['start'].fillna('').str.contains('http')]
	party = party[~party['end'].fillna('').str.contains('http')]
	party = party.reset_index(drop=True)
	
	#party_map = {row["party"]:row["abbreviation"] for _, row in party_map.iterrows()}
	#party["party_abbrev"] = party["party"].map(party_map)
	#party = party.dropna().reset_index(drop=True)


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
	minister = minister[minister['name'].notna()].reset_index(drop=True)

	# Speakers
	idx = (speaker['start'] == max(speaker['start'])) & speaker['end'].isna()
	if sum(idx) > 0:
		speaker.loc[idx, 'end'] = speaker.loc[idx, 'end'] = '2022-12-31'

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

	# Drop members with missing start date
	member = member.loc[~member["start"].isna()].reset_index(drop=True)
	member = member[~member['start'].fillna('').str.contains('http')]
	member = member[~member['end'].fillna('').str.contains('http')]

	# Impute end dates for members currently in office
	idx = member["end"].isna()
	idy = member["start"].fillna('').apply(lambda x: int(str(x)[:4]) >= 2014)
	member.loc[idx*idy, "end"] = '2022-12-31'

	# Drop members withm missing end date after imputation
	member = member.loc[~member["end"].isna()].reset_index(drop=True)

	
	# Impute missing party values for members (not used for other files atm)
	# Drop parties that are not unique AND that lack BOTH start and end date
	party['start'] = party['start'].fillna('')
	party['end'] = party['end'].fillna('')
	party['start'] = party['start'].apply(impute_date_precision, start=True)
	party['end'] = party['end'].apply(impute_date_precision, start=False)
	party['start'] = pd.to_datetime(party['start'], format='%Y-%m-%d')
	party['end'] = pd.to_datetime(party['end'], format='%Y-%m-%d')
	member['start'] = pd.to_datetime(member['start'], format='%Y-%m-%d')
	member['end'] = pd.to_datetime(member['end'], format='%Y-%m-%d')
	
	data = []
	for i, row in member[member['party'].isnull()].iterrows():	
		parties = party[party['wiki_id'] == row['wiki_id']]
		
		if len(parties) == 0:
			continue

		if len(set(parties['party'])) == 1:
			member.loc[i,'party'] = parties['party'].iloc[0]
			
		if len(set(parties['party'])) >= 2:
			for j, sow in parties.iterrows():
				res = check_date_overlap(row['start'], sow['start'], row['end'], sow['end'])
				m = row.copy()
				m['party'] = sow['party']
				data.append(m)
				#member = pd.concat([member, m])
	data = pd.DataFrame(data, columns=member.columns)
	member = pd.concat([member, data]).reset_index(drop=True)
	
#	idx = member["party"].isnull()
#	missing = member.loc[idx]
#	missing = missing.merge(party, on='wiki_id', how='left')
#	member.loc[idx, "party"] = missing["party_y"]

	# Map party_abbrev and chamber
	party_map = {row['party']:row['abbreviation'] for _, row in party_map.iterrows()}
	member["party_abbrev"] = member["party"].fillna('').map(party_map)
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