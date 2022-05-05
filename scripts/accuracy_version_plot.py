import pandas as pd
import matplotlib.pyplot as plt
import argparse
from cycler import cycler


def update_plot(version):
	default_cycler = (cycler(color=['r', 'g', 'b', 'y']) +
	                  cycler(linestyle=['-', '--', ':', '-.']))
	plt.rc('axes', prop_cycle=default_cycler)
	f, ax = plt.subplots()

	df = pd.read_csv('input/accuracy/difference.csv')

	# Overwrite current version
	if len(df[df['version'] == version]) > 1:
		df = df[df['version'] != version]

	# Add current version
	accuracy = pd.read_csv('input/accuracy/upper_bound.csv')
	accuracy = accuracy[['year', 'accuracy_upper_bound']].rename(columns={'accuracy_upper_bound':'accuracy'})
	accuracy['version'] = version
	df = pd.concat([df, accuracy])

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
	return f, ax


def main(args):
	f, ax = update_plot(args.version)
	plt.savefig('input/accuracy/version_plot.png')
	if args.show:
		plt.show()
		plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", "--version", type=str)
    parser.add_argument("-s", "--show", type=str, default="True")
    args = parser.parse_args()
    args.show = False if args.show.lower()[:1] == "f" else True
    main(args)

