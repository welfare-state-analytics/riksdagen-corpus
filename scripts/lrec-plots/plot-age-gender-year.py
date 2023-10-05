#!/usr/bin/env python3
from plotnine import *
import matplotlib.pyplot as plt
import os
import pandas as pd
import pandas.api.types as pdtypes




here = os.path.dirname(__file__)




def div(a,b):
    return a/b




def add(a,b,c):
    for _ in [a,b,c]:
        if pd.isnull(_):
            _=0
    return a+b+c




def plot_boxes(age_df):
    ppplot = ggplot(age_df, aes('year', 'age')) + geom_boxplot() + \
            xlab("Years") + \
            ylab("Age") + \
            ggtitle("ages/year")
    ppplot.save(filename=f"{here}/_boxplots.png",
       dpi=300,
       height=25,
       width=25
    )




def plot_gen(gender_df):
    gplt = gender_df.plot(kind='bar', stacked=True)
    gplt.legend(["Male", "Female"], loc='upper left')
    for ix, label in enumerate(gplt.xaxis.get_ticklabels(), start=1):
        lab = int(label.get_text())
        if lab%5 != 0:
            label.set_visible(False)

    plt.savefig(f"{here}/_prop-gender-bar.pdf", format='pdf', dpi=300)
    #plt.show()




def plot_gender_line(gender_df):
    p, (a2, a) =  plt.subplots(2, sharex=True)

    a2.plot(gender_df['female_p'])
    a.plot(gender_df['female_p'])


    a.spines['top'].set_visible(False)
    a.spines['right'].set_visible(False)
    a2.spines['top'].set_visible(False)
    a2.spines['bottom'].set_visible(False)
    a2.spines['right'].set_visible(False)

    a.set_ylim(0, 0.5)
    a2.set_ylim(0.9, 1)

    a2.set_title("Proportion of female members of parliament")
    #plt.savefig(f"{here}/_prop-female.pdf", format='pdf', dpi=300)
    plt.show()




def gender_preprocess(gender_df):
    gender_df['total'] = gender_df.apply(lambda x: add(x['male'], x['female'], x['unspec']), axis=1)
    gender_df['male_p'] = gender_df.apply(lambda x: div(x['male'], x['total']), axis=1)
    gender_df['female_p'] = gender_df.apply(lambda x: div(x['female'], x['total']), axis=1)
    gender_df['unspec_p'] = gender_df.apply(lambda x: div(x['unspec'], x['total']), axis=1)
    gender_df.drop(['male', 'female', 'unspec', 'unspec_p', 'total'], axis=1, inplace=True) # no unspec gender was visible in plot
    gender_df.set_index('year', inplace=True)
    return gender_df




def age_preprocess(age_df):
    age_df['year'] = age_df['year'].astype(pdtypes.CategoricalDtype(categories=list(age_df['year'].unique())))
    return age_df




def main():

    gender_df = pd.read_csv(f'{here}/_gender_df.csv', sep=';')
    age_df = pd.read_csv(f'{here}/_age_df.csv', sep=';')
    gen = gender_preprocess(gender_df)
    #plot_gen(gen)
    plot_gender_line(gen)
    #plot_boxes(age_preprocess(age_df))




if __name__ == '__main__':
    main()
