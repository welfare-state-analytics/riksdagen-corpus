"""
Draw a random sample of the digital protocols
"""
import pandas as pd
import random
import os
import argparse

def package2url(package_id):
	folder = package_id.split('-')[1]
	file = package_id+'.xml'
	url = f'https://github.com/welfare-state-analytics/riksdagen-corpus/tree/main/corpus/protocols/{folder}/{file}'
	return url

# Sample before 1990
def sample():
	df = pd.read_csv("input/protocols/pages.csv")
	df['decade'] = df['year']//10*10
	decades = set(df['decade'])
	data = []
	for decade in decades:
		dfd = df[df['decade'] == decade].reset_index(drop=True)
		data.append(dfd.loc[random.sample(range(len(dfd)), 20), ['package_id', 'pagenumber']])
	df = pd.concat(data)
	df['url'] = df['package_id'].apply(package2url)
	df['annotator'] = ['johan', 'fredrik', 'väinö', 'robin']*(len(df)//4)
	return df

def sample_digital():
	folders = [f for f in os.listdir('corpus/protocols') if int(f[:4]) >= 1990]
	annotators = ['johan', 'fredrik', 'väinö', 'robin']

	# Sample 1 page per folder per person
	data = []
	for folder in folders:
		files = os.listdir(os.path.join(path, folder))
		random.shuffle(files)
		for file in files[:4]:
			package_id = file.replace('.xml', '')
			url = f'https://github.com/welfare-state-analytics/riksdagen-corpus/tree/main/corpus/protocols/{folder}/{file}'
			with open(os.path.join(path, folder, file)) as f:
				n = sum(1 for line in f)
			try:
				start = random.sample(range(n-100), 1)[0]
			except: # some protocols are too short
				start = 0
			data.append([package_id, start, url])

	df = pd.DataFrame(data, columns=['package_id', 'start', 'url'])
	df['annotator'] = ['johan', 'fredrik', 'väinö', 'robin']*(len(df)//4)
	return df

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	args = parser.parse_args()

	path = 'corpus/protocols'
	random.seed(123)

	df = sample()
	df.to_csv('input/manual-annotation-2022-march/sample.csv', index=False)

	df = sample_digital()
	df.to_csv('input/manual-annotation-2022-march/sample-digital.csv', index=False)
