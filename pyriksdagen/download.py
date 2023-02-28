import pandas as pd
import os, re
import getpass
import kblab
import progressbar
from lxml import etree
from .utils import clean_html
import warnings

class LazyArchive:
    """
    Wrapper to KBLab archive class so that you don't need to
    log in if you don't actually use the archive
    """

    def __init__(self):
        self.archive = None

    def __getattr__(self, attr):
        if self.archive == None:
            self.archive = _login_to_archive()
        return getattr(self.archive, attr)


def _login_to_archive():

    if "KBLPASS" in os.environ and "KBLUSER" in os.environ and "KBLMYLAB" in os.environ:
        print("Connecting to KB the laziest way...")
        return kblab.Archive(os.environ.get("KBLMYLAB"), auth=(os.environ.get("KBLUSER"), os.environ.get("KBLPASS")))

    else:
        username = input("Username: ")
        password = getpass.getpass()
        print("Password set for user:", username)
        return kblab.Archive("https://betalab.kb.se", auth=(username, password))


def oppna_data_to_dict(input_dict):
    """
    Load protocols with the new XML / HTML structure (from 2013 onwards)
    and convert it to a python dict with contents.
    """
    data = {}
    data["paragraphs"] = []

    # Metadata
    session = input_dict["dokumentstatus"]["dokument"]["rm"]
    session = session.replace("/", "")
    pid = input_dict["dokumentstatus"]["dokument"]["nummer"]
    date = input_dict["dokumentstatus"]["dokument"]["datum"]
    html = input_dict["dokumentstatus"]["dokument"]["html"]
    html_tree = clean_html(html)
    year = int(date.split("-")[0])
    protocol_id = f"prot-{session}--{pid}"

    data["protocol_id"] = protocol_id
    data["date"] = date.split(" ")[0]
    data["session"] = session

    # New HTML structure with div[@class='Section1']
    section1 = html_tree.xpath(".//div[@class='Section1']")
    for elements in section1:
        for elem in elements:
            if elem.tag in ["p", "h1", "h2"]:
                elemtext = "".join(elem.itertext())
                linebreak = elemtext.strip() == "" and "\n" in elemtext
                if linebreak:
                    pass
                else:
                    paragraph = elemtext.strip()
                    paragraph = paragraph.replace("\n", " ")
                    paragraph = re.sub("\\s+", " ", paragraph)
                    data["paragraphs"].append(paragraph)

    if len(data["paragraphs"]) == 0:
        tree = html_tree

        # Old data structure 1990-2003
        pres = tree.findall(".//pre")
        if len(pres) > 0:
            for pre in pres:
                if pre.text is not None:
                    tblocks = re.sub("([a-zß-ÿ,])- ?\n ?([a-zß-ÿ])", "\\1\\2", pre.text)
                    tblocks = re.sub("([a-zß-ÿ,]) ?\n ?([a-zß-ÿ])", "\\1 \\2", tblocks)
                    for paragraph in tblocks.split("\n"):
                        paragraph = paragraph.replace("\n", " ")
                        paragraph = paragraph.replace("\n", " ")
                        data["paragraphs"].append(paragraph)

        # Standard HTML structure, roughly 2003-2013
        elif len(tree.xpath("//div[@class='indrag']")) > 0:
            tree = tree.xpath("//body")[0]
            for elem in tree:
                elemtext = "".join(elem.itertext())
                linebreak = elemtext.strip() == "" and "\n" in elemtext
                if elem.tag == "br" or linebreak:
                    pass
                else:
                    paragraph = elemtext.strip()
                    paragraph = paragraph.replace("\n", " ")
                    paragraph = re.sub("\\s+", " ", paragraph)
                    data["paragraphs"].append(paragraph)
    return data

