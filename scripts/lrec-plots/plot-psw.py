#!/usr/bin/env python3
import matplotlib.pyplot as plt
import os
import pandas as pd




here = os.path.dirname(__file__)




def main():
    df = pd.read_csv(f"{here}/_psw-counts.csv", sep=';')
    print(df)
    df.set_index('year', inplace=True)
    fig, (ax1, ax2, ax3) = plt.subplots(3)#, sharex=True)
    ax1.plot(df['prot'])
    ax1.set_title("Records")
    ax1.set_ylim(bottom=0)
    ax2.plot(df['intros'])
    ax2.set_title("Speeches")
    ax2.set_ylim(bottom=0)
    ax3.plot(df['words'])
    ax3.set_title("Words")
    ax3.set_ylim(bottom=0)
    ax3.ticklabel_format(useOffset=False, style='plain')
    for a in [ax1, ax2, ax3]:
        a.spines['top'].set_visible(False)
        a.spines['right'].set_visible(False)
    fig.set_size_inches(7,6)
    fig.tight_layout()
    plt.savefig(f"{here}/_prot-intro-word.pdf", format="pdf", dpi=300)
    #plt.show()




if __name__ == '__main__':
    main()
