#!/usr/bin/env python3
import matplotlib.pyplot as plt
import os
import pandas as pd
import pandas.api.types as pdtypes




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
    newdf.to_csv(f"{here}/_MP-coverage-ratios.csv", sep=';')




    newdf = None

    newdf = pd.read_csv(f"{here}/_MP-coverage-ratios.csv", sep=';')
    newdf.set_index("Parliament_starting_in", inplace=True)
    print(newdf)

    p, a = plt.subplots()
    plt.rcParams.update({'font.size': 14})
    a.plot(newdf['Avg_ratio'])
    a.spines['top'].set_visible(False)
    a.spines['right'].set_visible(False)
    plt.title("Ratio: members of parliament to seats")
    plt.axhline(y=1, color='green', linestyle='--', linewidth=1, label='_nolegend_')
    #print(a.xaxis.get_ticklabels())
    #for ix, label in enumerate(a.xaxis.get_ticklabels(), start=1):
    #    lab = int(label.get_text())
    #    if lab%20 != 0:
    #        label.set_visible(False)

    plt.savefig(f"{here}/_MP_db_coverage-vs-baseline.pdf", format='pdf', dpi=300)
    #plt.show()




if __name__ == '__main__':
    main()
