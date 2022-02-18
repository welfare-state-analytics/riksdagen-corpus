## File descriptions

### government.csv
Governments of Sweden from the 1920s and their inception/dissolution dates.

### location_specifier.csv
It is common for parliamentary speakers to be referred to by the location they reside in. This file contains these person-location connections.

### member_of_parliament.csv
Data for members of parliament connected to some specific time period, for example mandate periods.

### minister.csv
Same as member_of_parliament.csv but for ministers.

### name.csv
Individuals can have multiple names, change names, have nicknames, which are contained in this file.

### party_abbreviation.csv
Parties can switch names as well as discrepancies between the corpus and metadata. This file maps parties to the most recent party abbreviation. While unusal, references to parties can have OCR-errors in the protocols (for example (m)->(rn)). This file has an additional column indicating whether the mapping is a true abbreviation or if it is used for OCR correction.

### party_affiliation.csv
The only other file containing party affiliation atm is member_of_parliament.csv (and is missing for 40% of observations). This is due to the party metadata having a direct link to individuals at certain time points for these observations. Party affiliations not tied to a specific time period is contained in party_affiliation.csv. 

### person.csv
Individual level data such as born, gender, etc. for all persons in the metadata.

### speaker.csv
Same as member_of_parliament.csv but for speakers.

### twitter.csv
Twitter handles.