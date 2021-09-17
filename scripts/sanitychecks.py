import pandas as pd
from lxml import etree
import progressbar

mp_db = pd.read_csv("corpus/members_of_parliament.csv")
columns = mp_db.columns

dbs = []
for year in progressbar.progressbar(list(range(1920, 2021))):
    corpora_path = "input/parla-clarin/corpus" + str(year) + ".xml"

    year_rows = []

    parla_clarin = etree.parse(corpora_path).getroot()
    for u in parla_clarin.findall(".//{http://www.tei-c.org/ns/1.0}u"):
        mp_id = u.attrib.get("who", None)

        if mp_id not in ["UNK", "unk"] and mp_id is not None:
            # print(mp_id)
            row = mp_db[mp_db["id"] == mp_id].iloc[0]
        else:
            row = dict(name="unk", party="MP Not Detected")
            # print(row)
        year_row = []
        for column in columns:
            year_row.append(row.get(column, None))

            year_rows.append(year_row)

    year_db = pd.DataFrame(year_rows, columns=columns)
    by_party = year_db.set_index(["party", "id"]).count(level="party")
    by_party = by_party[["name"]]
    by_party.columns = [str(year)]

    dbs.append(by_party.T)
    print(by_party)

db = pd.concat(dbs)
db = db.fillna(0)
db.index.name = "year"
print(db)

db.to_csv("schecks.csv")
