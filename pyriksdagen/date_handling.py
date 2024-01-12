#!/usr/bin/env python3
"""
Handle issues relating to dates in the corpus and MP/Minister database.
"""
import pandas as pd
from tqdm import tqdm
import sys



def _get_parliament_years(start, end, start_year, end_year, start_p, end_p, year_list, riksmote):
    """
    get a list of parliament years in 4 or 6 digit format
    """
    parliament_years = []
    if start_year == end_year or end_year == None:
        if start_year in year_list:
            parliament_years.append(int(start_year))
        elif str(start_year) == "1999":
            parliament_years.append(19992000)
        elif str(start_year) == "1975":
            if end_year:
                if end_p == "day":
                    if end > "1975-10-15":
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
        if str(int(start_year)+1) == str(end_year):
            if str(start_year) + str(end_year)[2:] in year_list:
                parliament_years.append(str(start_year) + str(end_year)[2:])
            elif str(start_year) == "1999":
                parliament_years.append(19992000)
            elif str(start_year) == "1975":
                if end_year:
                    if end_p == "day":
                        if end > "1975-10-15":
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
            else:
                parliament_years.append(int(start_year))
                parliament_years.append(int(end_year))
        else:
            y_range = list(range(int(start_year), int(end_year)+1))
            if y_range[0] in year_list and y_range[-1] in year_list:
                [parliament_years.append(int(_)) for _ in y_range]
            else:
                for ix, y in enumerate(y_range):
                    if y > 2023:
                        continue
                    if str(y) in year_list:
                        parliament_years.append(int(y))
                    else:
                        if str(y) == "1999":
                            to_append = "19992000"
                            y = 19992000
                        elif str(start_year) == "1975":
                            if end_year:
                                if end_p == "day":
                                    if end > "1975-10-15":
                                        y, to_append = 197576, 197576
                                    else:
                                        y, to_append = 1975, 1975
                                else:
                                    if end_year > "1975":
                                        y, to_append = 197576, 197576
                                    else:
                                        y, to_append = 1975, 1975
                            else:
                                if start_p == "day":
                                    if start >= "1975-10-15":
                                        y, to_append = 197576, 197576
                                    else:
                                        y, to_append = 1975, 1975
                                else:
                                    y, to_append = 1975, 1975
                        else:
                            to_append = int(str(y) + f"{int(str(y)[2:])+1:02}")
                        if ix == 0:
                            try:
                                df = riksmote.loc[riksmote["parliament_year"] == int(to_append)]
                                assert df.empty == False
                            except:
                                print("wan sani de fokopu, yere -- [0]")
                                print(to_append)
                                print(df)
                                continue
                            else:
                                if start_p == "day":
                                    df_ends =  df["end"].unique()
                                    if start >= df_ends[0]:
                                        parliament_years.append(to_append)
                                    else:
                                        x = f"{int(str(start_year)[2:])-1:02}"
                                        if x == "-1":
                                            xx = 19992000
                                        else:
                                            xx = int(str(start_year)[:2] + x + f"{int(str(start_year)[2:]):02}")
                                        parliament_years.append(xx)
                                else:
                                    parliament_years.append(to_append)
                        elif ix == len(y_range)-1:
                            try:
                                df = riksmote.loc[riksmote["parliament_year"] == to_append]
                                assert df.empty == False
                            except:
                                print("wan sani de fokopu, yere -- [-1]")
                                print(to_append)
                                print(df)
                                continue
                            else:
                                if end_p == "day":
                                    df_starts =  df["start"].unique()
                                    if end <= df_starts[0]:
                                        parliament_years.append(to_append)
                                    else:
                                        x = f"{int(str(start_year)[2:])-1:02}"
                                        if x == "-1":
                                            xx = 19992000
                                        else:
                                            xx = int(str(start_year)[:2] + x + f"{int(str(start_year)[2:]):02}")
                                        parliament_years.append(xx)
                                else:
                                    parliament_years.append(to_append)
                        else:
                            parliament_years.append(to_append)
    return parliament_years




def yearize_mp_mandates():
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
    parliament_years = riksmote["parliament_year"].unique()
    parliament_years = [str(_) for _ in parliament_years]
    rows = []
    slen = []
    elen = []
    cols = ["swerik_id", "start", "end", "role", "parliament_year"]
    for i, r in tqdm(mep.iterrows(), total=len(mep)):
        #print(" ~~~~~~~>>>>>>>", r['swerik_id'])
        start = r["start"]
        end = r["end"]
        start_p = None
        end_p = None
        start_y = None
        end_y = None
        if pd.notnull(start):
            if len(str(start)) not in slen:
                slen.append(len(str(start)))
            if len(str(start)) == 10:
                start_p = "day"
                start_y = str(start)[:4]
            elif len(str(start)) == 4:
                start_p = "year"
                start_y = str(start)
            if len(str(start)) == 7:
                print(r)
        if pd.notnull(end):
            if len(str(end)) not in elen:
                elen.append(len(str(end)))
            if len(str(end)) == 10:
                end_p = "day"
                end_y = str(end)[:4]
            elif len(str(end)) == 4:
                end_p = "year"
                end_y = str(end)
            if len(str(end)) == 7:
                print(r)

        if start_y:
            pys = _get_parliament_years(start, end, start_y, end_y, start_p, end_p, parliament_years, riksmote)
            for ix, py in enumerate(pys):
                if int(py) < 202324:
                    try:
                        py_start = riksmote.loc[riksmote["parliament_year"] == int(py), "start"].unique()[0]
                    except:
                        print("start")
                        print(py)
                    try:
                        py_end = riksmote.loc[riksmote["parliament_year"] == int(py), "end"].unique()[-1]
                    except:
                        print("end")
                        print(py)

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
            continue
    return pd.DataFrame(rows, columns=cols)




def main():
    m = yearize_mp_mandates()
    print(m.head(50))
    print(m.sample(50).head(50))
    print(sorted(m["parliament_year"].unique()))


    m.to_csv("_scripts/chairs/yearized_mandates.csv", index=False)



if __name__ == '__main__':
    main()
