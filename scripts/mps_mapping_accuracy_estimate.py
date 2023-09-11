"""
Estimates Accuracy of speaker-speech mapping from gold standard annotations

Command-line arguments:
--start: The start year (default: 1867)
--end: The end year (default: 2022)
--path_goldstandard: Path to the gold standard CSV file 
"""
from pyriksdagen.utils import protocol_iterators, elem_iter, infer_metadata
from lxml import etree
import pandas as pd
from pathlib import Path
from scipy.stats import beta
import argparse

XML_NS = "{http://www.w3.org/XML/1998/namespace}"

def estimate_accuracy(protocol, df):
    
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(protocol, parser).getroot()

    correct, incorrect = 0, 0
    ids = set(df["elem_id"])

    found_correct_element=False

    for tag, elem in elem_iter(root):

        if found_correct_element and 'who' in elem.attrib:

            predicted_wiki_id = elem.attrib.get('who', None)

            if predicted_wiki_id==actual_wiki_id:
                correct+=1
            else:
                incorrect+=1
            #reset boolean
            found_correct_element=False
        
                
        if tag == "note" and found_correct_element==False:
            x = elem.attrib.get(f'{XML_NS}id', None)
            if x in ids:
                actual_wiki_id = df[df["elem_id"] == x]["speaker_wiki_id"].iloc[0]
                found_correct_element=True

    return correct, incorrect


def main(args):
    protocols = list(protocol_iterators("corpus/", start=args.start, end=args.end))
    df=pd.read_csv(args.path_goldstandard)

    rows = []
    correct, incorrect = 0, 0
    for p in protocols:
        path = Path(p)
        protocol_id = path.stem
        
        #print(p, protocol_id)
        df_p = df[df["protocol_id"] == protocol_id]
        if len(df_p) >= 1:

            acc = estimate_accuracy(path, df_p)
            metadata=infer_metadata(p)
            
            correct += acc[0]
            incorrect += acc[1]

            if acc[1] + acc[0] > 0:
                rows.append([acc[0], acc[1], acc[0] / (acc[0] + acc[1]), metadata["year"], metadata["chamber"]])
    accuracy = correct / (correct + incorrect)

    #Calculate a 90% credible interval, through a binomial experiment
    lower = beta.ppf(0.05, correct + 1, incorrect + 1)
    upper = beta.ppf(0.95, correct + 1, incorrect + 1)
    print(f"ACC: {100 * accuracy:.2f}% [{100* lower:.2f}% – {100* upper:.2f}%]")
    df = pd.DataFrame(rows, columns=["correct", "incorrect", "accuracy", "year", "chamber"])
    df["decade"] = (df["year"] // 10) * 10
    print(df)

    byyear_sum = df[["correct", "incorrect"]].groupby(df['decade']).sum()
    byyear_sum["lower"] = [beta.ppf(0.05, c + 1, i + 1) for c, i in zip(byyear_sum["correct"], byyear_sum["incorrect"])]
    byyear_sum["upper"] = [beta.ppf(0.95, c + 1, i + 1) for c, i in zip(byyear_sum["correct"], byyear_sum["incorrect"])]
    byyear = df['accuracy'].groupby(df['decade'])
    byyear_sum = byyear_sum.merge(byyear.mean(), on="decade").reset_index()
    print(byyear_sum)
    byyear_sum.to_csv("results.csv", index=False)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1867)
    parser.add_argument("--end", type=int, default=2022)
    parser.add_argument("--path_goldstandard", type=str, required=True)
    args = parser.parse_args()
    df = main(args)

    print(df)
