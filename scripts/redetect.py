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
from pyriksdagen.match_mp import clean_names, multiple_replace
from tqdm import tqdm
from multiprocessing import Pool
from itertools import product
from unidecode import unidecode

def main(args):
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end))    )    
    unknowns = []

    # For multiple replace function
    latin_characters = [chr(c) for c in range(192,383+1)]
    latin_characters = {c:unidecode(c) for c in latin_characters if c not in 'åäöÅÄÖ'}

    party_mapping, mp_db, minister_db, speaker_db = load_metadata()
    mp_db['name'] = mp_db['name'].apply(lambda x: multiple_replace(latin_characters, x))
    minister_db['name'] = minister_db['name'].apply(lambda x: multiple_replace(latin_characters, x))
    speaker_db['name'] = speaker_db['name'].apply(lambda x: multiple_replace(latin_characters, x))

    metadata = [party_mapping, mp_db, minister_db, speaker_db]

    if args.parallel == 1:
        pool = Pool()
        for unk in tqdm(pool.imap(redetect_protocol, product(protocols, [metadata])), total=len(protocols)):
            unknowns.extend(unk)
    else:
        for protocol in tqdm(protocols, total=len(protocols)):
            unk = redetect_protocol([protocol, metadata])
            unknowns.extend(unk)

    unknowns = pd.DataFrame(unknowns, columns=['protocol_id', 'hash']+["gender", "party", "other"])
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
