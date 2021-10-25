"""
Script to impute missing district values (due to wikipedia formatting) for years 1994-1998.
"""
import numpy as np
import pandas as pd

df = pd.read_csv('corpus/members_of_parliament.csv')
df_miss = df[df["district"].isnull()]

districts = pd.read_csv('corpus/districts-1994-1998.csv')
districts["district"] = districts["district"].apply(lambda x: x.split(',')[0])
districts = districts[["name", "district"]]

df_miss = df_miss.drop("district", axis=1)
df_fill = pd.merge(df_miss, districts, on="name", how='left')

df = df[df["district"].notnull()]
df = df.append(df_fill)
df = df.sort_values(by=["start", "chamber", "name"], ignore_index=True)

df.to_csv('corpus/members_of_parliament.csv', index=False)