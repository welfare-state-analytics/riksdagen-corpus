"""
Add page numbers as <pb> elements to the modern protocols (1990->).
The script downloads the PDFs and matches them with the text in parla-clarin.
"""
from lxml import etree
import json
from pathlib import Path
import pandas as pd
import requests
import subprocess
from tqdm import tqdm
import traceback
from urllib.request import urlopen
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"
parser = etree.XMLParser(remove_blank_text=True)

def populate_protocol(jsonpath):
    with open(jsonpath, encoding='utf-8-sig') as f:
        d = json.load(f)
        d = d["dokumentstatus"]
    pdf_url = None
    try:
        pdf_url = d["dokbilaga"]["bilaga"]["fil_url"]
    except:
        #warnings.warn("JSON does not include PDF URL")
        logging.info('JSON does not include PDF URL')
        meta_xml_url = d["dokument"]["dokumentstatus_url_xml"]
        try:
            with urlopen(meta_xml_url) as f:
                meta_xml = etree.parse(f)
        except:
            logging.error('Metadata XML fetching or parsing unsuccesful')
            traceback.print_exc()
        
        for bilaga in meta_xml.findall(".//bilaga"):
            for fil_url in bilaga.findall(".//fil_url"):
                pdf_url = fil_url.text

    gathering_year = d["dokument"]["rm"].replace("/", "")
    protocol_number = d["dokument"]["nummer"]
    protocol_id = f"prot-{gathering_year}--{protocol_number}"
    riksdagen_protocol_id = d["dokument"]["dok_id"]
    xmlpath = f"corpus/protocols/{gathering_year}/{protocol_id}.xml"
    if not Path(xmlpath).exists():
        #warnings.warn(f"Protocol file {xmlpath} missing! Skipping...")
        logging.error(f'Protocol file {xmlpath} missing! Skipping...')
        return
    
    pdfpath = f'input/rawpdf/{riksdagen_protocol_id}.pdf'
    txtpath = pdfpath.replace(".pdf", ".txt")
    pdf_exists = Path(pdfpath).exists()
    txt_exists = Path(pdfpath).exists()
    
    if not pdf_exists and not txt_exists:
        print("Download", pdfpath, "...")
        logging.info(f"Download {pdfpath} ...")
        r = requests.get(pdf_url)
        with open(f'input/rawpdf/{riksdagen_protocol_id}.pdf', 'wb') as f:
            f.write(r.content)
    else:
        logging.info(f"{pdfpath} already downloaded")
    
    if not txt_exists:
        logging.info("Run pdftotext...")
        result = subprocess.run(["pdftotext", pdfpath])
        logging.info(f"pdftotext result code {result.returncode}")
    else:
        logging.info(f"{txtpath} already exists.")
    
    if not Path(txtpath).exists():
        logging.error(f"Problems with conversion to {txtpath}! Skipping...")
        return
    
    with Path(xmlpath).open() as f:
        root = etree.parse(f, parser).getroot()

    with Path(txtpath).open() as f:
        pages = f.read().split("\f")
    
    pages = [" ".join(p.split()) for p in pages]
    pageindex = len(pages)
    
    ids = []
    rows = []
    bodies = root.findall(f"{tei_ns}body")
    assert len(bodies) == 1
    body = bodies[0]
    for div in body.findall(f"{tei_ns}div"):
        for elem in div:
            current_id = elem.attrib.get(f"{xml_ns}id")
            ids.append(current_id)
            if current_id is None:
                continue
            t = " ".join(elem.itertext())
            t = " ".join(t.split())
            for sentence in t.split("."):
                if len(sentence.strip()) < 2:
                    continue
                found_on_pages = []
                for pagenumber in range(pageindex):
                    if len(found_on_pages) >= 2:
                        break
                    if sentence in pages[pagenumber]:
                        found_on_pages.append(pagenumber)
                
                if len(found_on_pages) == 1:
                    rows.append([found_on_pages[0], sentence, current_id])
                else:
                    rows.append([-1, sentence, current_id])
            
    df = pd.DataFrame(rows, columns=["first page", "text", "id"])
    id_df = pd.DataFrame({"id": ids})
    mode_df = df[df["first page"] >= 0]
    mode_df = mode_df.groupby(['id'])['first page'].agg(pd.Series.mode).explode().to_frame()
    mode_df = mode_df.reset_index()
    mode_df = mode_df.drop_duplicates(subset="id", keep=False)
    mode_df = id_df.merge(mode_df, how="left", on="id")
    
    for pb in root.findall(f"{tei_ns}pb"):
        parent = pb.getparent()
        parent.remove(pb)
            
    mode_df = mode_df[mode_df["first page"].notnull()]
    mode_dict = {k: v for k, v in zip(mode_df["id"], mode_df["first page"])}
    current_page = 0
    for div in list(body.findall(f"{tei_ns}div")):
        # Insert link to first page
        pb = etree.Element("pb")
        pageno = 1
        pb.attrib["facs"] = f"{pdf_url}#page={pageno}"
        div.insert(0, pb)

        for elem in div:
            current_id = elem.attrib.get(f"{xml_ns}id")
            if current_id is not None and mode_dict.get(current_id) is not None:
                pageno = mode_dict.get(current_id)
                if pageno != current_page:
                    parent = elem.getparent()
                    elem_ix = parent.index(elem)
                    current_page = pageno
                    pb = etree.Element("pb")
                    pageno = int(pageno + 1)
                    pb.attrib["facs"] = f"{pdf_url}#page={pageno}"
                    parent.insert(elem_ix, pb)

    b = etree.tostring(
        root, pretty_print=True, encoding="utf-8", xml_declaration=True
    )
    with Path(xmlpath).open("wb") as f:
        f.write(b)

def main(args):
    folder = Path(args.jsonpath)
    for p in tqdm(list(folder.glob("*.json"))):
        try:
            populate_protocol(p)
        except KeyboardInterrupt:
            return
        except Exception:
            logging.error(f"An error occurred processing {p}")
            traceback.print_exc()
        #break
                
if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument("--jsonpath", type=str)
    argparser.add_argument("--utf8sig", type=bool, default=False)
    args = argparser.parse_args()
    main(args)