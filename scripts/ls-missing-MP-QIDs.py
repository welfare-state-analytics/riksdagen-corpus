#!/usr/bin/env python3
import pandas as pd
import os, json

def main():
	MPDir = "corpus/quality_assessment/known_mps"
	missings = os.listdir(MPDir)
	qids = []
	QIDs = {}
	for m in missings:
		if m.startswith('missing_'):
			df = pd.read_csv(f'{MPDir}/{m}', sep=';')
			for i, r in df.iterrows():
				if r['wiki_id'] not in qids:
					qids.append(r['wiki_id'])
				person = f"{r['wiki_id'].strip()} ({r['first_name'].strip()} {r['surname_iort'].strip()})"
				if person not in QIDs:
					QIDs[person] = [m]
				else:
					QIDs[person].append(m)
					
	QIDs = {k:v for k,v in sorted(QIDs.items(), key=lambda x: len(x[1]), reverse=True)}
	with open(f'{MPDir}/unique_missing_QIDs.json','w+') as outf:
		json.dump(QIDs, outf, indent=4, ensure_ascii=False)

	print(f"{len(QIDs)} == {len(qids)}?")
	if len(QIDs) != len(qids):
		print("\twell, no, it isn't. Checking duplicate wiki IDs...\n")
		qids = []
		for k, v in QIDs.items():
			ID = k.split(' (')[0]
			if ID in qids:
				print(k)
				for kk, vv in QIDs.items():
					if kk.startswith(f'{ID} ('):
						print('\t' + kk)
			else:
				qids.append(ID)

	print("\nFinally, checking for Q00FEL00 IDs...\n")
	for k,v in QIDs.items():
		if k.startswith('Q00FEL00'):
			print(f'{k}: {json.dumps(v, indent=4)}')




if __name__ == '__main__':
	main()
