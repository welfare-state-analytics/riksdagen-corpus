"""
throw ERROR on inconsistencies on our side

WARN on upstream errors
"""
import unittest
import pandas as pd
import yaml
from pyriksdagen.db import load_metadata
from pathlib import Path
import warnings

# OBS. set to False before commit / push!
# If True, the script attempts to write
# missing-data dfs to csv files.
running_local = False
####
###
##
#


class DuplicateWarning(Warning):
	def __init__(self, duplicate_df):
		self.message = f"Following duplicates found\n{duplicate_df}"
	
	def __str__(self):
		return self.message




class MissingPersonWarning(Warning):
	def __init__(self, missing_persons):
		self.message = f"The following people are missing from the corpus metadata (person.csv)\n{missing_persons}"

	def __str__(self):
		return self.message
	



class MissingNameWarning(Warning):
	def __init__(self, missing_names):
		self.message = f"The following people are missing from the corpus metadata (name.csv)\n{missing_names}"

	def __str__(self):
		return self.message




class MissingLocationWarning(Warning):
	def __init__(self, missing_location):
		self.message = f"The following people are missing from the corpus metadata (location_specifier.csv)\n{missing_location}"

	def __str__(self):
		return self.message




class MissingMemberWarning(Warning):
	def __init__(self, missing_member):
		self.message = f"The following people are missing members (member_of_parliament.csv)\n{missing_member}"

	def __str__(self):
		return self.message




class MissingPartyWarning(Warning):
	def __init__(self, missing_location):
		self.message = f"The following people are missing from the corpus metadata (party_affiliation.csv)\n{missing_location}"

	def __str__(self):
		return self.message



class CatalogIntegrityWarning(Warning):
	def __init__(self, issue):
		self.message = f"There's an integrity issue --| {issue} |-- maybe fix that."

	def __str__(self):
		return self.message 


	
