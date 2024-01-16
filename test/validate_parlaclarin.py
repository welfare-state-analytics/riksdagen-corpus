import sys
from pyriksdagen.utils import validate_xml_schema
import progressbar
from pathlib import Path
import warnings

def validate(parlaclarin_paths):

    # Official example parla-clarin 
    schema_path = "schemas/parla-clarin.xsd"
    #parlaclarin_path = "input/parla-clarin/official-example.xml"
    
    parlaclarin_paths = [Path(p) for p in parlaclarin_paths]
    parlaclarin_paths_xml = [p for p in parlaclarin_paths if p.suffix == ".xml"]
    if len(parlaclarin_paths_xml) != len(parlaclarin_paths):
        warnings.warn(f"Omitted {len(parlaclarin_paths) - len(parlaclarin_paths_xml)} non-XML files")
    parlaclarin_paths = [p for p in parlaclarin_paths_xml if p.stem not in ["prot-ek", "prot-ak", "prot-fk"]]
    if len(parlaclarin_paths_xml) != len(parlaclarin_paths):
        warnings.warn(f"Omitted {len(parlaclarin_paths_xml) - len(parlaclarin_paths)} corpus files")

    if len(parlaclarin_paths) == 0:
        warnings.warn("No files to be validated")
        return 0

    print(f"Validating {len(parlaclarin_paths)} XML files...")

    for parlaclarin_path in progressbar.progressbar(parlaclarin_paths):
        valid = validate_xml_schema(parlaclarin_path.absolute(), schema_path)
        if not valid:
            print(parlaclarin_path, "is not a valid parla-clarin XML file.")
            return 1

    print(f"All {len(parlaclarin_paths)} XML files were valid parla-clarin files")
    return 0

if __name__ == '__main__':
    # begin the unittest.main()
    paths = sys.argv[1:]
    print("Validate", ", ".join(paths), "...")
    exit_code = validate(paths)
    sys.exit(exit_code)
