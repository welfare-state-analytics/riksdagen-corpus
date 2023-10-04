#!/usr/bin/env python3
import matplotlib.pyplot as plt
import os
import pandas as pd




here = os.path.dirname(__file__)




def main():

    skip = [
        'prot-1909----reg-01.xml',
        'prot-1909----reg-02.xml',
        'prot-197677--.xml',
        'prot-197778--.xml',
        ] # these were "test" protocols & break code :|

    df = pd.read_csv(f"{here}/test-result.csv", sep=';') # output of MP frequency pre-unittest

    for s in skip:
        df.drop(df[df['protocol']==s].index, inplace=True)

    df['parliament_year'] = df['parliament_year'].apply(lambda x: x[:4])
    pyears = df['parliament_year'].unique()

    rows = []
    for py in pyears:
        rows.append([py, df.loc[df['parliament_year']==py, "ratio"].mean()])

    newdf = pd.DataFrame(rows, columns=["Parliament_starting_in", "Avg_ratio"])
    newdf.set_index("Parliament_starting_in", inplace=True)

    newdf.plot.line()
    plt.savefig(f"{here}/_MP_db_coverage-vs-baseline.pdf", format='pdf', dpi=300)
    #plt.show()




if __name__ == '__main__':
    main()
