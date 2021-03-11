import pandas as pd
import os
from pyriksdagen.utils import infer_metadata
import progressbar

def year_iterator(file_db):
    file_db_years = sorted(list(set(file_db["year"])))
    print("Years to be iterated", file_db_years)
    for corpus_year in file_db_years:
        year_db = file_db[file_db["year"] == corpus_year]
        package_ids = year_db["protocol_id"]
        package_ids = list(package_ids)
        package_ids = sorted(package_ids)
        
        yield corpus_year, package_ids, year_db

def _db_location(protocol_id=None, year=None, phase="segmentation"):
    if protocol_id is None and year is None:
        return None
    
    if protocol_id is not None:
        metadata = infer_metadata(protocol_id)
        year = metadata["year"]
    year_str = str(year)
    folder = "input/" + phase + "/instances/"
    if not os.path.exists(folder):
        os.mkdir(folder)
    folder = folder + year_str + "/"
    if not os.path.exists(folder):
        os.mkdir(folder)
    return folder

def save_db(db, protocol_id=None, year=None, phase="segmentation"):
    folder = _db_location(protocol_id=protocol_id, year=year, phase=phase)
    if protocol_id is None and year is None:
        print("Save the whole db...")
        for protocol_id in progressbar.progressbar(list(set(db["protocol_id"]))):
            if type(protocol_id) == str:
                current_db = db[db["protocol_id"] == protocol_id]
                save_db(current_db, protocol_id=protocol_id, phase=phase)
                
    elif protocol_id is not None:
        db.to_csv(folder + protocol_id + ".csv", index=False)
    else:
        for protocol_id in list(set(list(db["protocol_id"]))):
            current_db = db[db["protocol_id"] == protocol_id]
            current_db.to_csv(folder + protocol_id + ".csv", index=False)

def load_db(protocol_id=None, year=None, phase="segmentation"):
    folder = _db_location(protocol_id=protocol_id, year=year, phase=phase)
    # Everything
    if protocol_id is None and year is None:
        folder = "input/" + phase + "/instances/"
        dbs = []
        print("Load all DBs...")
        for year in progressbar.progressbar(os.listdir(folder)):
            if os.path.isdir(folder + year):
                year_db = load_db(protocol_id=None, year=int(year), phase=phase)
                dbs.append(year_db)
        return pd.concat(dbs)
    
    # One year
    elif year is not None:
        dbs = []
        for fname in os.listdir(folder):
            if fname.split(".")[-1] == "csv":
                dbs.append(pd.read_csv(folder + fname))
        return pd.concat(dbs)
    
    # One protocol
    else:
        if fname in os.listdir(folder):
            return pd.read_csv(folder + protocol_id + ".csv")

def load_patterns(year=None, phase="segmentation"):
    fpath = "input/" + phase +"/patterns.json"
    patterns = pd.read_json(fpath, orient="records", lines=True)
    if year is not None:
        patterns = patterns[patterns["start"] >= year]
        patterns = patterns[patterns["end"] <= year]

    patterns["protocol_id"] = None
    
    manual_path = "input/" + phase +"/manual.csv"
    if os.path.exists(manual_path):
        manual = pd.read_csv(manual_path)
        manual["type"] = "manual"
        return pd.concat([manual, patterns])
    else:
        return patterns

def filter_db(db, year=None, protocol_id=None):
    assert year is not None or protocol_id is not None, "Provide either year or protocol id"
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
