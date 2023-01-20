"""
Reformat minister names to form name_name{_name...}_minister_start.
"""
import numpy as np
import pandas as pd

df = pd.read_csv('corpus/ministers.csv')

names = list(map(lambda x: x.replace(' ', '_'), df["name"].str.lower()))

for i in range(len(df)):
	name = names[i]
	start = df.loc[i,"start"][0:4]

	df.loc[i,"id"] = '_'.join([name, 'minister', start])

df.to_csv('corpus/ministers.csv')