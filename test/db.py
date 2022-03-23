import unittest
import pandas as pd
import yaml
from pyriksdagen.db import load_metadata

class Test(unittest.TestCase):

    # Test that each column in the MP DB contains at least 95% valid values
    def test_mp_db(self):        
        _, mp_db, *_, = load_metadata()
        #mp_db = pd.read_csv("corpus/members_of_parliament.csv")

        total = len(mp_db)
        mp_db_columns = mp_db.columns
        print("Columns:", ", ".join(list(mp_db_columns)))
        mp_db_columns = dict(name=1.0,
                            party=0.95,
                            district=0.95,
                            chamber=0.95,
                            id=1.0,
                            gender=0.95)
        print("Test:", ", ".join(list(mp_db_columns)))
        for column, percentage in mp_db_columns.items():
            column_count = len(mp_db[mp_db[column].isnull()])
            valid_ratio = 1. - (column_count / total)
            print(column, valid_ratio)
            self.assertGreaterEqual(valid_ratio, percentage)

if __name__ == '__main__':
    unittest.main()
