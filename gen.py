import os
import shutil

folder = "data/curation/"

for d in os.listdir(folder):
    subfolder = folder + d + "/"
    if os.path.isdir(subfolder):
        for test in os.listdir(subfolder):
            subsubfolder = subfolder + test + "/"
            if os.path.isdir(subsubfolder):
                for zero in os.listdir(subsubfolder):
                    subsubsubfolder = subsubfolder + zero + "/"
                    if os.path.isdir(subsubsubfolder):
                        print(subsubsubfolder)
                        print(os.listdir(subsubsubfolder))

                        infile = subsubsubfolder + "annotated.txt"
                        outfile = subsubsubfolder + "annotated.xml"
                        shutil.copy(infile, outfile)

