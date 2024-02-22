import pandas as pd
import os, re
import getpass
import kblab
import progressbar
from lxml import etree
from .utils import clean_html
import warnings
import alto

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

def _alto_extract_paragraphs(altofile):
    """
    Extract text from ALTO XML on paragraph / textBlock level
    """
    paragraphs = []
    text_blocks = altofile.extract_text_blocks()
    for tb_ix, tb in enumerate(text_blocks):
        lines = tb.extract_string_lines()            
        paragraph = "\n".join(lines)
        
        # Remove line breaks when next line starts with a small letter
        paragraph = re.sub("([a-zß-ÿ,])- ?\n ?([a-zß-ÿ])", "\\1\\2", paragraph)
        paragraph = re.sub("([a-zß-ÿ,]) ?\n ?([a-zß-ÿ])", "\\1 \\2", paragraph)
        
        paragraph = " ".join(paragraph.split())
        if paragraph != "":
            paragraphs.append(paragraph)
    return paragraphs

def convert_alto(filenames, files):
    """
    Convert a document from ALTO to a list of paragraphs.

    Args:
        filenames: the names of the ALTO files of one document, as a list of str.
            The script assumes zero-padded numbering right before the .xml extension.
        files: ALTO XML files as a list of str in corresponding order to the filenames
    """
    in_sync = True
    paragraphs = []
    for ix, pair in progressbar.progressbar(enumerate(zip(filenames, files))):
        fname, s = pair
        altofile = alto.parse(s)
        page_number = int(re.findall("([0-9]{3,3}).xml", fname)[0])
        paragraphs.append(page_number)
        if in_sync and page_number != ix:
            not_in_sync_warning = f"ALTO page number and page count not in sync ({fname})"
            warnings.warn(not_in_sync_warning)
            in_sync = False
        paragraphs += _alto_extract_paragraphs(altofile)
    return paragraphs

def dl_kb_blocks(package_id, archive):
    """
    Download protocol from betalab, convert it to the simple XML 'blocks' schema
    """
    print(f"Get package {package_id}...")
    package = archive.get(package_id)
    filenames = fetch_files(package)
    def files():
        for fname in filenames:
            yield package.get_raw(fname).read()

    return convert_alto(filenames, files())


def count_pages(start, end):
    """
    Generate a dataframe of pages between provided start and end years. Fetches information from KB's API.
    """
    years = range(start, end)
    archive = LazyArchive()
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
