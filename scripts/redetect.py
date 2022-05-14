"""
Connect introductions to the speaker in the metadata.
"""
from lxml import etree
import pandas as pd
import json, math
import os, argparse
from datetime import datetime
from pyparlaclarin.refine import (
    format_texts,
)

from pyriksdagen.db import filter_db, load_patterns, load_metadata
from pyriksdagen.refine import (
    redetect_protocol,
    detect_mps,
    find_introductions,
    update_ids,
    update_hashes,
)
from pyriksdagen.utils import infer_metadata, parse_date
from pyriksdagen.utils import protocol_iterators
from pyriksdagen.match_mp import clean_names
from tqdm import tqdm
from multiprocessing import Pool
from itertools import product
from unidecode import unidecode
from functools import partial

def main(args):
    
    party_mapping, *dfs  = load_metadata()
    
    for df in dfs:
        df[["start", "end"]] = df[["start", "end"]].apply(pd.to_datetime, format='%Y-%m-%d')
    metadata = [party_mapping] + dfs
    
    redetect_fun = partial(redetect_protocol, metadata)
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end))    )    
    unknowns = []
    if args.parallel == 1:
        pool = Pool()
        for unk in tqdm(pool.imap(redetect_fun, protocols), total=len(protocols)):
            unknowns.extend(unk)
    else:
        for protocol in tqdm(protocols, total=len(protocols)):
            unk = redetect_fun(protocol)
            unknowns.extend(unk)

    unknowns = pd.DataFrame(unknowns, columns=['protocol_id', 'uuid']+["gender", "party", "other"])
    print('Proportion of metadata identified for unknowns:')
    print((unknowns[["gender", "party", "other"]] != '').sum() / len(unknowns))
    unknowns.drop_duplicates().to_csv('input/matching/unknowns.csv', index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--parallel", type=int, default=1)
    args = parser.parse_args()
    main(args)
