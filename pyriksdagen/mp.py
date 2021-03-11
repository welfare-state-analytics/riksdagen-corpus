"""
Handles the data on the members of parliament.
"""

import pandas as pd
import os, re
import progressbar
import hashlib
import unicodedata

def create_database(path):
    extension = path.split(".")[-1]

    if extension == "csv":
        print("Read:", path)
        df = pd.read_csv(path, skip_blank_lines=True)

        # Drop columns where everything is null
        nulls = df.isnull().values.all(axis=0)
        nulls = zip(df.columns, nulls)
        for column_name, null in nulls:
            if null:
                del df[column_name]
        
        new_columns = list(df.columns)
        for column_ix, column_name in enumerate(df.columns):
            if "." in column_name:
                new_name = column_name.split(".")[0]
                new_columns[column_ix] = new_name
        
        df.columns = new_columns
        
    elif extension == "txt":
        print("Read:", path)
        f = open(path)
        columns = ["Riksdagsledamot", "Parti", "Valkrets"]
        
        rows = []
        lan = None
        for line in f:
            line = line.replace("\n", "")
            if len(line) > 2:
                indented = line[:4] == "    "
                
                # Non-indented lines are titles, which correspond to 'län' / region
                if not indented:
                    lan = line
                else:
                    row = line.split(",")
                    row = [x.strip() for x in row]
                    
                    datapoint = []
                    # Add name
                    name = row[0]
                    datapoint.append(name)
                    # Add party
                    possible_parties = [s for s in row if "f." not in s]
                    party = possible_parties[-1]
                    party = re.sub(r'\(.*?\)', '', party)
                    party = re.sub(r'\[.*?\]', '', party).strip()
                    if len(party) < 4 or party.lower() != party:
                        datapoint.append(party)
                    else:
                        datapoint.append(None)
                    # Add 'län' / region
                    datapoint.append(lan)
                    rows.append(datapoint)

        df = pd.DataFrame(rows, columns = columns)
    else:
        print("File type not supported.", path)
        return None
    
    # Harmonize column names
    new_columns = list(df.columns)
    for column_ix, column_name in enumerate(df.columns):
        if column_name in ["Ledamot", "Riksdagsledamot", "Namn"]:
            new_columns[column_ix] = "name"
        if column_name in ["Parti"]:
            new_columns[column_ix] = "party"
        if column_name in ["Yrke"]:
            new_columns[column_ix] = "occupation"
        if column_name in ["Valkrets"]:
            new_columns[column_ix] = "district"

    df.columns = new_columns
    
    # Drop unnecessary columns
    retain = ["name", "party", "district", "occupation"]
    for column_name in df.columns:
        if column_name not in retain:
            del df[column_name]
    
    # Chamber
    chamber = "Enkammarriksdagen"
    potential_chamber = path.split("/")[-2]
    if potential_chamber == "ak":
        chamber = "Andra kammaren"
    elif potential_chamber == "fk":
        chamber = "Första kammaren"
    df["chamber"] = chamber
    
    # Year in office
    year_str = path.split("/")[-1].split(".")[0].replace("–­­", "-")
    if len(year_str) == 9:
        df["start"] = int(year_str[:4])
        df["end"] = int(year_str[-4:])
    elif len(year_str) == 4:
        # TODO: Currently using +-3 year heuristic because exact terms
        # are unavailable.
        if chamber == "Första kammaren":
            df["start"] = int(year_str) - 3
            df["end"] = int(year_str) + 3
        else:
            df["start"] = int(year_str)
            df["end"] = int(year_str)
    
    return df

def create_full_database(dirs):
    mp_dbs = []
    for d in dirs:
        for path in os.listdir(d):
            full_path = os.path.join(d, path)
            mp_db = create_database(full_path)
            if mp_db is not None:
                mp_dbs.append(mp_db)
    mp_db = pd.concat(mp_dbs)
    
    mp_db = mp_db.sort_values(by=["start", "chamber", "name"], ignore_index=True)

    columnsTitles = ['name' , 'party', 'district', 'chamber', 'start', 'end', 'occupation']
    mp_db = mp_db.reindex(columns=columnsTitles)

    mp_db = mp_db[mp_db["name"].notnull()]

    return mp_db

def add_gender(mp_db, names):
    print("Add gender...")
    mp_db["gender"] = None

    name_to_gender = {}
    for i, namerow in names.iterrows():
        name = namerow["name"]
        gender = namerow["gender"]
        if gender == "masculine":
            gender = "man"
        elif gender == "feminine":
            gender = "woman"
        name_to_gender[name] = gender

    for i, row in progressbar.progressbar(list(mp_db.iterrows())):
        first_name = row["name"].split()[0]
        if "-" in first_name:
            first_name = first_name.split("-")[0]
        if first_name in name_to_gender:
            mp_db.loc[i, 'gender'] = name_to_gender[first_name]

    return mp_db

def clean_names(mp_db):
    print("Clean names...")
    for i, row in progressbar.progressbar(list(mp_db.iterrows())):
        name = row["name"]
        name = name.split(" i ")[0]
        if "[" in name:
            name = name.split("[")[0]
        if "ersatt av" in name:
            name = name.split("ersatt av:")[-1]
        assert name != "", "names can't be empty: " + row["name"]
        mp_db.loc[i, 'name'] = name

    return mp_db

def replace_party_abbreviations(mp_db, party_db):
    print("Replace party abbreviations...")
    party_dict = dict()
    for _, row in party_db.iterrows():
        party = row["party"]
        abbreviation = row["abbreviation"]
        party_dict[abbreviation] = party
    
    
    for i, row in progressbar.progressbar(list(mp_db.iterrows())):
        current_party = row["party"]
        if type(current_party) == str:
            # Check if 'party' attribute is in the list of abbreviations
            row_party = current_party.strip().lower()
            if row_party in party_dict:
                mp_db.loc[i, 'party'] = party_dict[row_party]
    
    return mp_db

def add_id(mp_db):
    print("Add id...")
    columns = mp_db.columns
    mp_db["id"] = None
    print("columns used for generation:", ", ".join(columns))
    for i, row in progressbar.progressbar(list(mp_db.iterrows())):
        name = unicodedata.normalize("NFD", row["name"])
        name = name.encode("ascii", "ignore").decode("utf-8")
        name = name.lower().replace(" ", "_")
        name = name.replace(".", "").replace("(", "").replace(")", "").replace(":", "")
        party = row.get("party")

        pattern = [name]
        for column in columns:
            value = row[column]
            if type(value) != str:
                value = str(value)
            pattern.append(value)

        pattern = "_".join(pattern).replace(" ", "_").lower()

        digest = hashlib.md5(pattern.encode("utf-8")).hexdigest()
        mp_db.loc[i, 'id'] = name + "_" + digest[:6]

    return mp_db
def detect_mp(introduction, metadata, mp_db):
    """
    Detect which member of parliament is mentioned in a given introduction.

    Params:
        introuction: An introduction to a speech in the protocols. String.
        metadata: Year and chamber of the parliamentary proceeding in question. Dict.
        mp_db: MP database as a Pandas DataFrame.
    """

    year = metadata["year"]
    mp_db = mp_db[(mp_db["start"] <= year) & (mp_db["end"] >= year)]

    for ix, row in mp_db.iterrows():
        name = row["name"]
        last_name = " ".join(name.split()[1:])
        if last_name in introduction:
            return row
