#!/usr/bin/env python3
"""
Calculates MP coverage and generates plots
Should be run by `./generate-markdown.py`
"""
from tqdm import tqdm
import argparse
import datetime as dt
import os
import pandas as pd




here = os.path.dirname(__file__)

ledamot_map = {
    "fk": 1,
    "ak": 2,
    "ek": 0
}

skip = [
    'corpus/protocols/1909/prot-1909----reg-01.xml',
    'corpus/protocols/1909/prot-1909----reg-02.xml',
    'corpus/protocols/197677/prot-197677--.xml',
    'corpus/protocols/197677/prot-197778--.xml',
]




def is_within_tolerance(nmp, baseline):
    ratio = nmp/baseline
    #print(f" ---> R: {ratio}")
    if ratio > 1.1:
        return False, ratio
    elif ratio > 0.9:
        return True, ratio
    else:
        return False, ratio




def get_spec(protocol_path):
    spec = None
    spl = protocol_path.split('/')[3].split('-')
    if len(spl) == 4:
        return spec
    else:
        if len(spl[2]) > 0:
            spec = spl[2]
        return spec




def mk_py(row):
    if pd.isna(row['spec']):
        return row['year']
    else:
        return str(row['year']) + row['spec']




def get_ch(protocol_path):
    chamber = None
    spl = protocol_path.split('/')[3].split('-')
    if len(spl) == 4:
        chamber = "ek"
    else:
        chamber = spl[3]
    return chamber




def get_baseline(row, baseline_df):
    #print(row)
    #print(row['year'], row['chamber'], type(row['year']), type(row['chamber']))
    y = row['year']
    c = row['chamber']
    fdf = baseline_df.loc[(baseline_df['year'] == y) & (baseline_df['chamber'] == c)].copy()
    fdf.reset_index(inplace=True)
    #print(fdf.at[0, "n_mps"])
    return fdf.at[0, "n_mps"]




def main(args):
    print("checking MP coverage...")
    baseline_df = pd.read_csv(args.mp_baseline)
    baseline_df['year'] = baseline_df['year'].apply(lambda x: str(x)[:4])
    #print(baseline_df)
    dates = pd.read_csv(args.session_dates, sep=";")
    dates = dates[~dates['protocol'].isin(skip)]
    dates = dates[~dates['date'].isin(["2021", "1977"])]
    #print(dates)
    if "N_MP" not in dates.columns:
        dates["N_MP"] = None
    if "passes_test" not in dates.columns:
        dates["passes_test"] = None
    if "almost_passes_test" not in dates.columns:
        dates['almost_passes_test'] = None
    if "ratio" not in dates.columns:
        dates["ratio"] = None
    if "year" not in dates.columns:
        dates["year"] = None
    if "spec" not in dates.columns:
        dates["spec"] = None
    if "parliament_year" not in dates.columns:
        dates["parliament_year"] = None
    if "chamber" not in dates.columns:
        dates["chamber"] = None
    if "baseline_N" not in dates.columns:
        dates["baseline_N"] = None
    if "MEPs" not in dates.columns:
        dates["MEPs"] = None

    dates["year"] = dates["protocol"].apply(lambda x: str(x.split('/')[2][:4]))
    dates["spec"] = dates["protocol"].apply(lambda x: get_spec(x))
    dates["parliament_year"] = dates.apply(mk_py, axis=1)
    dates['chamber'] = dates['protocol'].apply(lambda x: get_ch(x))
    dates['baseline_N'] = dates.apply(get_baseline, args=(baseline_df,), axis=1)

    mp_meta = pd.read_csv("input/matching/member_of_parliament.csv")
    len(mp_meta)
    mp_meta = mp_meta[mp_meta.start.notnull()]
    len(mp_meta)

    mp_meta['start'] = mp_meta['start'].apply(lambda x: pd.to_datetime(x, format='%Y-%m-%d', errors='ignore'))
    len(mp_meta)
    mp_meta['end'] = mp_meta['end'].apply(lambda x: pd.to_datetime(x, format='%Y-%m-%d', errors='ignore'))
    len(mp_meta)


    print(mp_meta[['start', 'end']].describe())

    baselines = {
        "ak":0,
        "fk":0,
        "ek":0
    }
    chamber_map = {
        "ak":2,
        "fk":1,
        "ek":0
    }

    filtered_DFs = {}
    for k, v in ledamot_map.items():
        filtered_DFs[k] = mp_meta.loc[mp_meta['chamber'] == v]

    shouldnt_happen = 0
    

    with tqdm(total=len(dates)) as prgbr:
        for i, r in dates.iterrows():
            N_MP = 0
            chamber = r['chamber']
            MEPs = []
            if not pd.isna(chamber):
                parliament_day = r['date']
                baseline = r['baseline_N']
                prgbr.set_postfix_str(f"{chamber} / {r['parliament_year']} / {shouldnt_happen}")

                if len(parliament_day) == 10:
                    #print(r['date'], type(r['date']))
                    day = dt.datetime.strptime(r['date'], '%Y-%m-%d')
                    year = day.year

                    sub_df = filtered_DFs[chamber]
                    sub_df = sub_df[sub_df["start"] <= day]
                    sub_df = sub_df[sub_df["end"] > day]

                    N_MP = len(sub_df["swerik_id"].unique())
                    MEPs = list(sub_df["swerik_id"].unique())

                dates.at[i, 'N_MP'] = N_MP

                if N_MP != 0:
                    if N_MP == r['baseline_N']:
                        dates.at[i, 'passes_test'] = True
                        dates.at[i, 'almost_passes_test'], dates.at[i, "ratio"] = is_within_tolerance(N_MP, baseline)
                    else:
                        dates.at[i, 'passes_test'] = False
                        dates.at[i, 'almost_passes_test'], dates.at[i, "ratio"] = is_within_tolerance(N_MP, baseline)
                else:
                    dates.at[i, 'passes_test'] = False
                    dates.at[i, 'almost_passes_test'] = False
                    dates.at[i, "ratio"] = 0
            else:
                dates.at[i, 'passes_test'] = "None"
                dates.at[i, 'almost_passes_test'] = "None"
                dates.at[i, "ratio"] = "None"
            dates.at[i, "MEPs"] = list(MEPs)
            prgbr.update()
    dates.to_csv(f"{here}/figures/mp-coverage/_test-result.csv", index=False, sep=";")


    total_passed = len(dates.loc[dates['passes_test'] == True])
    total_almost = len(dates.loc[dates['almost_passes_test'] == True])
    no_passdf = dates.loc[dates['almost_passes_test'] == False]
    total = len(dates)
    print(f"Of {total} parliament days, {total_passed} have correct N MPs in metadata: {total_passed/total}.")
    print(f"   {total_almost} pass or almost passed within the margin of error, i.e. +- 10%: {total_almost/total}.")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mp-baseline",
                type=str,
                default = "corpus/quality_assessment/baseline_mp_frequencies_per_year/number_mp_in_parliament.csv",
                help = "Path to file with baseline number of MPs in parliament per year.")
    parser.add_argument("--session-dates",
                type = str,
                default = "test/data/session-dates/session-dates.csv",
                help = "Path to file with dates of parliamentary meetings.")
    args = parser.parse_args()
    main(args)
