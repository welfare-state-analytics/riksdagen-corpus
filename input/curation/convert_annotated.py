from pathlib import Path
import pandas as pd
import json
import jsonschema
from jsonschema import validate

def validate_json(jsonData, curation_schema):
    try:
        validate(instance=jsonData, schema=curation_schema)
    except jsonschema.exceptions.ValidationError as err:
        return False
    return True


def main(args):
    folder = args.folder
    p = Path(folder)
    full_d = []
    for fpath in p.glob("*/*.csv"):
        try:
            with fpath.open() as f:
                df = pd.read_csv(f)

            tag = fpath.parents[0].stem
            for _, r in df.iterrows():
                if type(r["id"]) == float:
                    break
                protocol_id = r["id"].split("/")[-1].split("#")[0]
                element_id = r["id"].split("#")[-1]
                text = r["content"]
                text = text.replace("\\n", "\n")
                
                d = dict(
                    protocol_id=protocol_id,
                    element_id=element_id,
                    quality_level="manual",
                    tag=tag,
                    text=text,
                    year=1950,
                    month=1,
                    day=2,
                    git_hash="dssd",
                    assessed_by="ninpnin",
                    )

                full_d.append(d)
        except pd.errors.ParserError:
            print("Problem with parsing", fpath)

    full_d_str = json.dumps(full_d, ensure_ascii=False, indent=4)
    with open("input/curation/schema.json") as f:
        curation_schema_str = f.read()
        curation_schema = json.loads(curation_schema_str)

    
    valid = validate_json(full_d, curation_schema)
    if valid:
        print("Output valid against the schema")
        with open(args.outfile, "w") as f:
            f.write(full_d_str)
        print("Wrote data on disk.")
    else:
        print("Output NOT valid against the schema")
        print("Data writing omitted.")

if __name__ == '__main__':
    import argparse                                                           
    parser = argparse.ArgumentParser()                                        
    parser.add_argument("--folder", type=str, default="input/multi_label_classifier/")                         
    parser.add_argument("--outfile", type=str, default="input/curation/manual_curation.json")                         
    args = parser.parse_args()
    main(args)