## Matching

Aggregated metadata files that have been used for or are a product of the person-speech matching algorithm are stored here.

### unknown.csv

When a speech fails to be linked to a unique person, the speech is tagged to have an unknown speaker. Information of this speaker (gender, party, role) is however often still available. This metadata is stored here together with the speeches introduction hash.

### Other files
These are the files used for person-speech matching. They are joined from the relevant corpus/metadata files and are subject to preprocessing needed for matching. For example names are cleaned, and missing time specific party affiliations are imputed.