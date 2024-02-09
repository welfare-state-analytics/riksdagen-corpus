#!/usr/bin/env python3
"""
Handle issues relating to dates in the corpus and MP/Minister database.
"""
from tqdm import tqdm
import pandas as pd
from pyriksdagen.metadata import (
    impute_date, # db
    impute_minister_date, # db gov_db
    impute_speaker_date, # db
)
import sys



def _get_parliament_years(start, end, start_year, end_year, start_p, end_p, year_list, riksmote, debug):
    """
    get a list of parliament years in 4 or 6 digit format
    """
    parliament_years = []
    # same start/end year or end year is none
    if start_year == end_year or end_year == None:
        if str(start_year) == "1999":
            if start <= "1999-09-15":
                parliament_years.append(19981999)
            else:
                parliament_years.append(19992000)
            if end:
                if end_year > "1999":
                    parliament_years.append(19992000)
                else:
                    if end_p == "day":
                        if end >= "1999-09-15":
                            parliament_years.append(19992000)
            parliament_years.append(19992000)
        elif str(start_year) == "1975":
            if end_year:
                if end_year > "1975":
                    parliament_years.append(1975)
                    parliament_years.append(197576)
                else:
                    if end_p == "day":
                        if end > "1975-10-15":
                            parliament_years.append(1975)
                            parliament_years.append(197576)
                        else:
                            parliament_years.append(1975)
            else:
                if start_p == "day":
                    if start >= "1975-10-15":
                        parliament_years.append(197576)
                    else:
                        parliament_years.append(1975)
                else:
                    parliament_years.append(1975)

        # if an year is an acceptable parliament year
        else:
            if start_year in year_list:
                parliament_years.append(int(start_year))


            # else
            else:
                try:
                    df = riksmote.loc[riksmote["parliament_year"] == int(start_year + f"{int(str(start_year)[2:])+1:02}")]
                    #print(df)
                    assert df.empty == False
                except:
                    print("start date except")
                    print(start_year + f"{int(str(start_year)[2:])+1:02}" + " not in parliament_years.")
                else:
                    if start_p == "day":
                        df_starts =  df["start"].unique()
                        if start >= df_starts[0]:
                            parliament_years.append(int(start_year + f"{int(str(start_year)[2:])+1:02}"))
                            return parliament_years
                    else:
                        parliament_years.append(int(start_year + f"{int(str(start_year)[2:])+1:02}"))
                        return parliament_years
                try:
                    x = f"{int(str(start_year)[2:])-1:02}"
                    if x == "-1":
                        xx = 19992000
                    else:
                        xx = int(str(start_year)[:2] + x + f"{int(str(start_year)[2:]):02}")

                    df = riksmote.loc[riksmote["parliament_year"] == xx]
                    assert df.empty == False
                except:
                    print("end date except")
                    print(int(str(start_year)[:2] + x + f"{int(str(start_year)[2:]):02}"))
                    print(start, end, start_year, end_year)
                else:
                    if start_p == "day":
                        df_starts =  df["start"].unique()
                        if start >= df_starts[0]:
                            parliament_years.append(xx)
                    else:
                        parliament_years.append(xx)
    else:
        # if start year is one year before end year
        if str(int(start_year)+1) == str(end_year):
            if str(start_year) == "1999":
                parliament_years.append(19992000)
            elif str(start_year) == "1975":
                if end_year:
                    if str(end_year) > "1975":
                        if debug:
                            print("end is > 1975")
                        parliament_years.append(1975)
                        parliament_years.append(197576)
                    elif end_p == "day":
                        if end > "1975-10-15":
                            parliament_years.append(1975)
                            parliament_years.append(197576)
                        else:
                            parliament_years.append(1975)
                else:
                    if start_p == "day":
                        if start >= "1975-10-15":
                            parliament_years.append(197576)
                        else:
                            parliament_years.append(1975)
                    else:
                        parliament_years.append(1975)
            elif str(start_year) + str(end_year)[2:] in year_list:
                try:
                    df = riksmote.loc[riksmote["parliament_year"] == int(str(start_year) + str(end_year)[2:])]
                    assert df.empty == False
                except:
                    print("wan sani de fokopu, yere -- [-1]")
                    print(int(str(start_year) + str(end_year)[2:]))
                    print(df)
                else:
                    df_ends = df["end"].unique()
                    df_starts = df["start"].unique()
                    if start < df_starts[0]:
                        if str(int(start_year)-1) + str(start_year)[2:] in year_list:
                            parliament_years.append(int(str(int(start_year)-1) + str(start_year)[2:]))
                        elif str(start_year) in year_list:
                            parliament_years.appenr(start_year)
                        else:
                            if start_year == "2000":
                                parliament_years.append(19992000)
                            else:
                                parliament_years.append(int(start_year)-1)
                    if end > df_ends[0]:
                        if str(int(end_year) + 1) + f"{int(str(end_year)[2:]) + 2:02}" in year_list:
                            parliament_years.append(int(str(int(end_year) + 1) + f"{int(str(end_year)[2:]) + 2:02}"))
                        elif end_year == "1999":
                            parliament_years.append(200001)
                        elif end_year == "1998":
                            parliament_years.append(19992000)
                        else:
                            print(int(str(int(end_year) + 1) + f"{int(str(end_year)[2:]) + 2:02}"), "isn't in year list, but maybe it should be")
                parliament_years.append(int(str(start_year) + str(end_year)[2:]))
            else:
                parliament_years.append(int(start_year))
                parliament_years.append(int(end_year))

        # if there's range
        else:
            y_range = list(range(int(start_year[:4]), int(end_year[:4])+1))
            if debug:
                print(y_range)
            if y_range[0] in year_list and y_range[-1] in year_list:
                [parliament_years.append(int(_)) for _ in y_range]
            else:
                for ix, y in enumerate(y_range):
                    #to_append = []
                    if y > 2023:
                        continue
                    if str(y) in year_list and str(y) != "1975":
                        parliament_years.append(int(y))
                    else:
                        if str(y) == "1999":
                            to_append = ["19992000"]
                            y = 19992000
                        elif str(y) == "1975":
                            if ix == 0:
                                if end_year and end_year > "1975":
                                    y, to_append = 197576, [1975, 197576]
                                elif end_year and str(end_year) == "1975":
                                    if start_p == "day":
                                        if start > "1975-10-15":
                                            y, to_append = 197576, [197576]
                                        else:
                                            y, to_append = 1975, [1975, 197576]
                                else:
                                    y, to_append = 1975, [1975]
                            elif ix == len(y_range)-1:
                                if end_p == "day":
                                    if end >= "1975-10-15":
                                        y, to_append = 197576, [1975, 197576]
                                    else:
                                        y, to_append = 1975, [1975]
                                else:
                                    y, to_append = 1975, [1975]
                            else:
                                y, to_append = 197576, [1975, 197576]
                        else:
                            to_append = [int(str(y) + f"{int(str(y)[2:])+1:02}")]

                        if debug:
                            print(ix, y, to_append)
                        for a in to_append:
                            if ix == 0:
                                try:
                                    df = riksmote.loc[riksmote["parliament_year"] == int(a)]
                                    assert df.empty == False
                                except:
                                    print("wan sani de fokopu, yere -- [0]")
                                    print(a)
                                    print(df)
                                    continue
                                else:
                                    if start_p == "day":
                                        df_ends =  df["end"].unique()
                                        if debug:
                                            print(start, df_ends, start >= df_ends[0])
                                        if start <= df_ends[0]:
                                            parliament_years.append(a)
                                        else:
                                            x = f"{int(str(start_year)[2:])-1:02}"
                                            if x == "-1":
                                                xx = 19992000
                                            else:
                                                xx = int(str(start_year)[:2] + x + f"{int(str(start_year)[2:]):02}")

                                            parliament_years.append(xx)
                                    else:
                                        parliament_years.append(a)

                            elif ix == len(y_range)-1:
                                try:
                                    df = riksmote.loc[riksmote["parliament_year"] == int(a)]
                                    assert df.empty == False
                                except:
                                    print("wan sani de fokopu, yere -- [-1]")
                                    print(a)
                                    print(df)
                                    continue
                                else:
                                    if end_p == "day":
                                        df_starts =  df["start"].unique()
                                        if debug:
                                            print(end, df_starts, end <= df_starts[0])
                                        if end <= df_starts[0]:
                                            parliament_years.append(a)

                                        else:
                                            x = f"{int(str(end_year)[2:])-1:02}"
                                            if x == "-1":
                                                xx = 19992000
                                            else:
                                                xx = int(str(end_year)[:2] + x + f"{int(str(end_year)[2:]):02}")
                                            parliament_years.append(xx)
                                    else:
                                        parliament_years.append(a)
                            else:
                                parliament_years.append(a)
    return list(set(parliament_years))



