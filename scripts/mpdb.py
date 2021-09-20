import pandas as pd
from pyriksdagen.mp import create_full_database
from pyriksdagen.mp import add_gender, add_id, clean_names, add_municipality
from pyriksdagen.mp import replace_party_abbreviations

def main():
    dirs = ["input/mp/", "input/mp/fk/", "input/mp/ak/"]
    mp_db = create_full_database(dirs)
    print(mp_db)

    names = pd.read_csv("input/mp/metadata/names.csv")
    mp_db = add_gender(mp_db, names)
    print(mp_db)

    party_db = pd.read_csv("input/mp/parties.csv")
    mp_db = replace_party_abbreviations(mp_db, party_db)

    print(mp_db)

    mp_db = clean_names(mp_db)

    # Add ad hoc gender
    fmissing = pd.read_csv("input/mp/metadata/adhoc_gender.csv")
    mp_db = pd.merge(mp_db, fmissing, how="left", on="name")
    mp_db["gender"] = mp_db["gender_x"].fillna(mp_db["gender_y"])
    mp_db = mp_db.drop(columns=["gender_x", "gender_y"])

    print(mp_db)

    mp_db = add_id(mp_db)

    print(mp_db)

    mun_db = pd.read_csv("input/mp/metadata/personregister.csv")
    mp_db = add_municipality(mp_db, mun_db)

    print(mp_db)

    id_duplicates = mp_db.duplicated(subset=["id"])

    print(mp_db[id_duplicates == True])
    print(mp_db)

    columns = list(mp_db.columns)
    columns.pop(columns.index("specifier"))
    columns.append("specifier")
    mp_db = mp_db[columns]

    mp_db.to_csv("corpus/members_of_parliament.csv", index=False)

    nogender = mp_db[mp_db["gender"].isnull()]
    nogender = nogender[["name"]].drop_duplicates(["name"])
    nogender.to_csv("nogender.csv", index=False)

if __name__ == "__main__":
    main()