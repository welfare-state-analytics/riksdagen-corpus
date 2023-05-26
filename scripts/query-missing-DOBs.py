#!/usr/bin/env python3
import pandas as pd
from wikidata.client import Client

def main():

	df = pd.read_csv("corpus/quality_assessment/known_mps/catalog.csv", sep=';')
	#df = pd.read_csv("corpus/quality_assessment/known_mps/integrity-error_missing-birthdate.csv", sep=';')
	#DOBisNA = df[df['born'].isna()]

	for i, r in df.iterrows():
		if pd.isna(df.iloc[i]['born']):
			try:
				e = Client().get(r['wiki_id'], load=True)
				date_of_birth = Client().get('P569')
				DOB = e[date_of_birth]
				df.at[i, 'born'] = DOB
				print(DOB)
			except:
				print('-------')
		else:
			print("Known DOB")

	df.to_csv("corpus/quality_assessment/known_mps/catalog.csv", sep=';', index=False)
	#df.to_csv("corpus/quality_assessment/known_mps/TEST_integrity-error_missing-birthdate.csv", sep=';', index=False)



if __name__ == '__main__':
	main()
