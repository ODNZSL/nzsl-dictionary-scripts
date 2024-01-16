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
parser.add_option("--skip-assets", action="store_true", help="Export Signbank data, but not supporting media", dest="skip_assets")
parser.add_option("--prerelease", action="store_true",
                                  help="Export prerelease Signbank data rather than published data",
                                  dest="prerelease")

(options, args) = parser.parse_args()

filename = 'signbank-glosses.csv'
prerelease_filename = 'signbank-glosses-prerelease.csv'
video_filename = 'signbank-gloss-assets.csv'
dat_file_filename = "nzsl.dat"
database_filename = 'nzsl.db'
assets_folder = 'signbank-assets'
pictures_folder = 'assets'
download = not options.skip_assets

filters = {}
if options.prerelease:
    filters['tags'] = signbank.SIGNBANK_WEB_READY_TAG_ID
else:
    filters['published'] = 'on'

print("Step 1: Fetching the latest published signs from Signbank")
signbank.fetch_gloss_export_file(filename, { 'published': 'on' })
data = signbank.parse_signbank_csv(filename)

if options.prerelease:
    print("Step 1a: Fetching the latest prerelease signs from Signbank")
    signbank.fetch_gloss_export_file(prerelease_filename, { 'tags': signbank.SIGNBANK_WEB_READY_TAG_ID })
    data += signbank.parse_signbank_csv(prerelease_filename)

print("Step 2: Write out sqlite nzsl.db for iOS")
signbank.write_sqlitefile(data, database_filename)


print("Step 3: Fetching assets from signbank")
signbank.fetch_gloss_asset_export_file(video_filename)

asset_data = signbank.parse_signbank_csv(video_filename)
signbank.fetch_gloss_assets(asset_data, database_filename, assets_folder, download=download)
signbank.prune_orphan_assets(database_filename)

print("Step 4: Write out nzsl.dat for Android")
signbank.write_datfile(database_filename, dat_file_filename)

if download:
    print("Step 5: Merge images together into one folder")
    signbank.copy_images_to_one_folder(assets_folder, pictures_folder)

    print("Step 6: Prepare images for distribution")
    image_processing.process_images(pictures_folder)

if options.cleanup:
    print("Step 7: Cleanup")
    os.remove(filename)
    os.remove(prerelease_filename)
    os.remove(dat_file_filename)
    os.remove(database_filename)
    shutil.rmtree(pictures_folder)
    shutil.rmtree(assets_folder)
else:
    print("Skipping cleanup (see --help for how to enable it)")

print("Done")
