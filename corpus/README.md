### Protocols
Contains the riksdagen protocols structured into subfolders for each parliamentary year.

### Metadata
The metadata folder contains useful variables for working with the corpus such as members of parliament, their gender and party affiltion, etc. Speeches in the protocols are linked to individuals in the metadata through the *person_id* variable. All metadata is formatted as fifth normal form csv tables, making it simple to join files together to get the metadata of interest.

The aim is to have all speeches linked to their respective speakers. Speeches not yet linked to the metadata are tagged as *unknown*. While not link is established to an individual person, there often is metadata contained in the speech which can be used. This information may contain gender, party affiliation and role (atm member of parliament, minister or speaker). This additional metadata is stored in *input/matching/unknowns.csv* and is linked to corpus speeches using a hash.
