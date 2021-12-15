"""
Script to change imputed time periods for första kammaren to manually collected ones from stadskalendern.
TODO: Something is slightly broken atm
"""
import numpy as np
import pandas as pd
import json

with open('corpus/fk_mandatperioder.json') as f:
	mandatperioder = json.load(f)

district_map = pd.read_csv('corpus/district_mapping.csv', delimiter=';')
members_of_parliament = pd.read_csv('corpus/members_of_parliament.csv')

# Clean dataset
members_of_parliament["start_imp"] = np.zeros(len(members_of_parliament))
members_of_parliament["end_imp"] = np.zeros(len(members_of_parliament))
n_fk = len(members_of_parliament.loc[members_of_parliament["chamber"] == "Första kammaren"])
members_of_parliament.loc[members_of_parliament["chamber"] == "Första kammaren", "start_imp"] = np.ones(n_fk)
members_of_parliament.loc[members_of_parliament["chamber"] == "Första kammaren", "end_imp"] = np.ones(n_fk)

for i in range(2):
	mop = members_of_parliament.loc[members_of_parliament["chamber"] == "Första kammaren"]
	control = mop.copy()

	for i,row in mop.iterrows():
		year = row["start"] + 3 # reverse engineer
		district = district_map[district_map["district"] == row["district"]]
		if len(district) == 0:
			continue
		district = district.iloc[0]["district_abbrev"]
		periods = mandatperioder.get(row["district"])

		if type(periods) == list: # period data is not complete yet
			
			start = [p for p in periods if p >= year]
			if (len(start) > 0) & (row["start_imp"] == 1): # period data is not complete yet
				members_of_parliament.loc[i, "start"] = max(start)
				members_of_parliament.loc[i, "start_imp"] = 0
			
			end = [p for p in periods if p < year]
			if (len(end) > 0) & (row["end_imp"] == 1): # period data is not complete yet
				
				members_of_parliament.loc[i, "end"] = min(end)
				members_of_parliament.loc[i, "end_imp"] = 0

	mop = members_of_parliament.loc[members_of_parliament["chamber"] == "Första kammaren"]
	changed_start = round(sum(mop["start"] != control["start"]) / len(control)*100, 2)
	changed_end = round(sum(mop["end"] != control["end"]) / len(control)*100, 2)
	print(f'FK start valued changed: {changed_start}%')
	print(f'FK end valued changed: {changed_end}%')

#members_of_parliament.to_csv('corpus/members_of_parliament.csv', index=False)