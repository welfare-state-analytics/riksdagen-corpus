import sys
from pyriksdagen.utils import validate_xml_schema
import progressbar

def validate(parlaclarin_paths):

    # Official example parla-clarin 
    schema_path = "schemas/parla-clarin.xsd"
    #parlaclarin_path = "input/parla-clarin/official-example.xml"
    
    print(f"Provided {len(parlaclarin_paths)} paths")
    parlaclarin_paths = [p for p in parlaclarin_paths if p.split(".")[-1] == "xml"]
    print(f"Validating {len(parlaclarin_paths)} XML files...")

    for parlaclarin_path in progressbar.progressbar(parlaclarin_paths):
        valid = validate_xml_schema(parlaclarin_path, schema_path)
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
