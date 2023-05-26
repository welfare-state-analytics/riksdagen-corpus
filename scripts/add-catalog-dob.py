#!/usr/bin/env python3
from tqdm import tqdm
import pandas as pd


def main():
	person = pd.read_csv("corpus/metadata/person.csv")
	catalog = pd.read_csv("corpus/quality_assessment/known_mps/catalog.csv", sep=';')
	DOBs = []
	for i, r in tqdm(catalog.iterrows(), total=len(catalog)):
		person_dobs = person[person['wiki_id'] == r['wiki_id']]
		if person_dobs.empty:
			DOBs.append(None)
		elif len(person_dobs) > 1:
			DOBs.append("Multival")
		else:
			DOBs.append(person_dobs.iloc[0]['born'])

	catalog['born'] = DOBs

	catalog.to_csv("corpus/quality_assessment/known_mps/catalog.csv", sep=';')

if __name__ == '__main__':
	main()
