#!/usr/bin/env python3
"""
Plots MP coverage per year/chamber/session
"""
import argparse, os, re
import pandas as pd
import matplotlib.pyplot as plt



here = os.path.dirname(__file__)



def main(args):
    print("plotting MP coverage")
    df = pd.read_csv(f"{here}/figures/mp-coverage/_test-result.csv", sep=";")

    year = df['parliament_year'].unique()
    #print(year)
    plt.figure(figsize=(38.20, 10.80))

    fk = df.loc[df["chamber"] == "fk"]
    plt.plot(fk['parliament_year'], fk['baseline_N'], label = "First Chamber baseline")
    for ix, y in enumerate(fk['parliament_year'].unique()):
        col = "blue"
        plt.boxplot(fk.loc[fk['parliament_year'] == y, "N_MP"].tolist(), positions=[ix],
            manage_ticks=False,
            boxprops=dict(color=col),
            flierprops=dict(markeredgecolor=col, marker=".", markersize=3),
            whiskerprops=dict(color=col),
            capprops=dict(color=col),
            medianprops=dict(color="red")
        )



    ak = df.loc[df["chamber"] == "ak"]
    plt.plot(ak['parliament_year'], ak['baseline_N'], label = "Second Chamber baseline")
    c = 0
    for ix, y in enumerate(ak['parliament_year'].unique()):
        c += 1
        col = "orange"
        plt.boxplot(ak.loc[ak['parliament_year'] == y, "N_MP"].tolist(), positions=[ix],
            manage_ticks=False,
            boxprops=dict(color=col),
            flierprops=dict(markeredgecolor=col, marker=".", markersize=3),
            whiskerprops=dict(color=col),
            capprops=dict(color=col),
            medianprops=dict(color="red")
        )


    ek = df.loc[df["chamber"] == "ek"]
    plt.plot(ek['parliament_year'], ek['baseline_N'], label = "Unicameral baseline")
    for ix, y in enumerate(ek['parliament_year'].unique(), start = c):
        col = "green"
        plt.boxplot(ek.loc[ek['parliament_year'] == y, "N_MP"].tolist(), positions=[ix],
            manage_ticks=False,
            boxprops=dict(color=col),
            flierprops=dict(markeredgecolor=col, marker=".", markersize=3),
            whiskerprops=dict(color=col),
            capprops=dict(color=col),
            medianprops=dict(color="red")
        )

    plt.title(f"MEP Coverage, relativee to baseline values ({args.version})", fontsize="40")
    plt.legend(fontsize="35")
    plt.xticks(range(0, len(year), 5), year[::5], rotation = 90, fontsize=25)
    plt.yticks(fontsize=20)
    #plt.xticks(rotation=90)
    plt.savefig(f"{here}/figures/mp-coverage/mp-coverage.png",
        dpi=100,
        bbox_inches='tight',
        pad_inches = 0.2
    )



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

