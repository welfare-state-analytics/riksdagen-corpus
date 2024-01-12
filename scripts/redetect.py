"""
Map introductions to the speaker in the metadata.
"""
import pandas as pd
import argparse
from pyriksdagen.db import load_metadata
from pyriksdagen.refine import redetect_protocol
from pyriksdagen.utils import protocol_iterators
from pyriksdagen.segmentation import join_text
from tqdm import tqdm
from multiprocessing import Pool
from functools import partial

def main(args):
    
    party_mapping, *dfs  = load_metadata()
    ## DEPRECIATED ##join_intros['text'] = join_intros.apply(lambda x: join_text(x['text1'], x['text2']), axis=1)
    ## DEPRECIATED ##join_intros = join_intros.drop(['text1', 'text2'], axis=1)

    for df in dfs:
        df[["start", "end"]] = df[["start", "end"]].apply(pd.to_datetime, format='%Y-%m-%d')
    metadata = [party_mapping] + dfs
    
    redetect_fun = partial(redetect_protocol, metadata)
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
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
    parser.add_argument("-s", "--start", type=int, default=1867, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    parser.add_argument("--parallel", type=int, default=1, help="N parallel processes (default=1)")
    args = parser.parse_args()
    main(args)
