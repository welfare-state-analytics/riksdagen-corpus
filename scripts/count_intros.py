import pandas as pd
from lxml import etree

def main(folder = "corpus/"):
    TEI = "{http://www.tei-c.org/ns/1.0}"
    sample = pd.read_csv("sample.csv")
    print(sample.columns)
    def no_of_intros(row):
        package_id = row["package_id"]
        year = package_id.split("-")[1] + "/"
        fpath = folder + year + package_id + ".xml"
        tree = etree.parse(fpath)

        page = row["pagenumber"]
        current_page = False
        speakers = 0
        for div in tree.findall(".//" + TEI + "div"):
            divtext = div.itertext()

            for elem in div:
                if elem.tag == TEI + "pb":
                    #print(elem)
                    if elem.attrib.get("n") == str(page):
                        current_page = True
                    elif current_page == True:
                        current_page = False

                elif elem.tag == TEI + "note":
                    if current_page:
                        elemtype = elem.attrib.get("type")
                        if elemtype == "speaker":

                            speakers += 1

        return speakers

    sample["speakers"] = sample.apply(lambda row: no_of_intros(row), axis=1)

    def decade(df, ind):
        year = df["year"].loc[ind]
        return (year // 10) * 10

    by_decade = sample.groupby(lambda x: decade(sample, x) )
    print(by_decade["speakers"].sum())

    print("SPEAKERS:", sample.groupby("year")["speakers"].sum())

if __name__ == '__main__':
    main()