#!/usr/bin/env python3
from plotnine import *
import os
import pandas as pd
import pandas.api.types as pdtypes
import matplotlib.pyplot as plt


here = os.path.dirname(__file__)

def main():
    mps = pd.read_csv("corpus/metadata/member_of_parliament.csv")
    person = pd.read_csv("corpus/metadata/person.csv")

    D = {}
    years = list(range(1867,2027))
    for y in years:
        D[y] = []

    for i,r in mps.iterrows():
        start = None
        end = None
        if pd.notnull(r['start']):
            start = int(str(r['start'])[:4])
        if pd.notnull(r['end']):
            end = int(str(r['end'])[:4])
        if start:
            if end == None:
                D[start].append(r['wiki_id'])
            else:
                for y in range(start, end+1):
                    D[y].append(r['wiki_id'])


    gender_rows = []
    gender_cols = ["year", "male", "female", "unspec"]
    age_rows = []
    age_cols = ["year", "age"]
    age_flags = []


    for k, v in D.items():
        if k < 2023:
            print('--->', k)
            male = 0
            female = 0
            unspec = 0
            ages = []
            for wiki_id in v:
                fpers = person.loc[person['wiki_id'] == wiki_id].copy()
                if len(fpers) > 0:
                    genders = fpers['gender'].unique()
                    if 'man' in genders and 'woman' in genders:
                        print("trans?")
                        unspec += 1
                    elif 'man' in genders:
                        male += 1
                    elif 'woman' in genders:
                        female += 1
                    else:
                        unspec += 1
                    try:
                        dob = fpers.loc[pd.notnull(fpers['born']), 'born'].unique()
                    except:
                        dob = None
                    if len(dob) > 0:
                        xyz = k-int(str(dob[0])[:4])
                        if xyz > 10:
                            age_rows.append([k, xyz])
                            if xyz < 25:
                                print(k, wiki_id, xyz)
                                print(dob)
                                age_flags.append(wiki_id)
                        else:
                            age_flags.append(wiki_id)

                else:
                    print(f"ERRRMAGERD, no person {wiki_id} in person.csv")
            gender_rows.append([k, male, female, unspec])


    age_df = pd.DataFrame(age_rows, columns=age_cols)
    age_df.to_csv(f"{here}/_age_df.csv", sep=';', index=False)
    with open(f"{here}/_age_flagged.csv", "w+") as outf:
        [outf.write(f"{_}"+"\n") for _ in set(age_flags)]

    gender_df = pd.DataFrame(gender_rows, columns=gender_cols)
    gender_df.to_csv(f"{here}/_gender_df.csv", sep=';', index=False)

    print(age_df, gender_df)




if __name__ == '__main__':
    main()
