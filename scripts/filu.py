from lxml import etree
from parliament_data.download.count_pages import login_to_archive, get_blocks
from parliament_data.segmentation import create_parlaclarin, infer_metadata


if __name__ == "__main__":
    archive = login_to_archive()
    package_id = "prot-198990--93"
    package = archive.get(package_id)
    
    filelist = package.list()
    xml_list = [f for f in filelist if f.split(".")[-1] == "xml"]
    #s = open("input/xml/prot_1972__57-137.xml").read()
        
    metadata = infer_metadata(package_id + ".txt")

    all_content_blocks = []
    for xml in xml_list:
        xml = package.get_raw(xml).read()
        blocks = get_blocks(xml)

        for block in blocks:
            all_content_blocks.append(block)
        #print(type(xml))

    parla_clarin = create_parlaclarin(all_content_blocks, metadata)
    parla_clarin_str = etree.tostring(parla_clarin, pretty_print=True, encoding="utf-8").decode("utf-8")

    outpath = "out/pc.xml"
    f = open(outpath, "w")
    f.write(parla_clarin_str)
    f.close()


