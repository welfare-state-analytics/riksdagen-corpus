import numpy as np
import pandas as pd
from datetime import datetime, timedelta

"""
Used for algorithmically providing dates for the (vice) talmän dataset.
"""

# Load and format data
talman = pd.read_csv('corpus/talman.csv')
talman["start"] = talman["start"].fillna('9999')
talman["end"] = talman["end"].fillna('9999')
talman["start"] = talman["start"].astype(str)
talman["end"] = talman["end"].astype(str)
talman["end"] = list(map(lambda x: x.split('.')[0], talman["end"]))

rd_dates = pd.read_csv('corpus/riksdagen_dates.csv')
rd_dates = rd_dates.dropna(subset=['start'])
rd_dates = rd_dates.drop_duplicates(subset='start')

years = rd_dates["start"].str.split('-')
rd_dates["year"] = [year[0] for year in years]
rd_dates = rd_dates.groupby('year').filter(lambda x : len(x)==1)
rd_dates = rd_dates.reset_index()

rd_dates["end"] = pd.Series(dtype=str)

# Reformat days to YYYY-MM-DD
for i in range(len(rd_dates)):

	# Format and store starting date
	date = rd_dates.loc[i,"start"]
	year,month,day = date.split('-')
	date = '-'.join([year,day,month])
	rd_dates.loc[i,"start"] = date

	# Convert datetime in order to back a day
	date = datetime.strptime(date, '%Y-%d-%m')
	date = str(date - timedelta(days = 1)).split(' ')[0]

	year,month,day = date.split('-')
	date = '-'.join([year,day,month])

	rd_dates.loc[i,"end"] = date

# Find non-overlapping stard-end years
start_no_overlap = list(set(talman["start"]) - set(talman["end"]))
end_no_overlap = list(set(talman["end"]) - set(talman["start"]))

for i in range(len(talman)):
	talman_start, talman_end = talman.loc[i, ["start", "end"]]
	
	# If no one ends when someone starts, make starting date 'YYYY-01-01'
	if talman_start in start_no_overlap:
		talman.loc[i, "start"] = '-'.join([talman_start, '01', '01'])

	# Else make date day of starting the riksdagen year
	else:
		id_start = np.where(rd_dates["year"] == talman_start)[0]
		# In few cases we have multiple 1st protocols, skip these
		if len(id_start) == 1:
			talman.loc[i,"start"] = rd_dates.loc[id_start[0],"start"]

	# If no one starts when someone ends, make starting date 'YYYY-31-12'
	if talman_end in end_no_overlap:
		talman.loc[i, "end"] = '-'.join([talman_end, '31', '12'])

	# Else make date day BEFORE starting of the NEXT riksdagen year
	else:
		id_end = np.where(rd_dates["year"] == talman_end)[0]
		# In few cases we have multiple 1st protocols, skip these
		if len(id_end) == 1:
			talman.loc[i,"end"] = rd_dates.loc[id_end[0],"end"]

talman.loc[talman["start"] == '9999-01-01', "start"] = np.nan
talman.loc[talman["end"] == '9999-31-12', "end"] = np.nan

talman.to_csv('corpus/talman_new.csv', index=False)

		




