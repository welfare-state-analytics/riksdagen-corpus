import pandas as pd
import os
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


def filter_db(db, year=None, protocol_id=None):
    """
    Filter dataframe either based on year or protocol id
    """
    assert (
        year is not None or protocol_id is not None
    ), "Provide either year or protocol id"
    if year is not None:
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
