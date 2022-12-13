#!/usr/bin/python
import os
import shutil
from optparse import OptionParser

import image_processing
import signbank
from log import print_run_msg

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

print("Step 6: Prepare images for distribution")
image_processing.process_images(pictures_folder)

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
