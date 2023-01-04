'''
Stratified sample by decade for manual quality control of corpus tags.
TODO: Does not take into account that multiple pages from same protocol can be sampled atm.
'''
import numpy as np
import pandas as pd
import os
from lxml import etree

seed = 123
pages_per_decade = 30
tei_ns = "{http://www.tei-c.org/ns/1.0}"

def get_pagenumber(link):
    link = link.replace(".jp2/_view", "")
    link = link.split("-")[-1]
    link = link.split("page=")[-1]
    if link.isnumeric():
        return int(link)

def sample_pages(seed, pages_per_decade):
    pages_path = pd.read_csv("input/protocols/pages.csv")
    pages_path['decade'] = pages_path['year'].apply(lambda x: x//10*10)

    np.random.seed(seed)
    variables = ['package_id', 'pagenumber', 'decade']
    data = []
    for dec in sorted(set(pages_path['decade'])):
        df_dec = pages_path.loc[pages_path['decade'] == dec].reset_index(drop=True)
        idx = np.random.choice(len(df_dec), pages_per_decade, replace=False)
        data.append(df_dec.loc[idx, variables])
    df = pd.DataFrame(pd.concat(data), columns=variables)
    return df

def write_file(pages, file_path):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(file_path, parser).getroot()
    print(file_path)
    file = os.path.split(file_path)[-1]
    f = open(f"input/quality-control/{file.replace('xml', 'txt')}", "w")
    intro = 'no previous speech'
    gather_speeches = False
    for body in root.findall(".//{http://www.tei-c.org/ns/1.0}body"):
        for div in body.findall("{http://www.tei-c.org/ns/1.0}div"):
            for elem in div:
                
                # Store intro
                t = elem.get('type')
                if t == 'speaker':
                    intro = ' '.join(elem.itertext()).strip()
                
                # Find page
                link = elem.attrib.get('facs', "")
                print(link)
                n = get_pagenumber(link)
                print(n)
                if n in pages:
                    # Store url
                    url = elem.attrib.get('facs')
                    gather_speeches = True
                    f.write(url)
                    f.write('\n')
                    f.write(f'Previous intro: {intro}')
                    f.write('\n'*2)
                    continue
                else:
                    gather_speeches = False
                    continue

                if gather_speeches:
                    tag = elem.tag.split('}')[-1]
                    speaker = elem.attrib.get('who')
                    f.write(str(elem.attrib))
                    f.write('\n')
                    for e in elem.itertext():
                        f.write(' '.join(e.split()))
                        f.write('\n'*2)
    f.close()
                    
path = 'corpus/protocols'
df = sample_pages(seed, pages_per_decade)
protocols = df['package_id'].tolist()

folders = sorted(os.listdir(path))
for folder in folders:
    files = sorted(os.listdir(os.path.join(path, folder)))
    for file in files:
        if file.replace('.xml', '') in protocols:
            pages = df.loc[df['package_id'] == file.replace('.xml', ''), 'pagenumber'].tolist()
            if len(pages) > 1:
                print(file, pages)
            write_file(pages, os.path.join(path, folder, file))



