"""
Script do detect incorrectly formatted names.
"""
import numpy as np
import pandas as pd
import string

upper = list(string.ascii_uppercase)
upper.extend(['Å','Ä','Ö'])

df = pd.read_csv('corpus/members_of_parliament.csv')
lst = []
for i in range(len(df)):
	problem = 0
	name = df.loc[i,"name"]
	name_split = name.split()

	for j in name_split:
		if j[0] not in upper and j not in ['af', 'von', 'de', 'der']:
			problem = 1
	if problem == 1:
		lst.append(df.loc[i])

pd.DataFrame(lst).to_csv('special_names.csv',index=False)