def dl_kb_blocks(package_id, archive):
    """
    Download protocol from betalab, convert it to the simple XML 'blocks' schema
    """
    package = archive.get(package_id)
    root = etree.Element("protocol", id=package_id)
    in_sync = True
    for ix, fname in enumerate(fetch_files(package)):
        s = package.get_raw(fname).read()
        tree = etree.fromstring(s)
        ns_dict = {"space": "http://www.loc.gov/standards/alto/ns-v3#"}
        content_blocks = tree.findall(
            ".//{http://www.loc.gov/standards/alto/ns-v3#}ComposedBlock"
        )
        page_number_str = re.findall("([0-9]{3,3}).xml", fname)[0]
        page_number = int(page_number_str)
        if in_sync and page_number != ix:
            not_in_sync_warning = f"KB page number and page count not in sync ({package_id})"
            warnings.warn(not_in_sync_warning)
            in_sync = False

        for cb_ix, content_block in enumerate(content_blocks):
            content_block_e = etree.SubElement(
                root, "contentBlock", page=str(page_number), ix=str(cb_ix)
            )
            text_blocks = content_block.findall(
                ".//{http://www.loc.gov/standards/alto/ns-v3#}TextBlock"
            )
            for tb_ix, text_block in enumerate(text_blocks):
                tblock = []
                text_lines = text_block.findall(
                    ".//{http://www.loc.gov/standards/alto/ns-v3#}TextLine"
                )

                for text_line in text_lines:
                    # tblock.append("\n")
                    strings = text_line.findall(
                        ".//{http://www.loc.gov/standards/alto/ns-v3#}String"
                    )
                    for string in strings:
                        content = string.attrib["CONTENT"]
                        tblock.append(content)

                tblock = "\n".join(tblock)
                # Remove line breaks when next line starts with a small letter
                tblock = re.sub("([a-zß-ÿ,])- ?\n ?([a-zß-ÿ])", "\\1\\2", tblock)
                tblock = re.sub("([a-zß-ÿ,]) ?\n ?([a-zß-ÿ])", "\\1 \\2", tblock)
                text_block_e = etree.SubElement(
                    content_block_e, "textBlock", ix=str(tb_ix)
                )
                text_block_e.text = tblock

    return root


def get_blocks(protocol_id, archive, load=True, save=True):
    """
    Get content and text blocks from an OCR output XML file. Concatenate words into sentences.

    Args:
        protocol_id: ID of the protocol
        archive: KBlab archive
        load: Load the file from disk if available
        save: Save the downloaded file to disk

    Returns an lxml elem tree with the structure page > contentBlock > textBlock.
    """
    folder = "input/raw/" + protocol_id + "/"
    fname = "original.xml"
    root = None
    overwrite = True
    if load or save:
        if not os.path.exists(folder):
            os.mkdir(folder)

    # Attempt to load from disk
    if load:
        fnames = os.listdir(folder)
        if fname in fnames:
            s = open(folder + fname).read()
            overwrite = False
            root = etree.fromstring(s.encode("utf-8"))

    # Load from server if local copy is not available
    if root is None:
        root = dl_kb_blocks(protocol_id, archive)

    # Save in case a new version was loaded from server
    if save and overwrite:
        fname = "original.xml"
        sb = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )
        f = open(folder + fname, "wb")
        f.write(sb)
        f.close()

    return root


def count_pages(start, end):
    """
    Generate a dataframe of pages between provided start and end years. Fetches information from KB's API.
    """
    years = range(start, end)
    archive = login_to_archive()
    rows = []

    for year in progressbar.progressbar(years):
        params = {"tags": "protokoll", "meta.created": str(year)}
        package_ids = archive.search(params, max=365)

        for package_id in package_ids:
            package = archive.get(package_id)
            jp2list = fetch_files(package, extension="jp2")
            page_count = len(jp2list)
            rows.append([package_id, year, page_count])

    columns = ["protocol_id", "year", "pages"]
    db_pages = pd.DataFrame(rows, columns=columns)
    return db_pages


def _create_dirs(outfolder):
    if not os.path.exists(outfolder):
        print("Create folder", outfolder)
        os.mkdir(outfolder)

    if not os.path.exists(outfolder + "train/"):
        os.mkdir(outfolder + "train/")

    if not os.path.exists(outfolder + "test/"):
        os.mkdir(outfolder + "test/")


def fetch_files(package, extension="xml"):
    """
    Fetch all files with the provided extension from a KBLab package

    Args:
        package: KBLab client package
        extension: File extension of the files that you want to fetch.
        String, or None which outputs all filetypes.
    """
    filelist = package.list()
    if extension is not None:
        filelist = [f for f in filelist if f.split(".")[-1] == extension]
    filelist = sorted(filelist)

    return filelist


def _get_seed(string):
    encoded = string.encode("utf-8")
    digest = hashlib.md5(encoded).hexdigest()[:8]
    return int(digest, 16)


def randomize_ordinals(files):
    """
    Create pseudo-random ordinal numbers for a database
    """
    columns = ["package_id", "year", "pagenumber", "ordinal"]
    data = []
    for index, row in files.iterrows():
        # print(index, row)
        package_id = row["package_id"]
        pages = row["pages"]
        year = row["year"]

        for page in range(0, pages):

            seedstr = package_id + str(year) + str(page)
            np.random.seed(_get_seed(seedstr))
            ordinal = np.random.rand()
            new_row = [package_id, year, page, ordinal]
            data.append(new_row)

    return pd.DataFrame(data, columns=columns)
