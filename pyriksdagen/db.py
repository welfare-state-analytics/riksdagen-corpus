import pandas as pd
import os, json, re, hashlib


def year_iterator(file_db):
    """
    Iterate over triplets of (corpus_year, package_ids, year_db) for provided file database.
    """
    file_db_years = sorted(list(set(file_db["year"])))
    print("Years to be iterated", file_db_years)
    for corpus_year in file_db_years:
        year_db = file_db[file_db["year"] == corpus_year]
        package_ids = year_db["protocol_id"]
        package_ids = list(package_ids)
        package_ids = sorted(package_ids)

        yield corpus_year, package_ids, year_db


def load_patterns(year=None, phase="segmentation"):
    """
    Load regex patterns from disk
    """
    fpath = "input/" + phase + "/patterns.json"
    patterns = pd.read_json(fpath, orient="records", lines=True)
    if year is not None:
        patterns = patterns[patterns["start"] >= year]
        patterns = patterns[patterns["end"] <= year]

    patterns["protocol_id"] = None

    manual_path = "input/" + phase + "/manual.csv"
    if os.path.exists(manual_path):
        manual = pd.read_csv(manual_path)
        manual["type"] = "manual"
        return pd.concat([manual, patterns])
    else:
        return patterns


def filter_db(db, start_date=None, end_date=None, year=None, protocol_id=None):
    """
    Filter dataframe either based on year or protocol id
    """
    assert (
        year is not None or protocol_id is not None or (start_date is not None and end_date is not None)
    ), "Provide either year or protocol id"
    if start_date is not None and end_date is not None:
        filtered_db = db[(db["start"].dt.date <= end_date.date()) & (db["end"].dt.date >= start_date.date())]
        return filtered_db
    elif year is not None:
        if "start" in db.columns:
            filtered_db = db[db["start"].dt.year <= year]
            filtered_db = filtered_db[filtered_db["end"].dt.year >= year]
            return filtered_db
        elif "year" in db.columns:
            filtered_db = db[db["year"] == year]
            return filtered_db
        else:
            return None

    else:
        return db[db["protocol_id"] == protocol_id]

def load_ministers(path='corpus/wiki-data/minister.json'):
    '''Unpacks very nested minister.json file to a df.'''
    with open(path, 'r') as f:
        minister = json.load(f)

    data = []
    for gov in minister:
        g = gov["government"]
        for member in gov["cabinet"]:
            Q = member["wiki_id"]
            n = member["name"]
            for pos in member["positions"]:
                r = pos["role"]
                s = pos["start"]
                e = pos["end"]
                data.append([g, Q, n, r, s, e])
    minister = pd.DataFrame(data, columns=["government", "wiki_id", "name", "role", "start", "end"])
    return minister

def load_metadata():
    party_mapping = pd.read_csv('corpus/metadata/party_abbreviation.csv')
    #join_intros = ## DEPRECIATED ##pd.read_csv('input/segmentation/join_intros.csv')  return party_mapping, join_intros, mp_db, minister_db, speaker_db
    mp_db = pd.read_csv('input/matching/member_of_parliament.csv')
    minister_db = pd.read_csv('input/matching/minister.csv')
    speaker_db = pd.read_csv('input/matching/speaker.csv')

    ### Temporary colname changes
    mp_db["specifier"] = mp_db["location"]
    mp_db = mp_db.rename(columns={'person_id':'id'})
    minister_db = minister_db.rename(columns={'person_id':'id'})
    speaker_db = speaker_db.rename(columns={'person_id':'id'})

    # Datetime format
    mp_db[["start", "end"]] = mp_db[["start", "end"]].apply(pd.to_datetime, errors="coerce")
    minister_db[["start", "end"]] = minister_db[["start", "end"]].apply(pd.to_datetime, errors="coerce")
    speaker_db[["start", "end"]] = speaker_db[["start", "end"]].apply(pd.to_datetime, errors="coerce")

    return party_mapping, mp_db, minister_db, speaker_db

def load_expressions(phase="segmentation", year=None):
    if phase == "segmentation":
        patterns = load_patterns(year=year)
        expressions = dict()
        for _, row in patterns.iterrows():
            pattern = row["pattern"]
            exp = re.compile(pattern)
            # Calculate digest for distringuishing patterns without ugly characters
            pattern_digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()[:16]
            expressions[pattern_digest] = exp
        return expressions
    elif phase == "mp":
        patterns = pd.read_csv("input/segmentation/detection.csv", sep=";")
        expressions = []
        for _, row in patterns.iterrows():
            exp, t = row[["pattern", "type"]]
            expressions.append((re.compile(exp), t))
        return expressions
    elif phase == "join_intros":
        patterns = pd.read_csv("input/segmentation/join_intro_pattern.csv", sep=";")
        expressions = []
        for _, row in patterns.iterrows():
            exp, t = row[["pattern", "type"]]
            expressions.append((re.compile(exp), t))
        return expressions

def _keep_most_significant(df, cols, id="wiki_id"):
    for col in cols:
        primary = df[df[col] != df[col].str[:4]]
        primary = primary[primary[col].notnull()]

        #primary = primary.drop_duplicates([id, col])
        secondary = df[df[col] == df[col].str[:4]]
        secondary = secondary[secondary[col].notnull()]

        secondary = secondary.drop_duplicates([id, col])

        col_df = pd.concat([primary, secondary])
        col_df = col_df.drop_duplicates(id)
        col_df = col_df[[id, col]]

        df = df[[c for c in df.columns if c != col]]
        df = df.drop_duplicates()
        df = pd.merge(df, col_df, how="left", on=id)

    col = cols[0]
    primary = df[df[col] != df[col].str[:4]]
    secondary = df[df[col] == df[col].str[:4]]

    df = pd.concat([primary, secondary])
    df = df.drop_duplicates(id)
    return df

def clean_person_duplicates(df):
    dupl = df[df.duplicated("swerik_id", keep=False)].copy()
    df = df[~df.duplicated("swerik_id", keep=False)]
    dupl = _keep_most_significant(dupl, ["born", "dead"], id="swerik_id")
    cols = list(df.columns)
    df = pd.concat([dupl, df])
    df = df[cols]
    df = df.drop_duplicates(list(df.columns))
    df = df.sort_values(list(df.columns))
    return df
