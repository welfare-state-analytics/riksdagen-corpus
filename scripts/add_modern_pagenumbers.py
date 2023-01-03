from lxml import etree
import json
from pathlib import Path
import pandas as pd
import requests
import subprocess
from tqdm import tqdm
import warnings

tei_ns = ".//{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

def populate_protocol(jsonpath):
    with open(jsonpath) as f:
        d = json.load(f)
        d = d["dokumentstatus"]
        
    pdf_url = d["dokbilaga"]["bilaga"]["fil_url"]
    gathering_year = d["dokument"]["rm"].replace("/", "")
    protocol_number = d["dokument"]["nummer"]
    protocol_id = f"prot-{gathering_year}--{protocol_number}"
    riksdagen_protocol_id = d["dokument"]["dok_id"]
    xmlpath = f"corpus/protocols/{gathering_year}/{protocol_id}.xml"
    if not Path(xmlpath).exists():
        warnings.warn(f"Protocol file {xmlpath} missing! Skipping...")
        return
    
    pdfpath = f'input/rawpdf/{riksdagen_protocol_id}.pdf'
    if not Path(pdfpath).exists():
        print("Download", pdfpath, "...")
        r = requests.get(pdf_url)
        with open(f'input/rawpdf/{riksdagen_protocol_id}.pdf', 'wb') as f:
            f.write(r.content)
    else:
        print(pdfpath, "already downloaded.")
    
    txtpath = pdfpath.replace(".pdf", ".txt")
    if not Path(txtpath).exists():
        print("Run pdftotext...")
        result = subprocess.run(["pdftotext", pdfpath])
        print(result)
    else:
        print(txtpath, "already exists.")
    
    if not Path(txtpath).exists():
        warnings.warn(f"Problems with conversion to {txtpath}! Skipping...")
        return
    
    parser = etree.XMLParser(remove_blank_text=True)
    with Path(xmlpath).open() as f:
        root = etree.parse(f, parser).getroot()

    with Path(txtpath).open() as f:
        pages = f.read().split("\f")
    
    pages = [" ".join(p.split()) for p in pages]
    pageindex = len(pages)
    
    ids = []
    rows = []
    for div in root.findall(f"{tei_ns}div"):
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
    for div in list(root.findall(f"{tei_ns}div")):
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
                    pb.attrib["n"] = f"{pdf_url}#page={pageno}"
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
        except:
            print(f"An error occurred processing {p}")
        #break
                
if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--jsonpath", type=str)
    args = argparser.parse_args()
    main(args)