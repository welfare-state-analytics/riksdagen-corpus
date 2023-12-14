"""
Draw a graph of the introduction mapping accuracy estimate
"""
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from cycler import cycler
import re


def update_plot(version):
    colors = list('bgrcmyk')
    default_cycler = (cycler(color=colors) +
                      cycler(linestyle=(['-', '--', ':', '-.']*2)[:len(colors)]))
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

    # Save new values
    df.to_csv('input/accuracy/difference.csv', index=False)


    # prepend 'v' to version nr if not already there
    df['version'] = df['version'].apply(lambda s: s if s.startswith('v') else f'v{s}')
    # sort versions 
    #    (a) first by patch, then minor, then major and 
    #    (b) by int (10, 9 ... 2, 1) not str ('9' ... '2', '10', '1')
    version = sorted(list(set(df['version'])), key=lambda s: list(map(int, s[1:].split('.'))), reverse=True)
    for v in version[:6]:
        dfv = df.loc[df['version'] == v]
        x = dfv['year'].tolist()
        y = dfv['accuracy'].tolist()
        x, y = zip(*sorted(zip(x,y),key=lambda x: x[0]))
        plt.plot(x, y, linewidth=1.75)

    plt.title('Estimated accuracy for identification of speaker')
    plt.legend(version, loc ="upper left")
    ax.set_xlabel('Year')
    ax.set_ylabel('Accuracy')
    return f, ax

def main(args):
    f, ax = update_plot(args.version)
    plt.savefig('input/accuracy/version_plot.png', dpi=300)
    if args.show:
        plt.show()
        plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", "--version", type=str)
    parser.add_argument("-s", "--show", type=str, default="True")
    args = parser.parse_args()
    args.show = False if args.show.lower()[:1] == "f" else True
    exp = re.compile(r"v([0-9]+)([.])([0-9]+)([.])([0-9]+)(b|rc)?([0-9]+)?")
    if exp.search(args.version) is None:
        print(f"{args.version} is not a valid version number. Exiting")
        exit()
    else:
        args.version = exp.search(args.version).group(0)
        main(args)

