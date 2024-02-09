#!/usr/bin/env python3
import argparse
import matplotlib.pyplot as plt
import os, re
import pandas as pd
import pandas.api.types as pdtypes




here = os.path.dirname(__file__)


def plot(df):
    versions = df.columns
    versions = sorted(set(versions), key=lambda v: list(map(int, v[1:].split('.'))), reverse=True)
    versions = versions[:4]
    df = df[versions]
    p, a = plt.subplots()
    a.plot(df)
    lines = a.get_children()
    for i, l in enumerate(lines, -len(lines)):
        l.set_zorder(abs(i))
    a.axhline(y=1, color='green', linestyle='--', linewidth=1, label='_nolegend_')
    a.set_title("Ratio: members of parliament to seats")
    a.legend(versions, loc ="upper left")
    p.savefig(f"{here}/figures/mp-coverage/mp-coverage-ratio.png")




def main(args):

    skip = [
        'prot-1909----reg-01.xml',
        'prot-1909----reg-02.xml',
        'prot-197677--.xml',
        'prot-197778--.xml',
        ] # these were "test" protocols & break code :|
    print("plotting quality of MP coverage")
    df = pd.read_csv(f"{here}/figures/mp-coverage/_test-result.csv", sep=';') # output of MP frequency pre-unittest
    mp_coverage_df = pd.read_csv(f"{here}/figures/mp-coverage/mp-coverage.csv")
    mp_coverage_df.set_index('year', inplace=True)

    for s in skip:
        df.drop(df[df['protocol']==s].index, inplace=True)

    df['parliament_year'] = df['parliament_year'].apply(lambda x: int(x[:4]))
    pyears = df['parliament_year'].unique()

    D = {}

    for py in pyears:
        D[py] = df.loc[df['parliament_year']==py, "ratio"].mean()

    mp_coverage_df[args.version] = D

    mp_coverage_df.to_csv(f"{here}/figures/mp-coverage/mp-coverage.csv")


    plot(mp_coverage_df)


    """
    p, a = plt.subplots()
    plt.rcParams.update({'font.size': 14})
    a.plot(newdf['Avg_ratio'])
    a.spines['top'].set_visible(False)
    a.spines['right'].set_visible(False)
    a.title("Ratio: members of parliament to seats")
    p.axhline(y=1, color='green', linestyle='--', linewidth=1, label='_nolegend_')
    p.savefig(f"{here}/_MP_db_coverage-vs-baseline.pdf", format='pdf', dpi=300)
    #plt.show()
    """



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", "--version", type=str)
    args = parser.parse_args()
    exp = re.compile(r"v([0-9]+)([.])([0-9]+)([.])([0-9]+)(b|rc)?([0-9]+)?")
    if exp.search(args.version) is None:
        print(f"{args.version} is not a valid version number. Exiting")
        exit()
    else:
        args.version = exp.search(args.version).group(0)
        main(args)
