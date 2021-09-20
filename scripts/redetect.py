"""
Connect introductions to the speaker in the metadata
"""
from lxml import etree
import pandas as pd
import os, progressbar, argparse
from datetime import datetime
from pyparlaclarin.refine import (
    format_texts,
)

from pyriksdagen.db import filter_db, load_patterns
from pyriksdagen.refine import (
    detect_mps,
    find_introductions,
    update_ids,
    update_hashes,
)
from pyriksdagen.utils import infer_metadata

def parse_date(s):
    """
    Parse datetimes with special error handling
    """
    try:
        return datetime.strptime(s, "%Y-%m-%d")

    except ValueError:
        if len(s) == 4:
            if int(s) > 1689 and int(s) < 2261:
                return datetime(int(s), 6, 15)
            else:
                return None
        else:
            return None


def main(args):
    start_year = args.start
    end_year = args.end
    root = ""  # "../"
    pc_folder = root + "corpus/"
    folders = os.listdir(pc_folder)
    tei_ns = ".//{http://www.tei-c.org/ns/1.0}"

    mp_db = pd.read_csv(root + "corpus/members_of_parliament.csv")
    minister_db = pd.read_csv(root + "corpus/ministers.csv", parse_dates=True)
    minister_db["start"] = pd.to_datetime(minister_db["start"], errors="coerce")
    minister_db["end"] = pd.to_datetime(minister_db["end"], errors="coerce")
    print(minister_db["start"])
    parser = etree.XMLParser(remove_blank_text=True)
    for outfolder in progressbar.progressbar(sorted(folders)):
        if os.path.isdir(pc_folder + outfolder):
            outfolder = outfolder + "/"
            protocol_ids = os.listdir(pc_folder + outfolder)
            protocol_ids = [
                protocol_id.replace(".xml", "")
                for protocol_id in protocol_ids
                if protocol_id.split(".")[-1] == "xml"
            ]

            first_protocol_id = protocol_ids[0]
            metadata = infer_metadata(first_protocol_id)
            year = metadata["year"]
            if year >= start_year and year <= end_year:
                for protocol_id in progressbar.progressbar(protocol_ids):
                    metadata = infer_metadata(protocol_id)
                    filename = pc_folder + outfolder + protocol_id + ".xml"
                    root = etree.parse(filename, parser).getroot()

                    years = [
                        int(elem.attrib.get("when").split("-")[0])
                        for elem in root.findall(tei_ns + "docDate")
                    ]

                    if not year in years:
                        year = years[0]

                    if str(year) not in protocol_id:
                        print(protocol_id, year)
                    year_mp_db = filter_db(mp_db, year=year)

                    dates = [
                        parse_date(elem.attrib.get("when"))
                        for elem in root.findall(tei_ns + "docDate")
                    ]
                    start_date, end_date = min(dates), max(dates)

                    # Convert start and end dates into datetimes
                    # Fails for pre-1600s and post-2200s dates
                    try:
                        year_ministers = minister_db[minister_db["start"] < start_date]
                        year_ministers = year_ministers[
                            year_ministers["end"] > end_date
                        ]
                    except pd.errors.OutOfBoundsDatetime:
                        print("Unreasonable date in:", protocol_id)
                        print(start_date)
                        print(end_date)
                        year_ministers = minister_db[minister_db.columns]

                    chamber = metadata.get("chamber", None)
                    if chamber is not None:
                        year_mp_db = year_mp_db[year_mp_db["chamber"] == chamber]
                    names = year_mp_db["name"]
                    ids = year_mp_db["id"]
                    names_ids = list(zip(names, ids))
                    year_mp_db = year_mp_db[year_mp_db["specifier"].notnull()]

                    pattern_db = load_patterns()
                    pattern_db = pattern_db[
                        (pattern_db["start"] <= year) & (pattern_db["end"] >= year)
                    ]
                    root = detect_mps(
                        root,
                        names_ids,
                        pattern_db,
                        mp_db=year_mp_db,
                        minister_db=year_ministers,
                        date=start_date,
                    )
                    root = update_hashes(root, protocol_id)
                    b = etree.tostring(
                        root, pretty_print=True, encoding="utf-8", xml_declaration=True
                    )

                    f = open(filename, "wb")
                    f.write(b)
                    f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2021)
    args = parser.parse_args()
    main(args)
