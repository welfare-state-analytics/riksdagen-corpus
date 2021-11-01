"""
New version of matching algorithm with fuzzy matching implemented:
TODO:
	- Change party in df to party_abbrev
	- Switch from filtering with chamber to matching with it (in case speaker is in "wrong" chamber)
	- Implement talman and minister matching
	- Improve date metadata
	- Factor code into functions
	- Differ between unknown and indistinguishable in results summary
	- Protocols often have very few intros detected, look into potential bug
	- OBS may have bug, matching if detected intro data and mop are missing for same variable

Notes from data exploration:
	- Found name "Fr. Julin", Fr. stands for Fröken?
	- Problems with year filtering:
		1. imputed data causes overlaps
		2. year is taken from first filename, i.e. 196767 --> 1976 causing lots of years being wrong.
			this should not be solved by buffers (until we have matched mop entries on individual level)as it causes overlaps.
			solution atm would be to use 1. docDate, 2. some other date.
			docDate seems unreliable (can be wrong or completely missing) but is probably the best option atm.
			some other date could be to scrape "date" tags together with intros and give intros the latest "date" tag.
			pretty good solution for now is probably to use docDate and substitute it for filename[:4] if it is missing or potentially contains conflicts
	- Observed lots of Unknown for first couple of ~100 protocols, investigate why
"""
import textdistance
import numpy as np
import pandas as pd
import re
from progressbar import progressbar

from pyriksdagen.segmentation import (
    detect_mp_new
)

def clean_names(names):
	names = names.str.replace('.','', regex=False) # A.C. Lindblad --> AC Lindblad
	names = names.str.replace('-',' ', regex=False) # Carl-Eric Lindblad --> Carl Eric Lindblad
	names = names.str.lower()
	return names

fuzzy = textdistance.Levenshtein(external=False) 

# Output object for summarizing results
matches = pd.DataFrame(np.zeros((1,7)), dtype = int)
matches.columns = ["name", "fuzzy", "no_match", "indistinguishable", "party_specifier", "party", "specifier"]

# Import patterns
patterns = pd.read_json("input/segmentation/detection.json", orient="records", lines=True)
expressions = []

for _, pattern in patterns.iterrows():
    exp, t = pattern["pattern"], pattern["type"]
    exp = re.compile(exp)
    expressions.append((exp, t))

# Import data
members_of_parliament = pd.read_csv('corpus/members_of_parliament.csv')
members_of_parliament["name"] = clean_names(members_of_parliament["name"])

# Sort by protocol id, not sure where we want the final outputs,
# but at least iterate over protocols to filter mop more efficiently.
# could sort by year,chamber,protocol to filter more efficiently
intros = pd.read_csv('output.csv').sort_values(by="protocol").reset_index()
protocols = sorted(list(set(intros["protocol"])))

for protocol in progressbar(protocols):
	df = intros[intros["protocol"] == protocol][:]
	year, chamber = df.iloc[0][["year", "chamber"]] # Weird hacky syntax
	
	# Filter mop on protocol level
	#mop = members_of_parliament.query(f'{year} >= start-1 and {year} <= end+1') #Old version
	mop = members_of_parliament.query(f'{year} >= start and {year} <= end') # skip buffer to avoid overlaps
	mop = mop[mop["chamber"] == chamber]

	# move this before for loop and fill "" --> nan to solve potential matching bug (as nan != nan)
	results = list(map(lambda x: detect_mp_new(x, expressions), df["intro"]))
	df["other"] = list(map(lambda x: x.get("other", ""), results))
	df["gender"] = list(map(lambda x: x.get("gender", ""), results))
	df["party"] = list(map(lambda x: x.get("party", ""), results))
	df["specifier"] = list(map(lambda x: x.get("specifier", ""), results))
	df["name"] = list(map(lambda x: x.get("name", ""), results))
	df["name"] = clean_names(df["name"])
	# Add party abbreviations mapping
	
	for i,row in df.iterrows():
		# fun starts here
		name, gender, party, specifier, other = row[["name","gender","party","specifier","other"]]
		
		# Matching algoritm:
		if other == 'talman':
			pass # debug
			# return match_talman()

		elif other == 'statsrådet':
			pass # debug
			# return match_minister()
			
		else:
			# filter by gender
			candidates = mop[mop["gender"] == gender]

			# match by name
			idx = [i for i,m in candidates.iterrows() if name in m["name"]]

			# if unique match, return mop id
			if len(idx) == 1:
				matches["name"] += 1
				# return candidates.loc[idx,"id"]

			# if no matches, perform fuzzy and proceed from there
			if len(idx) == 0:
				idx = [i for i,m in candidates.iterrows() if fuzzy(name,m["name"]) == 1]
				
				# if unique match, return mop id
				if len(candidates) == 1:
					matches["fuzzy"] += 1
					# return candidates.loc[idx,"id"]

				# if still no match, return unknown
				elif len(candidates) == 0:
					matches["no_match"] += 1
					# return 'Unknown'

			# if multiple candidates, start filtering other variables
			if len(idx) > 1:
				candidates = candidates.loc[idx]
				
				# Broken atm due to missing party_abbrev
				idx = np.where((candidates["specifier"] == specifier) & (candidates["party_abbrev"] == party))[0]
				if len(idx) == 1:
					matches["party_specifier"] += 1
					# return candidates.loc[idx,"id"]

				idx = np.where(candidates["specifier"] == specifier)[0]
				if len(idx) == 1:
					matches["specifier"] += 1
					# return candidates.loc[idx,"id"]

				# Broken atm due to missing party_abbrev
				idx = np.where(candidates["party_abbrev"] == party)[0]
				if len(idx) == 1:
					matches["party"] += 1
					# return candidates.loc[idx,"id"]

			# return 'Unknown'
		
print(matches)



## For prot in protocols:
# Make it same format (can probably be written more nicely)
# Unsure of how to use .get("x", "") on a list together with multiple keys


 # testing?

# Filter mop on protocol level


### fun(protocol, mop_filtered, ministers_filtered, talman_filtered, expressions) 
### return mop id





print(matches)	


			# filter by party and specifier



#for i,row in df.iterrows():
#
#	intro, chamber, year = row[["intro", "chamber", "year"]]
#	# Check that year is within 1 year difference
#
#	results = detect_mp_new(row["intro"], expressions)
#	name = results.get("name", "")
#	print(results)
#	print(chamber)
#	print(year)
#	
#	#if len(name.split()) > 2: # Check to find strange names
#	#	print(name)
#
#
## Matching algorithm
#
#mop = {'name': ['Johan Larsson', 'Johan Larsson', 'Johan Larsson'],\
#	   'parti':['(s)', '(s)', '(h)'], \
#	   'gender':['man', 'man', 'man'], \
#	   'specifier': [None, 'i Ronne', 'i Lönnbo'], \
#	   'other': [None, None, None]
#	   }
#mop = pd.DataFrame(data = mop)  
#
#p1 = {'name': 'JOHAN LARSSON', 'parti':'(s)', \
#		  'gender':'man', 'specifier': 'i Lönnbo'}
#
## Pseudocode:
## fun input dictionary, mop_filtered
## returns id
#
## Compute distance for full name
## If other vraia
#
## Fuzzy
#fuzzy = textdistance.Levenshtein(external=False)
#distance = fuzzy('ab', 'a')
#