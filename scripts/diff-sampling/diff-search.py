#!/usr/bin/env python3
"""
Search for something in a git diff. Return N instances and total diff lines. search is simple substr in str type

"""
import argparse, re




def ck_line(line, req, q):
    if req:
        #print(fr"{q}")
        if re.search(fr"{q}", line):
            return True
    else:
        if q in line:
            return True
    return False




def write_hits(hit_list, lines, outf):
    to_write = []
    write_next = False
    for i, l in enumerate(lines):
        if l.startswith('diff '):
            write_next = False
        if l.startswith('index '):
            if l in hit_list:
                write_next = True
                to_write.append(lines[i-1])
                to_write.append(l)
        else:
            if write_next:
                to_write.append(l)
    with open(outf, 'w+') as o:
        for _ in to_write:
            o.write(f"{_}"+"\n")







def main(args):
    changes = 0
    counter = 0
    hit_indexes = []
    with open(args.diff_file, 'r') as inf:
        rlines = inf.readlines()
    lines = [_.strip('\n') for _ in rlines]
    index_id = None
    for i, line in enumerate(lines, start=1):
        if line.startswith('index '):
            index_id = line

        if args.search_from:
            if line.startswith('- '):
                changes += 1
                if ck_line(line, args.regex, args.search_from):
                    if args.search_to:
                        if ck_line(lines[i], args.regex, args.search_to):
                            counter += 1
                            hit_indexes.append(index_id)
                            if args.print_hit:
                                print(f"{i} | {line}")
                                print(f"{i+1} | {lines[i]}")
                    else:
                        counter += 1
                        hit_indexes.append(index_id)
                        if args.print_hit:
                            print(f"{i} | {line}")
                            print(f"{i+1} | {lines[i]}")
        else:
            if line.startswith('+ '):
                changes += 1
                if ck_line(line, args.regex, args.search_to):
                    counter += 1
                    hit_indexes.append(index_id)
                    if args.print_hit:
                        print(f"{i-1} | {lines[i-2]}")
                        print(f"{i} | {line}")

    if args.out_file:
        write_hits(hit_indexes, lines, args.out_file)

    print(changes, counter, counter/changes)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d","--diff-file", required=True, help="Path to .diff file.")
    parser.add_argument("-s", "--search-from", type=str, default=None,
        help="Substring to search for in the change from line (`-`). If given together with `-S | --search-to`, results are given when matches are found in both lines."
    )
    parser.add_argument("-S", "--search-to", type=str, default=None,
        help="Substring to searhc for in the change to line (`+`)."
    )
    parser.add_argument("-b", "--search-both", type=str, default=None,
        help="Seach the same substring and `+` and `-` lines. Equivalent of setting the `-s` and `-S` args with the same input."
    )
    parser.add_argument("-r", "--regex", action="store_true",
        help="Treat search strings as literal in regex queries."
    )
    parser.add_argument('-p', '--print-hit', action='store_true',
        help='Print match results to console.'
    )
    parser.add_argument('-o', '--out-file', type=str,
        help="Write matched diffs to the given output file."
    )
    args = parser.parse_args()
    if args.search_from or args.search_to or args.search_both:
        if args.search_both:
            args.search_from = args.search_both
            args.search_to = args.search_both
        main(args)
    else:
        print("You need to use `-s` or `-S` (or both). Try again.")

