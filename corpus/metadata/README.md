## File descriptions

### government.csv

Governments of Sweden from the 1920s and their inception/dissolution dates.

- *start*: date of governments inception
- *end*: date of governments dissolution
- *government*: name of government

### location_specifier.csv

It is common for parliamentary speakers to be referred to by the location they reside in. This file contains these person-location connections.

- *person_id*: id for individuals in corpus metadata
- *location*: location that may be used in conjunction of persons name when referring to the person in parliament in order to distinguish person from others with similar names

### member_of_parliament.csv

Data for members of parliament connected to some specific time period, for example mandate periods.

- *person_id*: id for individuals in corpus metadata
- *district*: electoral district person is representing
- *end*: date of person leaving parliament
- *party*: party affiliation
- *role*: indicates which chamber the person is active in
- *start*: date of person entering parliament

### minister.csv

Same as member_of_parliament.csv but for ministers.

- *person_id*: id for individuals in corpus metadata
- *end*: date of person leaving government position
- *government*: name of government that person is member of
- *role*: government post that person has (often some kind of minister)
- *start*: date of person entering government position

### name.csv

Individuals can have multiple names, change names, have nicknames, which are contained in this file.

- *person_id*: id for individuals in corpus metadata
- *name*: name of person
- *primary_name*: indicates whether a name is believed to be the primary name used for that person

### party_abbreviation.csv

Parties can switch names as well as discrepancies between the corpus and metadata. This file maps parties to the most recent party abbreviation. While unusal, references to parties can have OCR errors in the protocols (for example (m)->(rn)). This file has an additional column indicating whether the mapping is a true abbreviation or if it is used for OCR correction.

- *party*: different names (or abbreviations) for a party in the metadata or corpus
- *abbreviation*: standardized abbreviations from most recent party names
- *ocr_correction*: indicates whether the party->abbreviation mapping is used for correcting systematic OCR errors in the corpus or whether it is a "correct" mapping

### party_affiliation.csv

The only other file containing party affiliation atm is member_of_parliament.csv (and is missing for 40% of observations). This is due to the party metadata having a direct link to individuals at certain time points for these observations. Party affiliations not tied to a specific time period is contained in party_affiliation.csv. 

- *person_id*: id for individuals in corpus metadata
- *party*: party that person is or has been a member of

### person.csv

Individual level data such as born, gender, etc. for all persons in the metadata.

- *person_id*: id for individuals in corpus metadata
- *wiki_id*: id for wikidata object
- *born*: date of birth
- *dead*: date of death
- *gender*: gender
- *riksdagen_guid*: guid for riksdagen open data individual
- *riksdagen_id*: id for riksdagen open data individual

### speaker.csv

Same as member_of_parliament.csv but for speakers.

- *person_id*: id for individuals in corpus metadata
- *end*: date of person leaving position as speaker
- *role*: position as 1/2/3 (vice) speaker
- *start*: date of person entering position as speaker

### twitter.csv

Twitter handles.

- *person_id*: id for individuals in corpus metadata
- *twitter*: twitter handle