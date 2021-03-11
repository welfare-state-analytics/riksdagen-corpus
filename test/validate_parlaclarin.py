import sys
from pyriksdagen.utils import validate_xml_schema

def validate(parlaclarin_paths):

    # Official example parla-clarin 
    schema_path = "schemas/parla-clarin.xsd"
    #parlaclarin_path = "input/parla-clarin/official-example.xml"
    
    for parlaclarin_path in parlaclarin_paths:
        if parlaclarin_path.split(".")[-1] == "xml":
            valid = validate_xml_schema(parlaclarin_path, schema_path)
            if not valid:
                print(parlaclarin_path, "is not a valid parla-clarin XML file.")
                return 1
    return 0

if __name__ == '__main__':
    # begin the unittest.main()
    paths = sys.argv[1:]
    print("Validate", ", ".join(paths), "...")
    exit_code = validate(paths)
    sys.exit(exit_code)
