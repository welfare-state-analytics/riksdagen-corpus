#!/usr/bin/env python3
"""
GENERATE SWERIK IDS FOR WIKIDATA
"""
from pyriksdagen.utils import get_formatted_uuid
from tqdm import tqdm
import argparse, glob, json, sys
import pandas as pd




no_wiki_id = [
    "corpus/metadata/government.csv",
    "corpus/metadata/riksdag_start-end.csv",
    "corpus/metadata/party_abbreviation.csv",
    ]
unittest_files = [
    "corpus/quality_assessment/known_iorter/known_iorter.csv",
    "corpus/quality_assessment/known_mps/known_mps_catalog.csv",
    ]



def generate_swerik_id(wiki_id):
    seed = wiki_id + str(int(wiki_id[1:]) * 7)
    return get_formatted_uuid(seed=seed)




def update_unittest_files():
    D = {}
    df = pd.read_csv("corpus/metadata/swerik-to-wikidata-id-map.csv")
    print(df)
    for i, r in df.iterrows():
        D[r["wiki_id"]] = r["SWERIK_ID"]
    print(len(D))
    for f in unittest_files:
        df = pd.read_csv(f, sep=";")
        df["wiki_id"] = df["wiki_id"].map(D)
        df.rename(columns={"wiki_id":"swerik_id"}, inplace=True)
        df.to_csv(f, sep=";", index=False)




def generate_from_wiki_id(ids_to_add):
    df = pd.read_csv("corpus/metadata/swerik-to-wikidata-id-map.csv")

    for wiki_id in ids_to_add:
        df.loc[len(df)] = [generate_serik_id(wiki_id), wiki_id]

    assert(len(df) == len(df.SWERIK_ID.unique()))
    df.to_csv("corpus/metadata/swerik-to-wikidata-id-map.csv", index=False)
    print("done")




def main(args):
    if args.add_singleton:
        print("adding one new SWERIK ID")
        generate_from_wiki_id([args.add_singleton])

    elif args.add_list:
        print("adding one new SWERIK IDs from list")
        with open(args.add_list, "r") as inf:
            if args.add_list.endswith(".txt"):
                lines = inf.readlines()
            elif args.add_list.endswith(".json"):
                j = json.load(inf)
                lines = [k for k,v in j.items()]

        generate_from_wiki_id([_.strip() for _ in lines])
    elif args.update_testfiles:
        print("DANGER ZONE: You want to update unittest files -- this should only be done once. Probably you made a mistake!")
        #update_unittest_files()
    else:
        wiki_ids = []
        metadata = glob.glob("corpus/metadata/*.csv")
        print("fetching Wiki IDs from:")
        for csv in metadata:
            if csv in no_wiki_id:
                continue
            print("  ", csv)
            df = pd.read_csv(csv)
            [wiki_ids.append(_) for _ in df.wiki_id.unique() if _ not in wiki_ids]
        print(f"Found {len(wiki_ids)} Wiki IDs")
        print("Generating SWERIK IDs")
        rows = []
        cols = ["SWERIK_ID", "wiki_id"]
        for wiki_id in tqdm(wiki_ids, total=len(wiki_ids)):
            rows.append([generate_swerik_id(wiki_id), wiki_id])
        df = pd.DataFrame(rows, columns=cols)
        print("Testing IDs are unique")
        assert(len(df) == len(df.SWERIK_ID.unique()))
        print("  ok")
        df.to_csv("corpus/metadata/swerik-to-wikidata-id-map.csv", index=False)
        print("done")




if __name__ == '__main__':
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument("-u", "--update-testfiles",
                        action="store_true",
                        help="Replace wiki_id colum in unit test files with SWERIK IDs.")
    parser.add_argument("-s", "--add-singleton",
                        type=str,
                        help="Wikidata ID of single individual for which to generate a swerik ID. \
                        If not set, the script will generate a new set of SWERIK IDs for all wiki \
                        IDs in the metadata")
    parser.add_argument("-l", "--add-list",
                        type=str,
                        help="List file of individual wikidata ids that need a swerik ID")
    args = parser.parse_args()
    if not len(sys.argv) > 1:
        print("DANGER ZONE: You called the sctript that will regnerate all SWERIK IDs, but probably don't want to do that!")
        #main(args)
    else:
        main(args)
