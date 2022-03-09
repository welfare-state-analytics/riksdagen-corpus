import pandas as pd
import os, json
from .utils import infer_metadata
import progressbar


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
            filtered_db = db[db["start"] <= year]
            filtered_db = filtered_db[filtered_db["end"] >= year]
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
