import sys

def check_unchanged(changed, files_and_dirs):
    for fpath in changed:
        for dirpath in files_and_dirs:
            if dirpath == fpath[:len(dirpath)]:
                print("File", fpath, "changed! Files in ", dirpath, "are not supposed to change")
                sys.exit(1)

    print("Ok.")
    sys.exit(0)

if __name__ == '__main__':
    files_not_supposed_to_change = ["input/curation/"]
    changed = sys.argv[1:]
    check_unchanged(changed, files_not_supposed_to_change)