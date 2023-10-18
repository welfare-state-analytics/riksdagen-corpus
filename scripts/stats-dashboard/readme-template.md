[![Unit tests](https://github.com/welfare-state-analytics/riksdagen-corpus/actions/workflows/push.yml/badge.svg)](https://github.com/welfare-state-analytics/riksdagen-corpus/actions/workflows/push.yml)
[![Validate Parla-Clarin XML](https://github.com/welfare-state-analytics/riksdagen-corpus/actions/workflows/validate.yml/badge.svg)](https://github.com/welfare-state-analytics/riksdagen-corpus/actions/workflows/validate.yml)


# Swedish parliamentary proceedings --- 1867--today

_Westac Project, 2020--2023_

_Swerik Project, 2023--2025_

## The data set

The full data set consists of multiple parts:

- Parliamentary records (riksdagens protokoll) from 1867 until today in the [Parla-clarin](https://github.com/clarin-eric/parla-clarin) format
- Comprehensive list of members of parliament, ministers and governments during this period + associated metadata (mandate periods, party info, etc)
- [In progress] An annotated catalog of motions submitted to the parliament with linked metadata
- [Documentation](https://github.com/welfare-state-analytics/riksdagen-corpus/tree/main/docs/) of the corpus and the curation process
- [A Google Colab notebook](https://colab.research.google.com/drive/1C3e2gwi9z83ikXbYXNPfB6RF7spTgzxA?usp=sharing) that demonstrates how the dataset can be used with Python

## Basic use

A full dataset is available under [this download link](https://github.com/welfare-state-analytics/riksdagen-corpus/releases/latest/download/corpus.zip). It has the following structure

- Annual protocol files in the ```corpus/protocols/``` folder
- Structured metadata on members of parliament, ministers, and governments in the ```corpus/metadata/``` folder

The workflow to use the data is demonstrated in [this Google Colab notebook](https://colab.research.google.com/drive/1C3e2gwi9z83ikXbYXNPfB6RF7spTgzxA?usp=sharing).

## Design choices of the project

The Riksdagen corpus is released as an iterative process, where the corpus is curated and expanded. Semantic versioning is used for the whole corpus, following the established major-minor-patch practices as they apply to data. For each major and minor release, a battery of unit tests are run and a statistical sample is drawn, annotated and quantitatively evaluated to ensure integrety and quality of updated data. Errors are fixed as they are detected in order of priority. Moreover, the edit history is kept as a traceable git repository.

While the contents of the corpus will change due to curation and expansion, we aim to keep the deliverable API, the `corpus/` folder, as stable as possible. This means we avoid relocating files or folders, changing formats, changing columns in metadata files, or any other changes that might break downstream scripts. Conversely, files outside the `corpus/` folder are internal to the project. End users may find utility in them but we make no effort to keep them consistent.

The data in the corpus is delivered as TEI XML files to follow established practices. The metadata is delivered as CSV files, following a [normal form](https://en.wikipedia.org/wiki/Database_normalization) database structure while allowing for a legible git history. A more detailed description of the data and metadata structure and formats can be found in the README files in the `corpus/` folder.

## Descriptive statistics at a glance

{sumstats_table}




\* Digital original parliamentary records in the period YEAR--YEAR were not paginated and thus do not contribute to the page count.

### Documents by type over time

FIGURE: N-protocols over time

### Members of Parliament over time

FIGURE: N by chamber/year

## Quality assessment

### Correct number of MPs over time

FIGURE: ratio of MP mandates and baseline

### Speech-to-speaker mapping

We check how many speakers in the parliamentary records our algorithms idenify in each release. 

![Estimate of mapping accuracy](https://raw.githubusercontent.com/welfare-state-analytics/riksdagen-corpus/main/input/accuracy/version_plot.png)


## Participate in the curation process

If you find any errors, it is possible to submit corrections to them. This is documented in the [project wiki](https://github.com/welfare-state-analytics/riksdagen-corpus/wiki/Submit-corrections).


## Acknowledgement of support
