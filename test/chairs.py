#!/usr/bin/env python3
"""
Test chars and chair-mp mapping metadata
"""
import pandas as pd
import unittest
import warnings




class ChairHog(Warning):

    def __init__(self, m):
        self.message = f"There following MPs sit in two chairs in {m}:."


    def __str__(self):
        return self.message




class ChairInWrongTimePeriod(Warning):

    def __init__(self, m):
        self.message = f"There is {m}."


    def __str__(self):
        return self.message




class ChairMissingFromRange(Warning):

    def __init__(self, m):
        self.message = f" in {m} is missing."


    def __str__(self):
        return self.message




class ChairOutOfRange(Warning):

    def __init__(self, chamber):
        self.message = f"There are chairs that are not within the acceptable range of the chamber: {chamber}."


    def __str__(self):
        return self.message




class ChairYearOutOfRange(Warning):

    def __init__(self, m):
        self.message = f"In {m} <-- chair is missing."


    def __str__(self):
        return self.message




class DuplicateIDWarning(Warning):

    def __init__(self, m):
        self.message = f"{m}"


    def __str__(self):
        return self.message




class Test(unittest.TestCase):

    #
    #  --->  get var fns
    #  -----------------
    #
    #  read in chairs.csv
    def get_chairs(self):
        return pd.read_csv("corpus/metadata/chairs.csv")


    #  read in chair_mp.csv
    def get_chair_mp(self):
        return pd.read_csv("corpus/metadata/chair_mp.csv")


    #  set max values for each chamber
    def get_max_chair(self):
        max_chair = {
            'ak':233,
            'fk':151,
            'ek':350
        }
        return max_chair


    #  Out of range chair for specific years
    def get_oor_year(self):
        oor_year = {
            '1957':
                    [    # until 1957 -- if year < 1957
                    '814127872a174909bd6ecaeaf59290fe',  # a231
                    'd423710cb9e64b17b93484e120f07e66',  # a232
                    'c77cdeebf789416e98cf8afb05b75a23',  # a233
                    '34ad45b358764a388b53c45ae1ce3681'   # f151
                    ],
            '1959':
                    [    # until 1959 -- elif year < 1959
                    '814127872a174909bd6ecaeaf59290fe',  # a231
                    'd423710cb9e64b17b93484e120f07e66',  # a232
                    'c77cdeebf789416e98cf8afb05b75a23'   # a233
                    ],
            '1961':
                    [    # unitl 1961 -- elif year < 1961
                    'd423710cb9e64b17b93484e120f07e66',  # a232
                    'c77cdeebf789416e98cf8afb05b75a23'   # a233
                    ],
            '1965':
                    [    # until 1965 -- elif year < 1965
                    'c77cdeebf789416e98cf8afb05b75a23'   # a233
                    ],
            '7677':
                    [    # from 197677
                    'af0ebaa9aed64c2d91750aa72651ea74'   # e350
                    ]
        }
        return oor_year


    #
    #  --->  misc fns
    #  --------------
    #
    #  return duplicates in a list
    def get_duplicated_items(self, l):
        seen = set()
        return [_ for _ in l if _ in seen or seen.add(_)]


    #
    #  --->  Test integrity of chairs
    #  -------------------------------------------
    #
    #  check chair IDs are unique
    def test_unique_chair_id(self):
        print("Testing: chairs have unique IDs")
        chairs = self.get_chairs()
        chair_ids = chairs['chair_id'].values
        if len(chair_ids) != len(set(chair_ids)):
            warnings.warn("There's probably a duplicate chair ID.", DuplicateIDWarning)
        self.assertEqual(len(chair_ids), len(set(chair_ids)))


    #  check no chairs are numbered higher than the max chair nr for that chamber
    def test_chair_nrs_in_range(self):
        print("Testing: chairs within max range for chamber")
        chairs = self.get_chairs()
        max_chair = self.get_max_chair()
        for k, v in max_chair.items():
            oor_chairs = chairs.loc[(chairs['chamber'] == k) & (chairs['chair_nr'] > v)]
            if len(oor_chairs) > 0:
                warnings.warn(k, ChairOutOfRange)
            self.assertEqual(len(oor_chairs), 0)


    #
    #  --->  Test integrity of chair_mp
    #  --------------------------------
    #
    #  check chair IDs in chair_mp are the same set as chairs
    def test_chair_id_sets(self):
        print("Testing: chair ids are the same set in chairs.csv and chair_mp.csv")
        chairs = self.get_chairs()
        chair_mp = self.get_chair_mp()
        chair_ids_a = chairs['chair_id'].unique()
        chair_ids_b = chair_mp['chair_id'].unique()
        if set(chair_ids_a) != set(chair_ids_b):
            warnings.warn(ChairIDMismatchW)
        self.assertEqual(len(chair_ids_a), len(chair_ids_b))


    #  check no chairs from tvåkammartiden are used in enkammartid and vice-versa
    def test_chair_chambertime_concurrence(self):
        print("Testing: no chairs from tvåkammartiden are used in enkammartid and vice-versa")
        chairs = self.get_chairs()
        tvok_chairs = chairs.loc[chairs['chamber'] != 'ek', 'chair_id'].unique()
        enk_chairs =  chairs.loc[chairs['chamber'] == 'ek', 'chair_id'].unique()
        chair_mp = self.get_chair_mp()
        tvok_chair_mp_chairs = chair_mp.loc[
            chair_mp['parliament_year'] < 1971,
            'chair_id'
        ].unique()
        enk_chair_mp_chairs = chair_mp.loc[
            chair_mp['parliament_year'] > 1970,
            'chair_id'
        ].unique()
        tkc_in_enkt = False # tvåkammar chair in enkammartid
        ekc_in_tvkt = False # enkammar chair in tvåkammartid
        for c in tvok_chair_mp_chairs:
            if c in enk_chairs:
                ekc_in_tvkt = True
        for c in enk_chair_mp_chairs:
            if c in tvok_chairs:
                tkc_in_enkt = True
        if tkc_in_enkt:
            warnings.warn('tvåkammar chair in enkammartid',ChairInWrongTimePeriod)
        if ekc_in_tvkt:
            warnings.warn('enkammar chair in tvåkammartid', ChairInWrongTimePeriod)
        self.assertFalse(tkc_in_enkt)
        self.assertFalse(ekc_in_tvkt)


    #  check that chairs are within acceptable range for a given year
    #      and that every seat within that range is present at least once
    #      in the chair_mp file (whether filled or not)
    def test_chair_nrs_in_range_for_year(self):
        print("Testing: chairs are within acceptable range for a given year\n     and that every seat within that range is present at least once")
        chairs = self.get_chairs()
        tvok_chairs = chairs.loc[chairs['chamber'] != 'ek', 'chair_id'].unique()
        enk_chairs =  chairs.loc[chairs['chamber'] == 'ek', 'chair_id'].unique()
        chair_mp = self.get_chair_mp()
        oor_year = self.get_oor_year()
        rd_years = chair_mp['parliament_year'].unique()
        OutOfRange = False
        missing_in_R = False
        for y in rd_years:
            year_chair_mp_chairs = chair_mp.loc[
                chair_mp['parliament_year'] == y,
                'chair_id'
            ].unique()
            excludes = []
            if y < 1971:
                if y < 1957:
                    excludes = oor_year['1957']
                elif y < 1959:
                    excludes = oor_year['1959']
                elif y < 1961:
                    excludes = oor_year['1961']
                elif y < 1965:
                    excludes = oor_year['1965']
                if len(excludes) > 0:
                    for x in excludes:
                        if x in year_chair_mp_chairs:
                            OutOfRange = True
                            warnings.warn(f"{y}: {x}", ChairYearOutOfRange)
                if len(tvok_chairs) > len(year_chair_mp_chairs)+len(excludes):
                    for c in tvok_chairs:
                        if c not in year_chair_mp_chairs and c not in excludes:
                            missing_in_R = True
                            warnings.warn(f"{y}: {c}", ChairMissingFromRange)
                elif len(tvok_chairs) > len(year_chair_mp_chairs)+len(excludes):
                    self.assertFalse(True, "¡Sth is super wrong!")
            else:
                if y > 197576 or y == 1980:
                    excludes = oor_year['7677']
                if len(excludes) > 0:
                    for x in excludes:
                        if x in year_chair_mp_chairs:
                            OutOfRange = True
                            warnings.warn(f"{y}: {x}", ChairYearOutOfRange)
                if len(enk_chairs) < len(year_chair_mp_chairs)+len(excludes):
                    for c in tvok_chairs:
                        if c not in year_chair_mp_chairs and c not in excludes:
                            missing_in_R = True
                            warnings.warn(f"{y}: {c}", ChairMissingFromRange)
                elif len(enk_chairs) > len(year_chair_mp_chairs)+len(excludes):
                    self.assertFalse(True, "¡Sth is super wrong!")
        self.assertFalse(OutOfRange)
        self.assertFalse(missing_in_R)


    #
    #  --->  Test integrity of bum to chair mapping
    # ---------------------------------------------
    #
    #  check no single person sits in two places at once
    def test_chair_hogs(self):
        print("Testing: no single person sits in two places at once")
        chair_mp = self.get_chair_mp()
        no_chair_hogs = True
        counter = 0
        ddups = []
        for y in chair_mp['parliament_year'].unique():
            year_chair_mp = chair_mp.loc[chair_mp['parliament_year'] == y]
            mps = year_chair_mp.loc[pd.notnull(year_chair_mp['wiki_id']), 'wiki_id'].values
            if len(mps) > len(set(mps)):
                dups = self.get_duplicated_items(mps)
                warnings.warn(f"{y}: [{', '.join(dups)}]", ChairHog)
                no_chair_hogs = False
                counter += len(dups)
                [ddups.append(_) for _ in dups]
        print(counter, ddups)
        self.assertTrue(no_chair_hogs)


    #  no one sitting in the same chair at the same time
    #      (need specific start-end dates first)


    #
    #  --->  Test coverage
    #  -------------------
    #  all chairs are filled ...
    #      or some percentage of chairs




if __name__ == '__main__':
    unittest.main()
