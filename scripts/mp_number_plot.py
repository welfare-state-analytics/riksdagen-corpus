"""
Draw a graph of the number of MPs per year
"""
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from cycler import cycler
import re
import seaborn as sns

def get_df(path='corpus/metadata/member_of_parliament.csv'):

    # Save new values
    df = pd.read_csv(path)
    df = df[df["start"].notnull()]
    df["start_month"] = df["start"].str[5:7]
    df["start_day"] = df["start"].str[8:]
    df["end_month"] = df["end"].str[5:7]
    df["end_day"] = df["start"].str[8:]
    df["accurate_date"] = True
    df.loc[df["start_day"] == "", "accurate_date"] = False
    df.loc[df["start_day"] == "", "start_day"] = "01"
    df.loc[df["start_month"] == "", "start_month"] = "01"
    df.loc[df["end_month"] == "", "end_month"] = "12"
    df.loc[df["end_day"] == "", "end_day"] = "31"


    df["start"] = df["start"].str[:4].astype('Int32')
    df["end"] = df["end"].str[:4].astype('Int32')
    print(df)

    minyear = min(df["start"])
    maxyear = 2022

    chambers = list(set(df["role"]))
    rows = []
    for year in range(minyear, maxyear):
        df_year = df[df["start"] <= year]
        df_year = df_year[df_year["end"] >= year]

        month = "11"
        for chamber in chambers:
            df_year_chamber = df_year[df_year["role"] == chamber]
            margin_of_error = len(df_year_chamber[df_year_chamber["accurate_date"] == False])
            print(margin_of_error)

        df_year = df_year[~((df_year["start_day"] > "01") & (df_year["start_month"] >= month) & (df_year["start"] == year))]
        df_year = df_year[~((df_year["end_month"] < month) & (df_year["end"] == year))]
        #df_year = df_year[~((df_year["start_day"] < "01") & (df_year["start"] == year))]
        df_year = df_year.drop_duplicates("wiki_id")
        #print(df_year)

        for chamber in chambers:
            df_year_chamber = df_year[df_year["role"] == chamber]

            rows.append([year, len(df_year_chamber), chamber])

        if year < 1887:
            rows.append([year, 143, "nominal_fk"])
            rows.append([year, 214, "nominal_ak"])
        elif year <= 1887:
            rows.append([year, 143, "nominal_fk"])
            rows.append([year, 221, "nominal_ak"])
        elif year <= 1888:
            rows.append([year, 144, "nominal_fk"])
            rows.append([year, 222, "nominal_ak"])
        elif year <= 1891:
            rows.append([year, 147, "nominal_fk"])
            rows.append([year, 228, "nominal_ak"])
        elif year <= 1894:
            rows.append([year, 148, "nominal_fk"])
            rows.append([year, 228, "nominal_ak"])
        elif year <= 1953:
            rows.append([year, 150, "nominal_fk"])
            rows.append([year, 230, "nominal_ak"])
        elif year < 1973:
            rows.append([year, 151, "nominal_fk"])
            rows.append([year, 233, "nominal_ak"])
        else:
            rows.append([year, 349, "nominal_ek"])

    df = pd.DataFrame(rows, columns=["year", "mps", "chamber"])
    return df

def get_plot(df):
    return sns.lineplot(data=df, x="year", y="mps", hue="chamber")

def main(args):
    df = get_df()
    #plt.savefig('input/accuracy/version_plot.png')
    plot = get_plot(df)
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

