"""
Split current protocol files into two:
1) TEI files with only protocol-specific content
2) teiCorpus files with metadata and links to the actual protocol-files
"""
from lxml import etree
from tqdm import tqdm
import os, argparse
from pyriksdagen.utils import protocol_iterators, infer_metadata
from pyparlaclarin.refine import format_texts
from pathlib import Path

TEI_NS = "{http://www.tei-c.org/ns/1.0}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"
XI_NS = "{http://www.w3.org/2001/XInclude}"


def extract_teiheader(root):
    teis = root.findall(f"{TEI_NS}teiHeader")
    assert len(teis) == 1
    return teis[0]


def extract_tei(root):
    teis = root.findall(f".//{TEI_NS}TEI")
    assert len(teis) == 1
    return teis[0]


def main(args):
    protocols = sorted(list(protocol_iterators(args.corpus_root, start=args.start, end=args.end)))
    parser = etree.XMLParser(remove_blank_text=True)

    protocol_dict = dict()
    corpus_dict = dict()
    for protocol in tqdm(protocols, total=len(protocols)):
        root = etree.parse(protocol, parser).getroot()
        tei = extract_tei(root)
        teiHeader = extract_teiheader(root)
        nsmap = {None: TEI_NS, "xi": XI_NS}
        nsmap = {key: value.replace("{", "").replace("}", "") for key,value in nsmap.items()}
        corpus = etree.Element(f"{TEI_NS}teiCorpus", nsmap=nsmap)
        corpus.append(teiHeader)

        tei = format_texts(tei, padding=10)
        # Write protocol file
        with open(protocol, "wb") as f:
            b = etree.tostring(
                tei, pretty_print=True, encoding="utf-8", xml_declaration=True
            )
            f.write(b)

        metadata = infer_metadata(protocol)
        sitting, chamber = metadata["sitting"], metadata["chamber"]
        chamber = f"{chamber.lower()[:1]}k"
        #Path(args.corpus_root).mkdir()
        corpus_file = f"{args.corpus_root}prot-{chamber}.xml"
        protocol_dict[corpus_file] = protocol_dict.get(corpus_file, []) + [protocol]
        
        for p in protocol_dict[corpus_file]:
            #  <xi:include xmlns:xi="http://www.w3.org/2001/XInclude" href="./prot-1973--12.xml"/>
            include = etree.SubElement(corpus, f"{XI_NS}include")
            p_filename = p.split("/")[-1]
            include.attrib["href"] = f"./{infer_metadata(p)['sitting']}/{p_filename}"

        corpus_dict[corpus_file] = corpus

    for corpus_file, corpus in corpus_dict.items():
        with open(corpus_file, "wb") as f:
            b = etree.tostring(
                corpus, pretty_print=True, encoding="utf-8", xml_declaration=True
            )
            f.write(b)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=None)
    parser.add_argument("-e", "--end", type=int, default=None)
    parser.add_argument("--corpus_root", type=str, default="corpus/protocols/")
    args = parser.parse_args()
    main(args)
