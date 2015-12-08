#!/usr/bin/python
from optparse import OptionParser
import sys
import os
import xml.etree.ElementTree as ET
import shutil

import freelex

parser = OptionParser()
parser.add_option("-i", "--ios",
                  help="location of iOS app root", metavar="IOS_PATH")
parser.add_option("-a", "--android",
                  help="location of Android app root", metavar="ANDROID_PATH")
parser.add_option("-c", action="store_true", dest="cleanup", help="clean up files after execution")

(options, args) = parser.parse_args()

if (options.ios == None or options.android == None):
    print("Missing iOS or Android path, please see build-assets.py -h")
    sys.exit(1)

if (os.path.isdir(options.ios) == False or
    os.path.exists(options.ios + '/NZSLDict/main.m') == False):
    print("Invalid iOS path")
    sys.exit(1)

if (os.path.isdir(options.android) == False or
    os.path.exists(options.android + '/build.gradle') == False):
    print("Invalid Android path")
    sys.exit(1)

filename = 'dnzsl-xmldump.xml'

print("Step 1: Fetching the latest signs from Freelex")
freelex.fetch_database(filename)

with open(filename) as f:
    data = f.read()

data = data.replace("\x05", "")
data = data.replace("<->", "")
root = ET.fromstring(data)

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

print("Step 7a: Update iOS app images")
ios_asset_path = options.ios + "/NZSLDict/nzsl/picture"
shutil.rmtree(ios_asset_path)
os.makedirs(ios_asset_path)
os.system("cp assets/* " + ios_asset_path)

print("Step 7b: Update iOS app nzsl.db")
os.system("cp nzsl.db " + options.ios + "/NZSLDict/nzsl/")

print("Step 8a: Update Android app images")
android_asset_path = options.android + "/app/src/main/res/drawable-nodpi"
shutil.rmtree(android_asset_path)
os.makedirs(android_asset_path)
os.system("cp assets/* " + android_asset_path)

print("Step 8b: Update Android app nzsl.dat")
os.system("cp nzsl.dat " + options.android + "/app/src/main/assets/db/")

if (options.cleanup == True):
    print("Step 9: Cleanup")
    os.remove("dnzsl-xmldump.xml")
    os.remove("nzsl.dat")
    os.remove("nzsl.db")
    shutil.rmtree("picture")
    shutil.rmtree("assets")

print("Done")
