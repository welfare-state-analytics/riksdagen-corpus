from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.refine import detect_mps, find_introductions, format_texts, update_ids, update_hashes
from pyriksdagen.utils import infer_metadata
from lxml import etree
import pandas as pd
import os, re, progressbar, argparse


name = "[A-ZÅÖÄÉ][a-zäöåé]{2,25}"
pattern = name + " i " + name
print(pattern)
e = re.compile(pattern)

TEI = "{http://www.tei-c.org/ns/1.0}"

def main(args):
    start_year = args.start
    end_year = args.end
    root = ""#"../"
    pc_folder = root + "corpus/"
    folders = os.listdir(pc_folder)

    parser = etree.XMLParser(remove_blank_text=True)
    for outfolder in progressbar.progressbar(folders):
        if os.path.isdir(pc_folder + outfolder):
            outfolder = outfolder + "/"
            protocol_ids = os.listdir(pc_folder + outfolder)
            protocol_ids = [protocol_id.replace(".xml", "") for protocol_id in protocol_ids if protocol_id.split(".")[-1] == "xml"]

            first_protocol_id = protocol_ids[0]     
            metadata = infer_metadata(first_protocol_id)
            year = metadata["year"]
            print("Year", year)
            if year >= start_year and year <= end_year:
                areas = set()
                for protocol_id in progressbar.progressbar(protocol_ids):
                    metadata = infer_metadata(protocol_id)
                    filename = pc_folder + outfolder + protocol_id + ".xml"
                    root = etree.parse(filename, parser).getroot()

                    years = [int(elem.attrib.get("when").split("-")[0]) for elem in root.findall(".//{http://www.tei-c.org/ns/1.0}docDate")]

                    if not year in years:
                        year = years[0]

                    if str(year) not in protocol_id:
                        print(protocol_id, year)

                    for note in root.findall(".//" + TEI + "note"):
                        if note.attrib.get("type", None) == "speaker":
                            text_content= "\n".join(note.itertext())

                            matches = e.finditer(text_content)
                            
                            if matches is not None:
                                for match in matches:
                                    start = match.start()
                                    end = match.end()
                                    if len(text_content) >= end and text_content[end] != ",":
                                        matched_str = text_content[start:end]

                                        area = matched_str.split()[-1]
                                        areas.add(area)

                for area in sorted(list(areas)):
                    print(f'{area}, {year}')
                            

                    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--start', type=int, default=1920)
    parser.add_argument('--end', type=int, default=2021)
    args = parser.parse_args()
    main(args)