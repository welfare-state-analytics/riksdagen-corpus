import pandas as pd
import progressbar
from pyriksdagen.download import LazyArchive
from pyriksdagen.export import parlaclarin_workflow
from pyriksdagen.export import parlaclarin_workflow_individual
from pyriksdagen.db import load_db, save_db, load_patterns
import argparse


def main(args):
    file_dbs = []
    file_dbs.append(pd.read_csv("input/protocols/scanned.csv"))
    file_dbs.append(pd.read_csv("input/protocols/digital_originals.csv"))
    file_db = pd.concat(file_dbs)

    start_year = args.start
    end_year = args.end

    print("Process files from", start_year, "to", end_year)

    file_db = file_db[file_db["year"] >= start_year]
    file_db = file_db[file_db["year"] <= end_year]

    mp_db = pd.read_csv("corpus/members_of_parliament.csv")
    archive = LazyArchive()

    parlaclarin_workflow_individual(
        file_db, archive, curations=None, segmentations=None
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
