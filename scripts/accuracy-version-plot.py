import pandas as pd
import matplotlib.pyplot as plt
from cycler import cycler

default_cycler = (cycler(color=['r', 'g', 'b', 'y']) +
                  cycler(linestyle=['-', '--', ':', '-.']))
plt.rc('axes', prop_cycle=default_cycler)
f, ax = plt.subplots()

df = pd.read_csv('input/acc-diff.csv')
version = sorted(list(set(df['version'])), reverse=True)

for v in version:
	dfv = df.loc[df['version'] == v]
	x = dfv['year'].tolist()
	y = dfv['accuracy'].tolist()
	x, y = zip(*sorted(zip(x,y),key=lambda x: x[0]))

	plt.plot(x, y)

plt.title('Estimated accuracy for identification of speech-maker')
plt.legend(version, loc ="upper left")
ax.set_xlabel('Year')
ax.set_ylabel('Accuracy')

plt.show()
plt.close()