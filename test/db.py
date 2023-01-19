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

class DuplicateWarning(Warning):
    def __init__(self, duplicate_df):
        self.message = f"Following duplicates found\n{duplicate_df}"
    
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
        
        if len(df) != len(df_unique):
            warnings.warn(str(df_duplicate), DuplicateWarning)

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

if __name__ == '__main__':
    unittest.main()
