#!/usr/bin/env python3
"""
Generate / update data files for the swerik catalog on the Swerik website
"""

from datetime import datetime
from pyriksdagen.metadata import load_Corpus_metadata
from pyriksdagen.swerik_catalog import (
    jsonize_person_data,
    write_J,
    write_md,
)
from tqdm import tqdm
import argparse
import numpy as np
import pandas as pd
import re




def load_additional_metadata():
    amd = {
        "party_affiliation": pd.read_csv("corpus/metadata/party_affiliation.csv"),
        "external_identifiers": pd.read_csv("corpus/metadata/external_identifiers.csv"),
        "place_of_birth": pd.read_csv("corpus/metadata/place_of_birth.csv"),
        "place_of_death": pd.read_csv("corpus/metadata/place_of_death.csv"),
        "portraits": pd.read_csv("corpus/metadata/portraits.csv"),
    }
    return amd




def main(args):
    now = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Comparing last meta ID set with this meta ID set.")
    try:
        with open("input/metadata/catalog-id-list.txt", "r") as inf:
            last_catalog_list = [_.strip() for _ in inf.readlines()]
    except:
        last_catalog_list = None
    ids_need_attention = []
    last_pulled_ids = pd.read_csv("corpus/metadata/wiki_id.csv")
    this_catalog_list = last_pulled_ids["swerik_id"].unique()
    if last_catalog_list:
        [ids_need_attention.append(_) for _ in last_catalog_list if _ not in this_catalog_list]
    if len(ids_need_attention) > 0:
        print(" --> Some IDs will need your attention")
    else:
        print(" -- so far so good")

    print("fetching corpus metadata")
    corpus_metadata = load_Corpus_metadata()
    corpus_metadata = corpus_metadata.fillna(np.nan).replace([np.nan], [None])
    additional_metadata = load_additional_metadata()
    print(" -- ok")


    print("Generating website catalog...")
    issue_counter = 0
    for swerik_id in tqdm(this_catalog_list, total=len(this_catalog_list)):
        #print(">>>---", swerik_id)
        filtered_Corpus = corpus_metadata.loc[corpus_metadata["swerik_id"] == swerik_id].copy()
        peripheral_metadata = {}
        for key, df in additional_metadata.items():
            df = df.loc[df["swerik_id"] == swerik_id]
            df = df.fillna(np.nan).replace([np.nan], [None])
            df.reset_index(inplace=True)
            peripheral_metadata[key] = df.copy()
        #{print(k, "\n", v, "\n") for k, v in peripheral_metadata.items()}
        J = jsonize_person_data(swerik_id,
                                filtered_Corpus,
                                peripheral_metadata,
                                args.version,
                                now)
        if J:
            #print(J)
            write_J(J, swerik_id, args.website_root)
            write_md(swerik_id, args.website_root)
        else:
            ids_need_attention.append(swerik_id)
            issue_counter += 1

    idname = []
    primary_names = corpus_metadata.loc[corpus_metadata["primary_name"]==True]
    primary_names.drop_duplicates(["swerik_id", "name", "born"], inplace=True)
    primary_names.sort_values(by='name', key=lambda x: x.str.split('\s+').str[-1], inplace=True)
    for i, r in primary_names.iterrows():
        idname.append({"swerik_id": r["swerik_id"], "name": r["name"], "born": r["born"]})
    names_list = {
        "version": args.version,
        "last-updated": now,
        "names": idname
        }
    write_J(names_list, "name-listing", args.website_root)
    print(" -- done")

    print("cleaning up...")
    print(f"{len(ids_need_attention)} problem IDs, {issue_counter} from generating the catalog.")
    with open("input/metadata/catalog_problem-ids.txt", "w+") as out:
        [out.write(f"{_}\n") for _ in ids_need_attention]
    with open("input/metadata/catalog-id-list.txt", "w+") as out:
        [out.write(f"{_}\n") for _ in this_catalog_list]

    print(" -- ok, byeee")




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-w", "--website_root",
                        type=str,
                        default="../swerik-project.github.io/",
                        help="Root path to the website's local files")
    parser.add_argument("-v", "--version",
                        type=str,
                        required=True,
                        help="Data version of the current update")
    args = parser.parse_args()
    exp = re.compile(r"v([0-9]+)([.])([0-9]+)([.])([0-9]+)(b|rc)?([0-9]+)?")
    if exp.search(args.version) is None:
        print(f"{args.version} is not a valid version number. Exiting")
        exit()
    else:
        main(args)
