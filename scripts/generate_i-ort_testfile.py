#!/usr/bin/env python3
"""
Genenrates quality assessment file with list of i-ort.
"""
import pandas as pd


def main():

	df = pd.read_csv("corpus/quality_assessment/known_mps/known_mps_catalog.csv", sep=";")

	counter = 0
	c1 = 0
	lines = len(df)
	rows = []
	for i, r in df.iterrows():
		c1 += 1
		if "senare" in r["surname_iort"]:
			primary, rest = r["surname_iort"].split('senare')
			primary = primary.strip(' ')
			primary = primary.strip(',')

			surname, ort1 = primary.split(' i ')
			rows.append([r["wiki_id"], surname, r["first_name"], ort1])
			orter = []
			#print(">", primary)
			#print("|", rest)
			for a in rest.split(','):
				for b in a.split(' o '):
					for c in b.split(' och '):
						if c.startswith("åter "):
							c = c[5:]
						if c:
							orter.append(c.strip())
			for ort in orter:
			#	print("-->", ort)
				counter += 1
				rows.append([r["wiki_id"], surname, r["first_name"], ort])

		else:
			try:
				surname, ort = r["surname_iort"].split(' i ')
			except:
				try:
					surname, ort = r["surname_iort"].split(' I ')
				except:
					print(r["surname_iort"])
			rows.append([r["wiki_id"], surname, r["first_name"], ort])

	outdf = pd.DataFrame(rows, columns=["wiki_id", "surname", "first_name", "iort"])
	outdf.to_csv("corpus/quality_assessment/known_iorter/known_iorter.csv", sep=";", index=False)
	
	print(counter, lines, c1, counter+lines, len(outdf))

if __name__ == '__main__':
	main()
