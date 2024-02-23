"""
Test that known MP start/end dates that have been manually verified do not change in the metadata.
"""
from datetime import datetime
from .pytestconfig import fetch_config
import json
import pandas as pd
import unittest
import warnings




class DateErrorWarning(Warning):
    def __init__(self, date_error):
        self.message = f"Date Error: {date_error}"

    def __str__(self):
        return self.message



class Test(unittest.TestCase):

    def fetch_known_mandate_dates(self):
        return pd.read_csv("corpus/quality_assessment/mp_start-end_dates/mandate-dates.csv")


    def fetch_mep_meta(self):
        return pd.read_csv("corpus/metadata/member_of_parliament.csv")


    def test_manually_checked_mandates(self):
        mep = self.fetch_mep_meta()
        df = self.fetch_known_mandate_dates()
        now = datetime.now().strftime("%Y%m%d-%H%M")
        config = fetch_config("mandates")
        counter = 0
        rows = []
        cols = ["swerik_id", "date", "type"]
        for i, r in df.iterrows():
            fil = mep.loc[(mep['swerik_id'] == r["swerik_id"]) & (mep[r["type"].lower()] == r['date'])]
            if fil.empty:
                counter += 1
                rows.append([r["swerik_id"], r["date"], r["type"]])
                warnings.warn(f"({r['type']}): {r['date']}, {r['swerik_id']}" , DateErrorWarning)
        if config:
            if config['write_errors'] and len(rows) > 0:
                out = pd.DataFrame(rows, columns=cols)
                out.to_csv(f"{config['write_path']}mandates-test_{now}.csv", index=False)


        self.assertEqual(counter, 0)




if __name__ == '__main__':
    unittest.test()
