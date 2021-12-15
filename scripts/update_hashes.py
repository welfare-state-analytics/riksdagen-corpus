"""
Update paragraph hashes.
"""
import sys
from pyriksdagen.refine import update_hashes
from lxml import etree


def update(parlaclarin_paths, manual=True):
    parser = etree.XMLParser(remove_blank_text=True)
    for parlaclarin_path in parlaclarin_paths:
        protocol_id = parlaclarin_path.split("/")[-1].split(".")[0]
        if parlaclarin_path.split(".")[-1] == "xml":
            root = etree.parse(parlaclarin_path, parser).getroot()
            root = update_hashes(root, protocol_id, manual=manual)
            b = etree.tostring(
                root, pretty_print=True, encoding="utf-8", xml_declaration=True
            )
            f = open(parlaclarin_path, "wb")
            f.write(b)
            f.close()


if __name__ == "__main__":
    # begin the unittest.main()
    paths = sys.argv[1:]
    print("Update hashes", ", ".join(paths), "...")
    exit_code = update(paths, manual=True)
