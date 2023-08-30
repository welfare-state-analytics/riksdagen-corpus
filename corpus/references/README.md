# References

This directory contains references used within the corpus. The sub-directory `bibfiles/` contains `.bib` files for each reference. A single reference list `.bib` file can be compiled using `scripts/references/compile-bib-references.py`.


## Conventions

Each file contained in the `bibfiles/` directory is named the same as its citation key + `.bib`. Citation keys have the following conventions:

### Single-author works

Single author works are named `authorsurnameYEAR` in all lowercase, e.g.

	smith1984

unless the surname has a prefix, then the surname is cammel case starting with a lower case letter, e.g.

	vanHout1999


### Two-author works

Works with two authors are cited like `Author1Author2YEAR`, e.g.:

	SmithAndersson2002

Surname prefixes are lowercase for author 1 and uppercase for author two.

	SmithVanHout1982


### More than two authors

Multi-author (3+) works are cited as `Author1EAYEAR`, e.g.:

	AnderssonEA2019

First-author prefixes remain lower-case

vanHoutEA2022


### Undated works

Undated works follow the same conventions as above, but instead `YEAR` is replaced with `ND`+`single descriptive word` in lower case or multiword starting with lowercase and cammel case for all words after word1

	AnderssonNDsvenskKokbok 


### Busy authors

Authors that have multiple works in the same year receive descriptive-word suffixes as in Undated works to distinguish works penned in the same year.

	magnusson2020critiqueOfTraditionalStatistics
	magnusson2020bayesianIsBetter


### Works with volumes

Works with multiple volumes are suffixed with `v1`, `v2`, etc

	NorbergEA1988v1
	NorbergEA1988v2

Do this even if the years and / or authorship is different.