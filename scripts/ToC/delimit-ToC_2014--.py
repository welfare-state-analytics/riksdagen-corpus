#!/usr/bin/env python3
"""
Delimit table of contents in protocols since the 2014/15 parliament year.

N.B. Two files ['corpus/protocols/201718/prot-201718--101.xml', 'corpus/protocols/202122/prot-202122--099.xml'] contained no \<pb> elems and thus, the TOC div was added just below the heading -- these were fixed manually.
"""
from copy import deepcopy
from lxml import etree
from pyriksdagen.utils import (
    get_formatted_uuid,
    parse_protocol,
    protocol_iterators,
    write_protocol,
)
import argparse, sys




missing_pbs = []
no_toc = []
no_body = []


def find_toc(protocol, debug):
    root, ns = parse_protocol(protocol, get_ns=True)
    body = root.find(f".//{ns['tei_ns']}body")

    TOC_found = False
    if body is None:
        if debug: print("A var is no one")
        no_body.append(protocol)
        return None #toc_urls
    print("BODY:", body, body.tag)
    last_pb = None
    last_pb_idx = None
    new_div = etree.Element("div")
    new_div.attrib[f"{ns['xml_ns']}id"] = get_formatted_uuid()
    new_div.attrib['type'] = "commentSection"
    new_div.attrib['subtype'] = "tableOfContents"
    del_divs = []
    for di, div in enumerate(body):
        if debug: print(di, div.tag, len(div))
        if TOC_found == True:
            del_divs.append(di)
            for elem in div:
                new_div.append(deepcopy(elem))
        else:
            elem_del = []
            for ei, elem in enumerate(div):
                if debug: print('  ', ei, elem.tag)
                if TOC_found:
                    if last_pb is not None:
                        if debug: print("///", last_pb.tag, last_pb.attrib.get("facs"))
                        new_div.append(deepcopy(elem))
                        elem_del.append(ei)
                    else:
                        print("NO PB FOUND before innehålsförteckning------>FAIL")
                        #sys.exit()
                        missing_pbs.append(protocol)
                        break

                else:
                    if elem.tag == f"{ns['tei_ns']}pb":
                        last_pb = elem
                        last_pb_idx = ei

                    elif elem.text and elem.text.strip().lower() == "innehållsförteckning":
                        if debug: print("    ", elem.tag, elem.text.strip().lower())
                        TOC_found = True
                        if debug: print("~", last_pb_idx, ei+1)
                        if type(last_pb_idx) == int:
                            for i in range(last_pb_idx, ei+1):
                                if debug: print(len(div), i)
                                new_div.append(deepcopy(div[i]))
                                elem_del.append(i)
                        else:
                            print("NO PB FOUND before innehålsförteckning------>FAIL")
                            #sys.exit()
                            missing_pbs.append(protocol)
                            break

            if len(elem_del) > 0:
                if debug: print("DEL Elem:", elem_del)
                [div.remove(div[_]) for _ in sorted(elem_del, reverse=True)]

    if TOC_found:
        print(len(body), "DEL DIVS:", del_divs)
        for d in sorted(del_divs, reverse=True):
            body.remove(body[d])
        body.append(new_div)
        if debug: print(etree.tostring(new_div))
        return root

    else:
        print("||||||", protocol, "No TOC found")
        no_toc.append(protocol)
        return None



def main(args):

    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
    for p in protocols:
        print(p)
        root = find_toc(p, args.debug)
        if not args.dry_run:
            if root:
                write_protocol(root, p)
        else: print("dry run")

    print(len(missing_pbs), len(no_toc), len(no_body), len(protocols))
    print("MISSING PB:\n", missing_pbs)
    print("NO TOC:\n", no_toc)
    print("NO BODY:\n", no_body)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=2014, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    parser.add_argument("-d", "--debug", action='store_true', help="Print debug info")
    parser.add_argument("-n", "--dry-run", action='store_true', help="Don't actually write the files.")
    args = parser.parse_args()
    main(args)

