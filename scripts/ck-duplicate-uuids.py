#!/usr/bin/env python3
"""
Looks for duplicate UUIDs in the protocols for a given period. 
Used when add_uuid.py throws an assetion error.
"""
import argparse, os
import xml.etree.ElementTree as et
protocols_dir = "corpus/protocols"




def ck_UUIDs(p, y, UUIDs, counter):
	XML = et.parse(f'{protocols_dir}/{y}/{p}')
	R = XML.getroot()
	body = R.find('{http://www.tei-c.org/ns/1.0}TEI/{http://www.tei-c.org/ns/1.0}text/{http://www.tei-c.org/ns/1.0}body')
	#print(body.tag)
	IDelems = body.findall('.//*[@{http://www.w3.org/XML/1998/namespace}id]')
	#print(y, p, len(IDelems))
	for e in IDelems:
		counter += 1
		uuid = e.get('{http://www.w3.org/XML/1998/namespace}id') 
		if uuid in UUIDs:
			print(f"ERMAGERD!!, trying to add element with {uuid} from {p} to a dict object, but the same uuid already exists in {UUIDs[uuid]}")
		else:
			UUIDs[uuid] = p
	return UUIDs, counter




def main(args):
	counter = 0
	years = None
	UUIDs = {}
	if args.year:
		years = args.year.split(',')
	else:
		years = list(range(args.start, args.end+1))
    
    # This doesn't handle two-year date -199495-
    #   perhaps we have to fix this later with protocol_iterator
	for year in years:
		protocols = os.listdir(f'{protocols_dir}/{year}')
		for p in protocols:
			UUIDs, counter = ck_UUIDs(p, year, UUIDs, counter)

	print(counter, len(UUIDs))




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, epilog="You need to specify a year list or a year range with -s and -e.")
    parser.add_argument("-y", "--year", type=str, default=None, help="Comma separated (no spaces) list of years to query")
    parser.add_argument("-s", "--start", type=int, default=None, help="Start year for a range of years.")
    parser.add_argument("-e", "--end", type=int, default=None, help="End year for a range of years.")
    args = parser.parse_args()
    if (args.year or (args.start and args.end)):
        main(args)
    else:
        print("\n\nOh No!\n\nSomething is wrong with your arguments. Get it together and try again.\n\n")
        if not (args.year or (args.start and args.end)):
            print("\tSet a list of years with -y or a range of years with -s AND -e. \n")
        parser.print_help()
