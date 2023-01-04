import pandas as pd
import subprocess

def main(args):
    call = ["git", "diff", "--stat"]
    #print("Run", *call)
    filename = "statdiff.txt"
    with open(filename, "w") as f:
        result = subprocess.run(call, stdout=f)
    #print(result)
    df = pd.read_csv(filename, delimiter="|", names=["filename", "changes"])
    df["changes"] = df["changes"].str.strip().str.split(" ").str[0]
    df = df[df["changes"].notnull()]
    df["changes"] = df["changes"].astype(int)
    df["p"] = df["changes"] / df["changes"].sum()
    
    sample = df.sample(args.n, weights="p", replace=True)
    
    sample = list(sample["filename"])
    print(" ".join([s.strip() for s in sample]))
    
if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--n", type=int, default=150)
    args = argparser.parse_args()
    main(args)