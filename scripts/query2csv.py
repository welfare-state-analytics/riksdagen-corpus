#!/usr/bin/env python3
"""
Generates csv of protokoll packages for a given year or list of years.
"""
import argparse, kblab, os
from kblab import Archive
from pyriksdagen.download import fetch_files, LazyArchive




query = {
#           Add parameters to the query if necessary
#			"tags": "protokoll", # apparently not all protokolls are tagged, so it's not part of the query,
#                                #   rather protocols are filtered by existence of 'prot-' in filename,
#                                #   see query_archive().
		}
a = LazyArchive()




def query_archive(a, query_dates):

    package_ids = []

    for qd in query_dates:
        if args.mkdirs:
            if not os.path.exists(f"corpus/protocols/{qd}"):
                os.mkdir(f"corpus/protocols/{qd}")
        query["meta.created"] = qd
        [package_ids.append(p) for p in a.search(query) if p.startswith("prot-")]

    return package_ids




def packages_to_input_csv(package_ids):

    csvfile = None
    if args.scanned:
        csvfile = "scanned.csv"
    else:
        csvfile = "digital_originals.csv"

    with open(f"input/protocols/{csvfile}", "w+") as csv:
        csv.write(',protocol_id,year,pages\n')
        for i, p in enumerate(package_ids):
            year = p.split('-')[1]
            n_files = len(fetch_files(a.get(p)))
            print(f'{i}, {p}, {year}, {n_files}')
            csv.write(f'{i},{p},{year},{n_files}\n')

    print("no już, your input file is ready")




def main(args):

    query_dates = None

    if args.year:
        query_dates = args.year.split(',')
    elif args.start and args.end:
        query_dates = list(range(args.start, args.end + 1))
    else:
        print("Something is wrong. Run with -h for help.")

    packages_to_input_csv(query_archive(a, query_dates))




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, epilog="You need to specify a year list or a year range with -s and -e.")
    parser.add_argument("-i", "--scanned", action='store_true', help="set this flag for scanned protocols")
    parser.add_argument("-d", "--digital_originals", action="store_true", help="set this flag for born digital protocols")
    parser.add_argument("-y", "--year", type=str, default=None, help="Comma separated (no spaces) list of years to query")
    parser.add_argument("-s", "--start", type=int, default=None, help="Start year for a range of years.")
    parser.add_argument("-e", "--end", type=int, default=None, help="End year for a range of years.")
    parser.add_argument("-m", "--mkdirs", action='store_true', help="Makes a <year> directory for each year arg in corpus/protocols/")
    args = parser.parse_args()
    if (args.year or (args.start and args.end)) and (args.scanned != args.digital_originals):
        main(args)
    else:
        print("\n\nOh No!\n\nSomething is wrong with your arguments. Get it together and try again.\n\n")
        if not (args.year or (args.start and args.end)):
            print("\tSet a list of years with -y or a range of years with -s AND -e. \n")
        if not (args.scanned != args.digital_originals):
            print("\tSet either -i OR -d. \n")
        parser.print_help()
