#!/usr/bin/env python3
"""
Iterate through EK protocols and label interpellation sections.
"""
from pyriksdagen.utils import (
        parse_protocol,
        protocol_iterators,
        write_protocol,
)
import argparse




def is_ip_debate(text):
    text = text.lower()
    ip = "svar på interpellation"
    ip2 = "svar på interpellationerna"
    not_ip = "meddelande om"
    if (ip in text or ip2 in text) and not_ip not in text:
        return True
    else:
        return False




def label_ip_debates(protocol, counter):
    root, ns = parse_protocol(protocol, get_ns=True)
    body = root.find(f".//{ns['tei_ns']}body")
    if body is None:
        print("---> got no body")
    else:
        divs = body.findall(f"{ns['tei_ns']}div")
        print("--->", len(divs))
        for i, div in enumerate(divs):
            if len(div) == 0:
                print("    ~~~> empty div")
            if len(div) == 1:
                print("    ~~~> len div == 1. index:", i, div[0].tag)
            else:
                div_id = div.attrib.get(f"{ns['xml_ns']}id")
                section_type = div.attrib.get("type")
                div_len = len(div)
                firstnote = div.find(f"{ns['tei_ns']}note")
                if section_type == "debateSection":
                    print("    --->", firstnote)
                    print("    ------->", firstnote.text.strip())
                    if firstnote is not None:
                        if len(firstnote.text) > 0 and "§" in firstnote.text.strip()[:5]:
                            note_id = firstnote.attrib.get(f"{ns['xml_ns']}id")
                            txt = ' '.join(firstnote.text.split())
                            #sections.append([protocol, div_id, section_type, div_len, note_id, txt])
                            if is_ip_debate(txt):
                                print("IS IP!!!~~~~~~~~~~~~~~~~~~~---> : ", len(div), txt)
                                div.attrib["subtype"] = "interpellationDebate"
                                counter += 1
                        else:
                            notes = div.findall(f"{ns['tei_ns']}note")
                            for note in notes:
                                if "§" in note.text.strip()[:5]:
                                    note_id = note.attrib.get(f"{ns['xml_ns']}id")
                                    txt = ' '.join(note.text.split())
                                    #sections.append([protocol, div_id, section_type, div_len, note_id, txt])
                                    if is_ip_debate(txt):
                                        print("IS IP!!!~~~~~~~~~~~~~~~~~~~---> : ", len(div), txt)
                                        div.attrib["subtype"] = "interpellationDebate"
                                        counter += 1
                                    break
                    else:
                        print("div has no notes?")
                        [print(_.tag) for _ in div]
    return root, counter




def main(args):
    counter = 0
    protocols = sorted(list(protocol_iterators("corpus/protocols/", start=args.start, end=args.end)))
    for p in protocols:
        root, counter = label_ip_debates(p, counter)
        write_protocol(root, p)

    print(counter)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--start", type=int, default=1971, help="Start year")
    parser.add_argument("-e", "--end", type=int, default=2022, help="End year")
    args = parser.parse_args()
    main(args)

