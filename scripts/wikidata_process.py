'''
Script for processing raw wikidata tables into files used for corpus speech matching.
'''
from pyriksdagen.metadata import Corpus


def main():
	corpus = Corpus()

	corpus = corpus.add_mps()
	corpus = corpus.add_ministers()
	corpus = corpus.add_speakers()

	corpus = corpus.add_persons()
	corpus = corpus.add_location_specifiers()
	corpus = corpus.add_names()

	corpus = corpus.impute_dates()
	corpus = corpus.impute_parties()
	corpus = corpus.abbreviate_parties()
	corpus = corpus.clean_names()

	# Clean up speaker role formatting
	corpus["role"] = corpus["role"].replace({
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

	# Temporary ids
	corpus['person_id'] = corpus['wiki_id']

	# Drop individuals with missing names
	corpus = corpus[corpus['name'].notna()]

	# Remove redundancy and split file
	corpus = corpus.drop_duplicates()
	corpus = corpus.dropna(subset=['name', 'start', 'end'])
	corpus = corpus.sort_values(['wiki_id', 'start', 'end', 'name'])
	for file in ['member_of_parliament', 'minister', 'speaker']:
		df	= corpus[corpus['source'] == file]
		df.to_csv(f"input/matching/{file}.csv", index=False)


if __name__ == '__main__':
	main()