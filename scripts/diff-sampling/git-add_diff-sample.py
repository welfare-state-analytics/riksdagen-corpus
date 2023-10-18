#!/usr/bin/env python3
"""
After creating a diff sample with e.g. sample-git-diffs, this script will `git add $f for f in sampled files`.

"""
import argparse, subprocess

def main(args):
    changed_files = []
    with open(args.diff_file, 'r') as inf:
        rlines = inf.readlines()
        lines = [_.strip() for _ in rlines if _.startswith('diff')]
        [changed_files.append(_.split(' ')[-1][2:]) for _ in lines]


    if args.dry_run:
        [subprocess.call(['git', 'add',  '-n', '--', _]) for _ in changed_files]
        print(f"{len(changed_files)} files to be added")
    else:
        [subprocess.call(['git', 'add', '--', _]) for _ in changed_files]
        print(f"{len(changed_files)} files added")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d","--diff-file", required=True, help="Path to .diff file.")
    parser.add_argument("-n", "--dry-run", action="store_true", help="== `git add --dry-run` : Don’t actually add the file(s), just show if they exist and/or will be ignored")
    args = parser.parse_args()
    main(args)
