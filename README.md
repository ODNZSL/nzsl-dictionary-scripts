# nzsl-scripts

This repository holds scripts that are useful for the creation of the NZSL Android and iOS applications.


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

python3 ./build-assets.py 
```

## build-assets.py

This is a holistic script that performs all the steps needed to get all the necessary assets from the NZSL Freelex server. It does a number of steps:

* Step 1: Fetching the latest signs from Freelex
* Step 2: Fetching images from Freelex
* Step 3: Rename all images to meet Android requirements
* Step 4: Write out nzsl.dat for Android
* Step 5: Write out sqlite nzsl.db for iOS
* Step 6: Merge images together into one folder
* Step 6a: Generate search thumbnails
* Step 6b: Shrink images for distribution
* Step 7: Cleanup (optional, requires -c flag)

At the end of this process, you will find pictures (diagrams + search thumbnails), in the 'assets/` folder, and the
application databases in 'nzsl.dat' and 'nzsl.db'. The content of the two data files is the same, but they represent the 
data in different formats.

## freelex.py

Helper functions to interact with freelex and modify the files on the local file system.
