"""
Impute districts gathered from wikipedia for years 24, 59, 61.
"""
import pandas as pd

mop = pd.read_csv('corpus/members_of_parliament.csv')
mop["year_imputed"] = 0

mop_districts = pd.read_csv('input/mp/mop_districts.csv')
mop_districts["chamber"] = 'Första kammaren'
years = list(set(mop_districts["year"]))

# Clean names
mop_districts["name"] = list(map(lambda x: x.split(',')[0], mop_districts["name"]))
mop_districts["name"] = list(map(lambda x: x.split(' i ')[0], mop_districts["name"]))

for year in years:
	fk = mop_districts.loc[mop_districts["year"] == year]

	a = 0
	for i,row in fk.iterrows():
		match = mop[(mop["name"] == row["name"]) &
					(mop["start"] == row["start_old"]) & 
					(mop["end"] == row["end_old"])]
		
		if len(match) == 1:
			mop.loc[match.index[0], "district"] = row["district"]
			mop.loc[match.index[0], "start"] = row["start"]
			mop.loc[match.index[0], "end"] = row["end"]
			mop.loc[match.index[0], "year_imputed"] = 1
		
		if len(match) == 0:
			print('No match found for:')
			print(row)

		if len(match) > 1:
			print('Multiple matches found for:')
			print(row)
			print('Matches:')
			print(match)

#mop.to_csv('mop_new.csv', index=False)
