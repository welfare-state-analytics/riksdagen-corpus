import pandas as pd
from lxml import etree


def main(samplepath, folder="corpus/"):
    TEI = "{http://www.tei-c.org/ns/1.0}"
    sample = pd.read_csv(samplepath)
    sample["path"] = "corpus/" + sample["package_id"].str.split("-").str[1] + "/"
    sample["path"] = sample["path"] + sample["package_id"] + ".xml"
    print(sample["path"])
    print(sample.columns)

    def no_of_intros(row, unknown=True):
        fpath = row["path"]
        tree = etree.parse(fpath)

        page = row["pagenumber"]
        current_page = False
        whos = 0
        for div in tree.findall(".//" + TEI + "div"):
            divtext = div.itertext()

            for elem in div:
                if elem.tag == TEI + "pb":
                    # print(elem)
                    if elem.attrib.get("n") == str(page):
                        current_page = True
                    elif current_page == True:
                        current_page = False

                elif elem.tag == TEI + "u" and current_page:
                    who = elem.attrib.get("who")
                    if who == "unknown" or who is None:
                        if unknown:
                            whos += 1
                    else:
                        if not unknown:
                            whos += 1

        return whos

    sample["unknowns"] = sample.apply(lambda row: no_of_intros(row), axis=1)
    sample["knowns"] = sample.apply(
        lambda row: no_of_intros(row, unknown=False), axis=1
    )
    sample["year"] = sample["path"].str.split("/").str[1]
    sample["year"] = sample["year"].str[:4].astype(int)

    def decade(df, ind):
        year = df["year"].loc[ind]
        return (year // 10) * 10

    by_decade = sample.groupby(lambda x: decade(sample, x))
    print(by_decade["unknowns"].sum())
    print(by_decade["knowns"].sum())

    full = sample[["unknowns", "knowns"]].sum()
    print(full)
    # print("SPEAKERS:", sample.groupby("year")["unknowns"].sum())


if __name__ == "__main__":
    main("largesample.csv")
