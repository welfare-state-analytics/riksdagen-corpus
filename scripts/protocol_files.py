"""
Split current protocol files into two:
1) TEI files with only protocol-specific content
2) teiCorpus files with metadata and links to the actual protocol-files
"""
from lxml import etree
import os, argparse
from pyriksdagen.utils import protocol_iterators, infer_metadata
from pyparlaclarin.refine import format_texts
import progressbar as pb

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
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
    parser = etree.XMLParser(remove_blank_text=True)

    protocol_dict = dict()
    for protocol in pb.progressbar(protocols):
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

        corpus_file = "--".join(protocol.split("--")[:-1]) + ".xml"
        corpus_file = "corpus/protocols/" + corpus_file.split("/")[-1]
        protocol_dict[corpus_file] = protocol_dict.get(corpus_file, []) + [protocol]
        metadata = infer_metadata(protocol)
        sitting = metadata["sitting"]

        for p in protocol_dict[corpus_file]:
            #  <xi:include xmlns:xi="http://www.w3.org/2001/XInclude" href="./prot-1973--12.xml"/>
            include = etree.SubElement(corpus, f"{XI_NS}include")
            p_filename = p.split("/")[-1]
            include.attrib["href"] = f"./{sitting}/{p_filename}"

        with open(corpus_file, "wb") as f:
            b = etree.tostring(
                corpus, pretty_print=True, encoding="utf-8", xml_declaration=True
            )
            f.write(b)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1920)
    parser.add_argument("--end", type=int, default=2022)
    args = parser.parse_args()
    main(args)
