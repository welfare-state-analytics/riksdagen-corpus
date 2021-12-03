# Swedish parliamentary proceedings - Riksdagens protokoll 1921-2021 v0.3.0

_Westac Project, 2020-2021_

The full data set consists of multiple parts:

- Riksdagens protokoll between from 1921 until today in the [Parla-clarin](https://github.com/clarin-eric/parla-clarin) format
- Comprehensive list of MPs and cabinet members during this period
- Traceable logs of all curation and segmentation as a git history
- [Documentation](https://github.com/welfare-state-analytics/riksdagen-corpus/wiki/) of the corpus and the curation process
- [A Google Colab notebook](https://colab.research.google.com/drive/1C3e2gwi9z83ikXbYXNPfB6RF7spTgzxA?usp=sharing) that demonstrates how the dataset can be used with Python

## Basic use

A full dataset is available under [this download link](https://github.com/welfare-state-analytics/riksdagen-corpus/releases/download/v0.3.0-alpha/corpus.zip). It has the following structure

- Annual protocol files in the ```corpus/``` folder
- List of MPs ```corpus/members_of_parliament.csv```
- List of ministers ```corpus/ministers.csv```
- List of speakers of the house ```corpus/talman.csv```

The workflow to use the data is demonstrated in [this Google Colab notebook](https://colab.research.google.com/drive/1C3e2gwi9z83ikXbYXNPfB6RF7spTgzxA?usp=sharing).

## Participate in the curation process

The corpora are large and automatically curated and segmented. If you find any errors, it is possible to submit corrections to them. This is documented in the [project wiki](https://github.com/welfare-state-analytics/riksdagen-corpus/wiki/Submit-corrections).
