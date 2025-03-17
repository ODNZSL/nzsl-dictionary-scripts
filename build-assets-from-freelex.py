#!/usr/bin/python
import os
import re
import shutil
import xml.etree.ElementTree as ET
from optparse import OptionParser

import freelex

parser = OptionParser()
parser.add_option("-c", action="store_true", dest="cleanup",
                  help="clean up files after execution")

(options, args) = parser.parse_args()

filename = 'dnzsl-xmldump.xml'

print("Step 1: Fetching the latest signs from Freelex")
freelex.fetch_database(filename)

with open(filename) as f:
    data = f.read()
data = data.replace("\x05", "")
data = data.replace("<->", "")

# Replace ampersands, which are XML control characters, with
# the appropriate XML escape sequence
data = re.sub(r"&(?=[^#])", "&#038;", data)
parser = ET.XMLParser(encoding="UTF-8")
root = ET.XML(data, parser=parser)

print("Step 2: Fetching images from freelex")
freelex.fetch_assets(root)

print("Step 3: Rename all images to meet Android requirements")
freelex.rename_assets(root)

print("Step 4: Write out nzsl.dat for Android")
freelex.write_datfile(root)

print("Step 5: Write out sqlite nzsl.db for iOS")
freelex.write_sqlitefile()

print("Step 6: Merge images together into one folder")
freelex.copy_images_to_one_folder()

print("Step 7: Prepare images for distribution")
image_processing.process_images(pictures_folder)

if options.cleanup:
    print("Step 8: Cleanup")
    os.remove("dnzsl-xmldump.xml")
    os.remove("nzsl.dat")
    os.remove("nzsl.db")
    shutil.rmtree("picture")
    shutil.rmtree("assets")
else:
    print("Skipping cleanup (see --help for how to enable it)")

print("Done")