def yearize_date(date, riksmote):
    """
    takes a date and a dataframe of corpus/metadata/riksdage_start-end.csv
    """
    parliament_years = riksmote["parliament_year"].unique()
    parliament_years = [str(_) for _ in parliament_years]
    if len(date) == 10:
        date_p = "day"
    elif len(date) == 4:
        date_p = "year"
    else:
        print(f"  ERROR!!!\nI can't handle dates of len {len(date)}")
        sys.exit()
    year = date[:4]

    return _get_parliament_years(date, None, year, None, date_p, None, parliament_years, riksmote, None)[0]




def yearize_mandates(debug_id=None):
    """
    return a dataframe of mandate periods, lengthened for each parliament year

    from
        mp   start        end
        A    2000-10-01   2002-09-30
    to
        mp   start       end           parliament_year
        A    2000-10-01  2001-09-30    200001
        A    2001-10-01  2002-09-30    200201

    """
    print("Yearizing mandates... this will take a moment.")
    riksmote = pd.read_csv("corpus/metadata/riksdag_start-end.csv")
    mep = pd.read_csv("corpus/metadata/member_of_parliament.csv")
    minister = pd.read_csv("corpus/metadata/minister.csv")
    speaker = pd.read_csv("corpus/metadata/speaker.csv")
    government = pd.read_csv("corpus/metadata/government.csv")
    parliament_years = riksmote["parliament_year"].unique()
    parliament_years = [str(_) for _ in parliament_years]
    rows = []
    slen = []
    elen = []
    cols = ["swerik_id", "start", "end", "role", "parliament_year"]
    for k, df in {"member_of_parliament":mep, "minister": minister, "speaker": speaker}.items():
        if k == "minister":
            df = impute_minister_date(impute_date(df), government)
        if k == "speaker":
            df = impute_speaker_date(impute_date(df))
        for i, r in tqdm(df.iterrows(), total=len(df)):

            if debug_id and r['swerik_id'] == debug_id:
                print(r)

            start = r["start"]
            end = r["end"]
            start_p = None
            end_p = None
            start_y = None
            end_y = None

            if pd.notnull(start):
                if "timestamps.Timestamp" in str(type(start)):
                    start_p = "year"
                    start_y = start.strftime('%Y')
                    start = start.strftime('%Y-%m-%d')
                else:
                    if len(str(start)) not in slen:
                        slen.append(len(str(start)))
                    if len(str(start)) == 10:
                        start_p = "day"
                        start_y = str(start)[:4]
                    elif len(str(start)) == 4:
                        start_p = "year"
                        start_y = str(start)
                    elif len(str(start)) == 6:
                        start_p = "year"
                        start_y = str(start)[:4]
                    elif len(str(start)) == 7:
                        print(r)
                    elif len(str(start)) > 10:
                        start = start[:10]
                        start_y = start[:4]
                        start_y = "year"
                    else:
                        print(r, len(start))

            if pd.notnull(end):
                if "timestamps.Timestamp" in str(type(end)):
                    end_p = "year"
                    end_y = end.strftime('%Y')
                    end = end.strftime('%Y-%m-%d')
                else:
                    if len(str(end)) not in elen:
                        elen.append(len(str(end)))
                    if len(str(end)) == 10:
                        end_p = "day"
                        end_y = str(end)[:4]
                    elif len(str(end)) == 4:
                        end_p = "year"
                        end_y = str(end)
                    elif len(str(end)) == 6:
                        end_p = "year"
                        end_y = str(end)[:4]
                    elif len(str(end)) == 7:
                        print(r)
                    elif len(str(end)) > 10:
                        end = end[:10]
                        end_y = end[:4]
                        end_y = "year"
                    else:
                        print(r, len(end))

            if start_y and 1866 < int(start_y[:4]) < 2025:
                if debug_id and debug_id == r["swerik_id"]:
                    pys = _get_parliament_years(start, end, start_y, end_y, start_p, end_p, parliament_years, riksmote, True)
                else:
                    pys = _get_parliament_years(start, end, start_y, end_y, start_p, end_p, parliament_years, riksmote, None)
                if debug_id and r['swerik_id'] == debug_id:
                    print(start_y, end_y, pys, start_p, end_p)
                for ix, py in enumerate(pys):
                    if int(py) < 202324:
                        try:
                            py_start = riksmote.loc[riksmote["parliament_year"] == int(py), "start"].unique()[0]
                        except:
                            print("start")
                            print(py, type(py), pys, start, end, start_y, end_y)
                        try:
                            py_end = riksmote.loc[riksmote["parliament_year"] == int(py), "end"].unique()[-1]
                        except:
                            print("end")
                            print(py, pys, start, end, start_y, end_y)

                        if start_p == "year":
                            start = py_start
                        if end_p == "year":
                            end = py_end

                        if len(pys) == 1:
                            rows.append([r["swerik_id"], start, end, r["role"], int(py)])
                        else:
                            if ix == 0:
                                rows.append([r["swerik_id"], start, py_end, r["role"], int(py)])
                            elif ix == len(pys)-1:
                                rows.append([r["swerik_id"], py_start, end, r["role"], int(py)])
                            else:
                                rows.append([r["swerik_id"], py_start, py_end, r["role"], int(py)])

            else:
                pass
    df = pd.DataFrame(rows, columns=cols)
    df.sort_values(by="swerik_id", inplace=True)
    return df



def test_yearize_mandates():
    m = yearize_mandates(debug_id="i-XvpBFhfR9SDB1i9KLCmqX2")
    #print(m.head(50))
    #print(m.sample(50).head(50))
    #print(sorted(m["parliament_year"].unique()))
    m.to_csv("_scripts/chairs/yearized_mandates.csv", index=False)


def test_yearize_date():
    riksmote = pd.read_csv("corpus/metadata/riksdag_start-end.csv")
    print(yearize_date("1982-04-13", riksmote))
    print(yearize_date("1982-12-05", riksmote))
    print(yearize_date("1882-04-13", riksmote))
    print(yearize_date("1882-12-05", riksmote))
    print(yearize_date("1932-04-13", riksmote))
    print(yearize_date("1942-12-05", riksmote))


def main():
    test_yearize_mandates()
    #test_yearize_date()



if __name__ == '__main__':
    main()
