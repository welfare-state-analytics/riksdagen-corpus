"""
(OLD?) New version of matching algorithm with fuzzy matching implemented.

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
import json
import re
from progressbar import progressbar
from itertools import combinations
import random
import argparse

from pyriksdagen.segmentation import (
    intro_to_dict
)
from pyriksdagen import match_mp

def main(args):
	# Import mp_db
	mop = pd.read_csv(args.mop)
	mop["name"] = match_mp.clean_names(mop["name"])

	# Import patterns
	patterns = pd.read_json(args.patterns, orient="records", lines=True)
	expressions = []
	for _, pattern in patterns.iterrows():
	    exp, t = pattern["pattern"], pattern["type"]
	    exp = re.compile(exp)
	    expressions.append((exp, t))

	# Import and clean detected intros
	with open(args.party_map) as f:
	  party_map = json.load(f)
	data = pd.read_csv(args.intros).sort_values(by="protocol").reset_index()
	results = list(map(lambda x: intro_to_dict(x, expressions), data["intro"]))
	data["other"] = list(map(lambda x: x.get("other", ""), results))
	data["gender"] = list(map(lambda x: x.get("gender", ""), results))
	data["party"] = list(map(lambda x: x.get("party", ""), results))
	data["party_abbrev"] = list(map(lambda x: party_map.get(x, ""), data["party"]))
	data["specifier"] = list(map(lambda x: x.get("specifier", ""), results))
	data["name"] = list(map(lambda x: x.get("name", ""), results))
	data["name"] = match_mp.clean_names(data["name"])

	# Create objects to match by
	variables = ['party_abbrev', 'specifier', 'name']
	mop_variables = sum([list(map(list, combinations(variables, i))) for i in range(len(variables) + 1)], [])[1:]

	# Same procedure for statskalendern
	sk = pd.read_csv(args.sk)
	sk["name"] = match_mp.clean_names(sk["name"])
	sk_variables = [v for v in variables if v in list(sk.columns)]
	sk_maxyear = max(sk["year"])
	# Fake ids for testing
	sk["id"] = list(map(lambda x: str(x), list(range(len(sk)))))

	# Shuffle protocols for debugging
	protocols = sorted(list(set(data["protocol"])))
	random.seed(int(args.seed))
	random.shuffle(protocols)

	matching_funs = [match_mp.in_name, match_mp.fuzzy_name, match_mp.subnames_in_mpname, match_mp.mpsubnames_in_name,
					 match_mp.firstname_lastname, match_mp.two_lastnames, match_mp.firstname_lastname_reversed]

	protocols = protocols[:int(args.n_protocols)]
	output = []

	for protocol in progressbar(protocols):
		df = data[data["protocol"] == protocol]
		year, chamber = df.iloc[0][["year", "chamber"]] # Weird hacky syntax
		mp_db = mop[(mop["start"] <= year) & (mop["end"] >= year)]
		
		if year < 1971:
			mp_db_split = mp_db[mp_db["chamber"] == chamber]
		else:
			mp_db_split = mp_db

		for i,row in df.iterrows():
			match, reason, person, fun = match_mp.match_mp(row, mp_db_split, mop_variables, matching_funs)

			# if no match in bichameral era, check other chamber
			if match == 'unknown' and year < 1971:
				mp_db_rest = mp_db[mp_db["chamber"] != chamber]
				match, reason, person, fun = match_mp.match_mp(row, mp_db_rest, mop_variables, matching_funs)

			if match == 'unknown' and year <= sk_maxyear:
				sk_db = sk[sk["year"] == year]
				match, reason, person, fun = match_mp.match_mp(row, sk_db, sk_variables, matching_funs)
				if match != 'unknown':
					reason += '_sk'

			output_data = list(row[["name", "gender", "party", "party_abbrev", "specifier", "other", "intro"]])
			output_data.extend([match, reason, fun, year, chamber, protocol])
			output.append(output_data)
			

	output = pd.DataFrame(output, columns = ["name", "gender", "party", "party_abbrev", "specifier", "other", "intro",\
											 "match", "reason", "fun", "year", "chamber", "protocol"])
	output.to_csv('matched-output.csv', index=False)

	print('____________________________________')
	print(f'Acc upper bound: {1 - len(output[output["match"] == "unknown"]) / len(output)}%')
	print('____________________________________')
	for reason in list(set(output["reason"])):
		print(f'Reason {reason}: {len(output[output["reason"] == reason]) / len(output)}%')
	print('____________________________________')
	for fun in matching_funs:
		print(f'Fun {fun}: {len(output[output["fun"] == str(fun)]) / len(output)}%')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--n_protocols", type=str, default=10**10, help="Number of protocols")
	parser.add_argument("--seed", type=str, default=123, help="Number of protocols")

	parser.add_argument("--mop", type=str, default="corpus/members_of_parliament.csv", help="Path to mop")
	parser.add_argument("--sk", type=str, default="../riksdagen-ocr/metadata/mps.csv", help="Path to statscalender")
	parser.add_argument("--patterns", type=str, default="input/segmentation/detection.json", help="Path to patterns")
	parser.add_argument("--party_map", type=str, default="corpus/party_mapping.json", help="Path to party_mapping")
	parser.add_argument("--intros", type=str, default="output.csv", help="Path detected intros")

	args = parser.parse_args()

	main(args)