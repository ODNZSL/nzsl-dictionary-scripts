# nzsl-scripts

This repository holds scripts that are useful for the creation of the NZSL Android and iOS applications.

## Quick access to assets

An scheduled build runs monthly to produce the assets and data files for the NZSL Dictionary applications to use.
If you are after these assets and are not interested in the absolute latest data, you can download these files without
having to wait for them to build from the [Releases](https://github.com/odnzsl/nzsl-dictionary-scripts/releases) tab.

## Prerelease builds

Aside from scheduled releases, prerelease builds may occasionally be run. This
build extracts sign data, but does not process assets like sign illustrations or
videos. Prerelease data is not published as a Github release or as build
artifacts, but is used to allow data to be checked in prerelease environments of
our apps.

## Deployment

This tool contains a number of [Github Actions](/actions) which can be manually run by repository administrators
to update the dictionary data used by [NZSL Share](https://nzslshare.nz) and the [NZSL Dictionary](https://nzsl.nz).

The deployment process is:

1. Download the sign data from Signbank, and process it into a SQLite database
2. Upload the SQLite database to an S3 bucket. This requires a role ARN, bucket
   name, and deployment ACL, which are specified as repository secrets and
   provisioned by https://github.com/odnzsl/nzsl-infrastructure.
3. Restarts the Heroku applications (these applications download the latest sign
   data on boot using a presigned URL). This requires a valid Heroku app name
   and API token to be configured, which are specified as repository secrets.
4. If the database being exported is a production release, the SQLite and .dat
   files produced are attached to the build as artifacts. Prerelease data is not
   available for download from the build and is limited for Prerelease app use
   (we use prereleases to perform a final check of data before publishing, but
   this sign data is not available for general use until this check is completed
   and the sign is published)

Configuration and secrets required for the deployment are managed by
[Ackama](https://ackama.com). If you are a Ackama staff member and require
access, this may be requested by messaging the Codecare team to request accesss
to the appropriate project vault.

## Build - Docker

A Dockerfile is provided in this repository to make it easier to run the scripts. A Makefile is provided with
some very simple commands to build and run the image.

You can run `make build update_assets` to build the Docker image and then generate the assets and database files.
Expect this process to take between 2 and 4 hours.

## Build - Non-Docker

To build without Docker, there are some dependencies you will need to have available on your PATH.

### python3

These scripts are written in Python 3 and will not work with Python 2.

If you are using OSX you can install it via

```
brew install python3
```

Debian/Ubuntu users have access to the python3 command.

### Imagemagick

Image compression requires the `mogrify` and `convert` commands from imagemagick

If you are using OSX you can install it via

```
brew install imagemagick
```

Debian/Ubuntu users will need to install it with

```
sudo apt-get install imagemagick
```

### Optipng

Image compression also uses `optipng` as the final step

If you are using OSX you can install it via

```
brew install optipng
```

Debian/Ubuntu users will need to install it with

```
sudo apt-get install optipng
```

## Usage summary

```
cd /path/to/this/repo

python3 ./build-assets-from-signbank.py
```

Expect this process to take between 2 and 4 hours. A valid Signbank user account is required and may be configured via the following environment variables:

* `DEFAULT_SIGNBANK_HOST`
* `SIGNBANK_USERNAME`
* `SIGNBANK_PASSWORD`

## build-assets-from-signbank.py

This is a holistic script that performs all the steps needed to get all the necessary assets from the NZSL Signbank server. It does a number of steps:

- Step 1: Fetching the latest signs from Signbank
- Step 2: Fetching images from Signbank
- Step 3: Rename all images to meet Android requirements
- Step 4: Write out nzsl.dat for Android
- Step 5: Write out sqlite nzsl.db for iOS
- Step 6: Merge images together into one folder
- Step 6a: Generate search thumbnails
- Step 6b: Shrink images for distribution
- Step 7: Cleanup (optional, requires -c flag)

At the end of this process, you will find pictures (diagrams + search thumbnails), in the 'assets/` folder, and the
application databases in 'nzsl.dat' and 'nzsl.db'. The content of the two data files is the same, but they represent the
data in different formats.

This script can be passed the following options:

* `--skip-assets`: The sign data will be extracted, but not assets. This
  substantially speeds up the export process, much of which is concerned with
  image resizing and transformation.
* `--cleanup`: Remove the exported files as soon as the script completes
* `--prerelease`: Export signs that are in the web-ready: check stage. This is
  determined by the `SIGNBANK_WEB_READY_TAG_ID` environmnent variable.

## signbank.py

Helper functions to interact with Signbank, DSRU's editorial system for managing the dictionary.

## image_processing.py

Helper functions to resize, compress and otherwise transform sign illustrations for app use.

## freelex.py

Helper functions to interact with freelex and modify the files on the local file system. Deprecated and unused, this file is kept for historical reference only.


## build-assets-from-freelex.py

Prior extraction script for the previous NZSL editorial system, Freelex. Deprecated and unused, this file is kept for historical reference only.
