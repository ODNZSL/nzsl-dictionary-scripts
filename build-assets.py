#!/usr/bin/python
from optparse import OptionParser
import sys
import os
import re
import xml.etree.ElementTree as ET
import shutil

import freelex

def print_run_msg(msg):
    print(" - Running: " + msg)

parser = OptionParser()
parser.add_option("-c", action="store_true", dest="cleanup", help="clean up files after execution")

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

print("Step 6a: Generate search thumbnails")
# Create thumbnails used on search screens
for path, dirs, files in os.walk("assets/"):
    for filename in files:
        # Some images have a 1px border that looks bad in search results
        # Not all do - but we can safely trim 1px off all images
        shave_cmd = "mogrify -shave 1x1 assets/" + filename
        print_run_msg(shave_cmd)
        os.system(shave_cmd)

        # Then we make thumbnails of the border-free images
        create_thumbnail_cmd = "convert -resize x92 assets/" + filename + " assets/50." + filename
        print_run_msg(create_thumbnail_cmd)
        os.system(create_thumbnail_cmd)

print("Step 6p: Shrink images for distribution")
# In order to keep the app size small, we need to run a series
# of compressions over the images

# Resize images larger than 600x600 down using mogrify from imagemagick
for path, dirs, files in os.walk("assets/"):
    for filename in files:
        cmd = "mogrify -resize '600x600>' assets/" + filename
        print_run_msg(cmd)
        os.system(cmd)

# Convert all images to 4 colour depth
for path, dirs, files in os.walk("assets/"):
    for filename in files:
        recolor_cmd = "convert -colors 4 assets/" + filename + " assets/" + filename
        print_run_msg(recolor_cmd)
        os.system(recolor_cmd)

# Finally, run optipng
for path, dirs, files in os.walk("assets/"):
    for filename in files:
        optipng_cmd = "optipng -quiet assets/" + filename
        print_run_msg(optipng_cmd)
        os.system(optipng_cmd)

if options.cleanup:
    print("Step 7: Cleanup")
    os.remove("dnzsl-xmldump.xml")
    os.remove("nzsl.dat")
    os.remove("nzsl.db")
    shutil.rmtree("picture")
    shutil.rmtree("assets")
else:
    print("Skipping cleanup (see --help for how to enable it)")

print("Done")