class Test(unittest.TestCase):

	def get_duplicates(self, df_name, columns):
		p = Path(".") / "corpus" / "metadata"
		path = p / f"{df_name}.csv"
		df = pd.read_csv(path)
		
		df_duplicate = df[df.duplicated(columns, keep=False)]
		df_unique = df.drop_duplicates(columns)
		return df, df_unique, df_duplicate


	def get_emil(self):
		emil_df = pd.read_csv('corpus/quality_assessment/known_mps/known_mps_catalog.csv', sep=';')
		return emil_df


	def get_meta_df(self, df_name):
		p = Path(".") / "corpus" / "metadata"
		path = p / f"{df_name}.csv"
		df = pd.read_csv(path)
		return df


	def write_missing(self, df_name, missing):
		missing.to_csv(f"corpus/quality_assessment/known_mps/missing_{df_name}.csv", sep=';', index=False)


	def write_integrity_error(self, df_name, error_df):
		error_df.to_csv(f"corpus/quality_assessment/known_mps/integrity-error_{df_name}.csv", sep=';', index=False)	


	def test_government(self):
		columns = ["start", "end"]
		df_name = "government"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, columns)		
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_member_of_parliament(self):
		columns = ["wiki_id", "start", "end"]
		df_name = "member_of_parliament"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, columns)		
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_minister(self):
		df_name = "minister"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, None)
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_party_affiliation(self):
		columns = ["wiki_id", "start", "end"]
		df_name = "party_affiliation"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, columns)
		
		if len(df) != len(df_unique):
			warnings.warn(str(df_duplicate), DuplicateWarning)
		
		df, df_unique, df_duplicate = self.get_duplicates(df_name, None)
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_person(self):
		columns = ["wiki_id"]
		df_name = "person"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, columns)		
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_speaker(self):
		columns = ["start", "end", "role"]
		df_name = "speaker"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, columns)
		
		if len(df) != len(df_unique):
			warnings.warn(str(df_duplicate), DuplicateWarning)

		df, df_unique, df_duplicate = self.get_duplicates(df_name, None)
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_twitter(self):
		df_name = "twitter"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, None)
		
		if len(df) != len(df_unique):
			warnings.warn(str(df_duplicate), DuplicateWarning)
		
		df, df_unique, df_duplicate = self.get_duplicates(df_name, None)
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_emil_integrity(self):
		emil = self.get_emil()
		wiki_id_issue = emil[(emil['wiki_id'].isna()) | (emil['wiki_id'] == "Q00FEL00")]
		birthdate_NA = emil[(emil['born'].isna()) | (emil['born'] == "Multival")]

		if not wiki_id_issue.empty:
			warnings.warn(f'{len(wiki_id_issue)} wiki_id issues', CatalogIntegrityWarning)
			if running_local:
				self.write_integrity_error("wiki-id-issue", wiki_id_issue)

		if not birthdate_NA.empty:
			warnings.warn(f"{len(birthdate_NA)} birthdates missing", CatalogIntegrityWarning)
			if running_local:
				self.write_integrity_error("missing-birthdate", birthdate_NA)

		self.assertEqual(len(wiki_id_issue), 0, wiki_id_issue)
		self.assertEqual(len(birthdate_NA), 0, birthdate_NA)


	def test_cf_emil_person(self):
		df_name = "person"
		df = self.get_meta_df(df_name)
		emil = self.get_emil()
		missing_persons = pd.DataFrame(columns=list(emil.columns))

		for i, row in emil.iterrows():
			if row['wiki_id'] not in df['wiki_id'].unique():
				missing_persons.loc[len(missing_persons)] = row

		if not missing_persons.empty:
			warnings.warn(str(missing_persons), MissingPersonWarning)
			if running_local:
				self.write_missing(df_name, missing_persons)

		self.assertTrue(missing_persons.empty, missing_persons)


	def test_cf_emil_name(self):
		df_name = "name"
		df = self.get_meta_df(df_name)
		emil = self.get_emil()
		missing_names = pd.DataFrame(columns=list(emil.columns))

		for i, row in emil.iterrows():
			if row['wiki_id'] not in df['wiki_id'].unique():
				missing_names.loc[len(missing_names)] = row

		if not missing_names.empty:
			warnings.warn(str(missing_names), MissingNameWarning)
			if running_local:
				self.write_missing(df_name, missing_names)

		self.assertTrue(missing_names.empty, missing_names)


	def test_cf_emil_location(self):
		df_name = "location_specifier"
		df = self.get_meta_df(df_name)
		emil = self.get_emil()
		missing_locations = pd.DataFrame(columns=list(emil.columns))

		for i, row in emil.iterrows():
			if row['wiki_id'] not in df['wiki_id'].unique():
				missing_locations.loc[len(missing_locations)] = row

		if not missing_locations.empty:
			warnings.warn(str(missing_locations), MissingLocationWarning)
			if running_local:
				self.write_missing(df_name, missing_locations)

		#self.assertTrue(missing_locations.empty, missing_locations)


	def test_cf_emil_member(self):
		df_name = "member_of_parliament"
		df = self.get_meta_df(df_name)
		emil = self.get_emil()
		missing_members = pd.DataFrame(columns=list(emil.columns))

		for i, row in emil.iterrows():
			if row['wiki_id'] not in df['wiki_id'].unique():
				missing_members.loc[len(missing_members)] = row

		if not missing_members.empty:
			warnings.warn(str(missing_members), MissingMemberWarning)
			if running_local:
				self.write_missing(df_name, missing_members)

		self.assertTrue(missing_members.empty, missing_members)


	def test_cf_emil_party(self):
		df_name = "party_affiliation"
		df = self.get_meta_df(df_name)
		emil = self.get_emil()
		missing_parties = pd.DataFrame(columns=list(emil.columns))

		for i, row in emil.iterrows():
			if row['wiki_id'] not in df['wiki_id'].unique():
				missing_parties.loc[len(missing_parties)] = row

		if not missing_parties.empty:
			warnings.warn(str(missing_parties), MissingPartyWarning)
			if running_local:
				self.write_missing(df_name, missing_parties)

		#self.assertTrue(missing_parties.empty, missing_parties)




if __name__ == '__main__':
	unittest.main()
