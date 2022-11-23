#!/usr/bin/python
import os
import pdb
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from optparse import OptionParser

import signbank


def print_run_msg(msg):
    print(" - Running: " + msg)


parser = OptionParser()
parser.add_option("-c", action="store_true", dest="cleanup",
                  help="clean up files after execution")

(options, args) = parser.parse_args()

filename = 'signbank-glosses.csv'
video_filename = 'signbank-gloss-assets.csv'
dat_file_filename = "nzsl.dat"
database_filename = 'nzsl.db'
assets_folder = 'signbank-assets'
pictures_folder = 'assets'

print("Step 1: Fetching the latest signs from Signbank")
signbank.fetch_gloss_export_file(filename)
data = signbank.parse_signbank_csv(filename)


print("Step 3: Write out sqlite nzsl.db for iOS")
signbank.write_sqlitefile(data, database_filename)


print("Step 4: Fetching assets from signbank")
signbank.fetch_gloss_asset_export_file(video_filename)
asset_data = signbank.parse_signbank_csv(video_filename)
signbank.fetch_gloss_assets(asset_data, database_filename, assets_folder)

print("Step 4: Write out nzsl.dat for Android")
signbank.write_datfile(database_filename, dat_file_filename)

print("Step 5: Merge images together into one folder")
signbank.copy_images_to_one_folder(assets_folder, pictures_folder)

print("Step 6a: Generate search thumbnails")
# Create thumbnails used on search screens
for path, dirs, files in os.walk(pictures_folder):
    for filename in files:
        # Some images have a 1px border that looks bad in search results
        # Not all do - but we can safely trim 1px off all images
        shave_cmd = "mogrify -shave 1x1 assets/" + filename
        print_run_msg(shave_cmd)
        os.system(shave_cmd)

        # Then we make thumbnails of the border-free images
        create_thumbnail_cmd = "convert -resize x92 assets/" + \
            filename + " assets/50." + filename
        print_run_msg(create_thumbnail_cmd)
        os.system(create_thumbnail_cmd)

print("Step 6p: Shrink images for distribution")
# In order to keep the app size small, we need to run a series
# of compressions over the images

# Resize images larger than 600x600 down using mogrify from imagemagick
for path, dirs, files in os.walk(pictures_folder):
    for filename in files:
        cmd = "mogrify -resize '600x600>' assets/" + filename
        print_run_msg(cmd)
        os.system(cmd)

# Convert all images to 4 colour depth
for path, dirs, files in os.walk(pictures_folder):
    for filename in files:
        recolor_cmd = "convert -colors 4 assets/" + filename + " assets/" + filename
        print_run_msg(recolor_cmd)
        os.system(recolor_cmd)

# Finally, run optipng
for path, dirs, files in os.walk(pictures_folder):
    for filename in files:
        optipng_cmd = "optipng -quiet assets/" + filename
        print_run_msg(optipng_cmd)
        os.system(optipng_cmd)

if options.cleanup:
    print("Step 7: Cleanup")
    os.remove(filename)
    os.remove(dat_file_filename)
    os.remove(database_filename)
    shutil.rmtree(pictures_folder)
    shutil.rmtree(assets_folder)
else:
    print("Skipping cleanup (see --help for how to enable it)")

print("Done")
