import sys
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import shutil
import sqlite3

def fetch_database(filename):
    r = urllib.request.urlopen('https://nzsl-assets.vuw.ac.nz/dnzsl/freelex/publicsearch?xmldump=1')
    with open(filename, "wb") as f:
        f.write(r.read())


def fetch_assets(root):
    for entry in root.iter("entry"):
        print(entry.find("headword").text)
        for asset in entry.find("ASSET"):
            if ("picture" == asset.tag):
                fn = os.path.join(asset.tag, asset.text)
                if not os.path.exists(fn):
                    try:
                        os.makedirs(os.path.dirname(fn))
                    except IOError:
                        pass
                    r = urllib.request.urlopen("https://nzsl-assets.vuw.ac.nz/dnzsl/freelex/assets/" +       urllib.parse.quote(asset.text))
                    with open(fn, "wb") as f:
                        f.write(r.read())

# Modify filenames to match the Android requirements (lowercase a-z and _ only)
# Since iOS uses the same data source (the .dat file), update iOS to use the same image names.
def normalize_image_filename(filename):
    normalized_filename = filename.replace('-', '_').lower()
    num_of_periods = normalized_filename.count('.')
    if (num_of_periods > 1):
        normalized_filename = normalized_filename.replace('.', '_', num_of_periods - 1)

    return normalized_filename


def rename_assets(root):
     for entry in root.iter("entry"):
         for asset in entry.find("ASSET"):
             if ("picture" == asset.tag):
                 old_filename = os.path.join(asset.tag, asset.text)
                 if not os.path.isfile(old_filename):
                     print("Picture {} does not exist!", old_filename)
                     continue
                 new_filename = normalize_image_filename(old_filename)
                 os.rename(old_filename, new_filename)
                 asset.text = new_filename.replace('picture/', '', 1)

def write_datfile(root):
    with open("nzsl.dat", "w") as f:
        for entry in root.iter("entry"):
            headword = entry.attrib["id"], entry.find("headword").text
            sec = entry.find("glosssecondary")
            maori = entry.find("glossmaori")
            picture = entry.find("ASSET/picture")
            video = entry.find("ASSET/glossmain")
            handshape = entry.find("handshape")
            if picture is None:
                print("{} missing picture".format(headword))
            if video is None:
                print("{} missing video".format(headword))
            if handshape is None:
                print("{} missing handshape".format(headword))
            print("\t".join([
                entry.find("glossmain").text,
                sec.text if sec is not None else "",
                maori.text if maori is not None else "",
                os.path.basename(normalize_image_filename(picture.text)) if picture is not None else "",
                "https://nzsl-assets.vuw.ac.nz/dnzsl/freelex/assets/"+video.text.replace(".webm", ".mp4") if video is not None else   "",
                handshape.text if handshape is not None else "",
                entry.find("location").text,
            ]), file=f)

def write_sqlitefile():
    if os.path.exists("nzsl.db"):
        os.unlink("nzsl.db")
    db = sqlite3.connect("nzsl.db")
    db.execute("create table words (gloss, minor, maori, picture, video, handshape, location, target)")
    with open("nzsl.dat") as f:
        for s in f:
            a = s.strip().split("\t")
            a.append("{}|{}|{}".format(normalise(a[0]), normalise(a[1]), normalise(a[2])))
            assert all(32 <= ord(x) < 127 for x in a[-1]), a[-1]
            db.execute("insert into words values (?, ?, ?, ?, ?, ?, ?, ?)", a)
    db.commit()
    db.close()

def copy_images_to_one_folder():
    if (os.path.isdir("assets")):
        shutil.rmtree("assets")
    os.makedirs("assets")
    os.system("cp picture/*/*.png assets/ 2>/dev/null")

# Helper functions
def normalise(s):
    return (s.lower()
             .replace("ā", "a")
             .replace("ē", "e")
             .replace("é", "e")
             .replace("ī", "i")
             .replace("ō", "o")
             .replace("ū", "u"))

