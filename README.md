# nzsl-scripts

This repository holds scripts that are useful for the creation of the NZSL Android and iOS applications. These scripts are written in Python 3 and will not work with Python 2.

## build-assets.py

This is a wholistic script that performs all the steps needed to get all the necessary assets from the NZSL Freelex server. It does a number of steps:

* Step 1: Fetching the latest signs from Freelex
* Step 2: Fetching images from Freelex
* Step 3: Rename all images to meet Android requirements
* Step 4: Write out nzsl.dat for Android
* Step 5: Write out sqlite nzsl.db for iOS
* Step 6: Merge images together into one folder
* Step 6a: Generate search thumbnails
* Step 6b: Shrink images for distribution
* Step 7a: Update iOS app images
* Step 7b: Update iOS app nzsl.db
* Step 8a: Update Android app images
* Step 8b: Update Android app nzsl.dat
* Step 9: Cleanup (optional, requires -c flag)

To call the script you must provide the iOS and Android app base paths. The end result is your apps are updated with the latest sign databases and images, ready for building.

## freelex.py

Helper functions to interact with freelex and modify the files on the local file system.
