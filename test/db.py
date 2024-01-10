"""
throw ERROR on inconsistencies on our side

WARN on upstream errors
"""
from lxml import etree
from pathlib import Path
from pyriksdagen.db import load_metadata
from pyriksdagen.utils import protocol_iterators, get_doc_dates
import pandas as pd
import unittest
import warnings
import yaml



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
		missing.to_csv(f"corpus/_quality_assessment/unittest_failure/missing_{df_name}.csv", sep=';', index=False)


	def write_integrity_error(self, df_name, error_df):
		# todo: add path var to put unit test results in the right directory
		error_df.to_csv(f"corpus/quality_assessment/known_mps/integrity-error_{df_name}.csv", sep=';', index=False)	


	def test_government(self):
		columns = ["start", "end"]
		df_name = "government"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, columns)		
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_member_of_parliament(self):
		columns = ["swerik_id", "start", "end"]
		df_name = "member_of_parliament"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, columns)		
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_minister(self):
		df_name = "minister"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, None)
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_party_affiliation(self):
		columns = ["swerik_id", "start", "end"]
		df_name = "party_affiliation"
		df, df_unique, df_duplicate = self.get_duplicates(df_name, columns)
		
		if len(df) != len(df_unique):
			warnings.warn(str(df_duplicate), DuplicateWarning)
		
		df, df_unique, df_duplicate = self.get_duplicates(df_name, None)
		self.assertEqual(len(df), len(df_unique), df_duplicate)


	def test_person(self):
		columns = ["swerik_id"]
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
		swerik_id_issue = emil[(emil['swerik_id'].isna()) | (emil['swerik_id'] == "Q00FEL00")]
		birthdate_NA = emil[(emil['born'].isna()) | (emil['born'] == "Multival")]

		if not swerik_id_issue.empty:
			warnings.warn(f'{len(swerik_id_issue)} swerik_id issues', CatalogIntegrityWarning)
			if running_local:
				self.write_integrity_error("wiki-id-issue", swerik_id_issue)

		if not birthdate_NA.empty:
			warnings.warn(f"{len(birthdate_NA)} birthdates missing", CatalogIntegrityWarning)
			if running_local:
				self.write_integrity_error("missing-birthdate", birthdate_NA)

		self.assertEqual(len(swerik_id_issue), 0, swerik_id_issue)
		self.assertEqual(len(birthdate_NA), 0, birthdate_NA)


	def test_cf_emil_person(self):
		df_name = "person"
		df = self.get_meta_df(df_name)
		emil = self.get_emil()
		missing_persons = pd.DataFrame(columns=list(emil.columns))

		for i, row in emil.iterrows():
			if row['swerik_id'] not in df['swerik_id'].unique():
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
			if row['swerik_id'] not in df['swerik_id'].unique():
				missing_names.loc[len(missing_names)] = row

		if not missing_names.empty:
			warnings.warn(str(missing_names), MissingNameWarning)
			if running_local:
				self.write_missing(df_name, missing_names)

		self.assertTrue(missing_names.empty, missing_names)


	def test_cf_known_iorter_metadata(self):
		df_name = "location_specifier"
		df = self.get_meta_df(df_name)
		iorter = pd.read_csv("corpus/quality_assessment/known_iorter/known_iorter.csv", sep=";")
		missing_locations = pd.DataFrame(columns=list(iorter.columns))

		for i, row in iorter.iterrows():
			filtered = df.loc[(df["swerik_id"] == row["swerik_id"]) & (df["location"] == row["iort"])]
			if len(filtered) < 1:
				missing_locations.loc[len(missing_locations)] = row

		if not missing_locations.empty:
			warnings.warn(str(missing_locations), MissingLocationWarning)
			if running_local:
				self.write_missing(df_name, missing_locations)

		self.assertTrue(missing_locations.empty, missing_locations)


	def test_cf_emil_member(self):
		df_name = "member_of_parliament"
		df = self.get_meta_df(df_name)
		emil = self.get_emil()
		missing_members = pd.DataFrame(columns=list(emil.columns))

		for i, row in emil.iterrows():
			if row['swerik_id'] not in df['swerik_id'].unique():
				missing_members.loc[len(missing_members)] = row

		if not missing_members.empty:
			warnings.warn(str(missing_members), MissingMemberWarning)
			if running_local:
				self.write_missing(df_name, missing_members)

		self.assertTrue(missing_members.empty, missing_members)

	@unittest.skip("Skipping party_affiliation test")
	def test_cf_emil_party(self):
		df_name = "party_affiliation"
		df = self.get_meta_df(df_name)
		emil = self.get_emil()
		missing_parties = pd.DataFrame(columns=list(emil.columns))

		for i, row in emil.iterrows():
			if row['swerik_id'] not in df['swerik_id'].unique():
				missing_parties.loc[len(missing_parties)] = row

		if not missing_parties.empty:
			warnings.warn(str(missing_parties), MissingPartyWarning)
			if running_local:
				self.write_missing(df_name, missing_parties)

		self.assertTrue(missing_parties.empty, missing_parties)

	def test_session_dates(self):
		dates_df = pd.read_csv("corpus/quality_assessment/session-dates/session-dates.csv", sep=';')
		protocols = sorted(list(protocol_iterators("corpus/protocols/", start=1867, end=2022)))
		date_counter = 0
		for protocol in protocols:
		    #print(protocol)
		    #if protocol not in ignore:
		    E, dates = get_doc_dates(protocol)
		    self.assertFalse(E, f"A docDate 'when' attr doesn't match its text value.")
		    for d in dates:
		        date_counter += 1
		        self.assertTrue(((dates_df['protocol'] == protocol) & (dates_df['date'] == d)).any(), f"{d} not in list of known dates for {protocol}")
		if len(dates_df)-date_counter > 0:
		    rows = []
		    for i, r in dates_df.iterrows():
		        tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
		        xml_ns = "{http://www.w3.org/XML/1998/namespace}"
		        parser = etree.XMLParser(remove_blank_text=True)
		        root = etree.parse(r['protocol'], parser).getroot()
		        d = r["date"]
		        date_match = root.findall(f'{tei_ns}docDate[@when="{d}"]')
		        self.assertEqual(len(date_match), 1, f"[{r['protocol']}, {r['date']}] not in the known session dates csv")




if __name__ == '__main__':
	unittest.main()
