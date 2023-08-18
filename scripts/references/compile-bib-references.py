#!/usr/bin/env python3
"""
This compiles references from `corpus/references/bibfiles/*` 
to a single bibtex document, `corpus/references/references.bib`.
 """
from tqdm import tqdm
import os, sys
import argparse

refs_dir = "corpus/references/"




def throw_error(errors, bibfile):
	print(f"The following is no bueno: {bibfile}\n\n")
	for e in errors:
		print(f"    {e}")
	print("")
	print("Fix that and try again.\n\n")
	sys.exit()




def validate_bib(b, filename):
	OK = True
	errors = []
	if not b[0].startswith("@"):
		errors.append("First line of .bib needs to start with '@'.")
		OK = False
	try:
		bibtype, key = b[0].split("{")
		#print(filename, key[:-1], filename[:-4])
		if key[:-1] != filename[:-4]:
			if not key.endswith(","):
				errors.append("Malformed first line. (missing comma?)")
			else:
				errors.append("Key must be the same as the filename without '.bib'.")
			OK = False
	except:
		errors.append("Malformed first line.")
		OK = False
	for ix, l in enumerate(b, start=1):
		if ix != 1 and ix != len(b) and ix != len(b)-1:
			if not l.endswith(","):
				errors.append(f"Line {ix} (1 index) doesn't end with a comma and it should.")
				OK = False
		if ix == len(b):
			if not l == "}":
				errors.append("Last line must == '}'")
				OK = False
		if ix != 1 and ix != len(b):
			if "=" not in l:
				errors.append(f"Line {ix} (1 index) is malformed. Must contain '='.")
				OK = False	
		if ix == len(b)-1:
			if l.endswith(","):
				errors.append("Second to last line shouln't end with a comma, but it does.")
				OK = False
	# More validation (planned?):
	# --- reference type (right of @) are from valid set
	# --- Fields (left of =) are from valid set 

	if OK:
		return True, errors
	else:
		return False, errors




def main(args):
	bibfiles = os.listdir(f"{refs_dir}bibfiles")
	with open(args.output_file, "w+") as outf:
		for bf in tqdm(bibfiles, total=len(bibfiles)):
			with open(refs_dir+'bibfiles/'+bf, 'r') as f:
				b = f.readlines()
			b = [l.strip() for l in b if l != '\n']
			
			valid, errors = validate_bib(b, bf)
			if valid:
				for idx, l in enumerate(b):
					if idx == 0 or idx == len(b)-1:
						outf.write(f"{l}\n")
					else:
						outf.write(f"    {l}\n")					
				outf.write("\n\n")
			else:
				throw_error(errors, bf)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output-file", type=str, default="corpus/references/_compiled-references.bib", help="Where do you want the compiled reference list?")
    args = parser.parse_args()
    main(args)
