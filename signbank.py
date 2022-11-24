import csv
import os
import re
import shutil
import sqlite3
import sys

import requests
from requests.adapters import HTTPAdapter, Retry

DEFAULT_SIGNBANK_HOST = os.getenv("SIGNBANK_HOST", "https://signbank.nzsl.nz")
SIGNBANK_DATASET_ID = os.getenv("SIGNBANK_DATASET_ID", 1)
SIGNBANK_USERNAME = os.getenv("SIGNBANK_USERNAME")
SIGNBANK_PASSWORD = os.getenv("SIGNBANK_PASSWORD")


def signbank_session():
    s = requests.Session()
    s.get("%s/accounts/login/" % DEFAULT_SIGNBANK_HOST)
    s.post("%s/accounts/login/" % DEFAULT_SIGNBANK_HOST,
           data={'username': SIGNBANK_USERNAME, 'password': SIGNBANK_PASSWORD,
                 'csrfmiddlewaretoken': s.cookies['csrftoken']},
           headers={'Referer': DEFAULT_SIGNBANK_HOST})

    return s


def s3_session():
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1,
                    status_forcelist=[502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))

    return s

##########################
# Dictionary data handling
##########################


def fetch_gloss_export_file(filename):
    session = signbank_session()
    response = session.get("%s/dictionary/advanced/" % DEFAULT_SIGNBANK_HOST,
                           params={"dataset": SIGNBANK_DATASET_ID, "published": 'on', "format": 'CSV'})
    response.raise_for_status()
    with open(filename, "wb") as f:
        f.write(response.content)


def parse_signbank_csv(filename):
  with open(filename, 'r') as f:
    reader = csv.reader(f)
    headers = next(reader, None)
    return [{h: x for (h, x) in zip(headers, row)} for row in reader]


##########################
# Asset handling
##########################
def fetch_gloss_asset_export_file(filename):
    session = signbank_session()
    video_response = session.get("%s/video/csv" % DEFAULT_SIGNBANK_HOST)
    video_response.raise_for_status()
    with open(filename, "wb") as f:
        f.write(video_response.content)


def fetch_gloss_assets(data, database_filename, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    db = sqlite3.connect(database_filename)
    db.executescript(
        """
        BEGIN;
        CREATE TABLE videos (
            word_id, video_type, filename, url, display_order
        );
        CREATE UNIQUE INDEX idx_word_videos ON videos (word_id, video_type, filename);
        COMMIT;
      """
    )

    # data = data[0:100]  # Testing, only process the first 100 lines
    for entry in data:
        print(f"{entry['Gloss']} ({entry['Video_type']})", end=" ")
        gloss_parts = entry['Gloss'].split(':')
        if (len(gloss_parts) < 2):
            print(f"skipped - couldn't extract gloss ID")
            continue

        gloss = ":".join(gloss_parts[0:-1])
        gloss_id = gloss_parts[-1]
        video_type = entry['Video_type']
        url = entry['Videofile']

        basename = normalize_asset_filename(entry['Title'])
        filename = os.path.join(output_folder, basename)

        if filename.endswith(".webm"):
            print("skipped - webm video")
            continue

        # We don't need to download videos, just know where they are
        if filename.endswith(".png"):
            if not os.path.exists(filename):
                asset_request = s3_session().get(entry['Videofile'])
                with open(filename, "wb") as asset_file:
                    asset_file.write(asset_request.content)
                print("downloaded", end=", ")
            else:
                print("already downloaded", end=", ")
        else:
            print("not an image, skipping download", end=", ")

        # Update the words table with the picture, if this is an image and of type main
        if video_type == 'main' and filename.endswith('.png'):
            db.execute("UPDATE words SET picture = :basename WHERE id = :gloss_id",
                       {'basename': basename, 'gloss_id': gloss_id})
            print(" assigned as main picture", end=", ")

        # Update the words table with the video URL, if this is a video and of type main
        if video_type == 'main' and filename.endswith('.mp4'):
            db.execute(
                "UPDATE words SET video = :url WHERE id = :gloss_id",
                {'gloss_id': gloss_id, 'url': url}
            )
            print("assigned as main video", end=", ")

        # Insert the video data
        db.execute(
            """
            INSERT INTO videos (word_id, video_type, filename, url, display_order)
                        VALUES (:word_id, :video_type, :filename, :url, :display_order)
                        ON CONFLICT DO NOTHING
            """, {
                'word_id': gloss_id,
                'video_type': video_type,
                'filename': basename,
                'url': url,
                'display_order': entry['Version']
            }
        )
        db.commit()
        print("added to database")

# Modify filenames to match the Android requirements (lowercase a-z and _ only)
# Since iOS uses the same underlying data, update iOS to use the same image names.


def normalize_asset_filename(filename):
    normalized_filename = filename.replace('-', '_').lower()
    num_of_periods = normalized_filename.count('.')
    if (num_of_periods > 1):
        normalized_filename = normalized_filename.replace(
            '.', '_', num_of_periods - 1)

        return normalized_filename
    else:
        return normalized_filename


def write_datfile(database_filename, dat_file_filename):
    db = sqlite3.connect(database_filename)
    db.row_factory = sqlite3.Row
    with open(dat_file_filename, "w") as f:
        for row in db.execute("SELECT * FROM words"):
            print("\t".join([
                row['gloss'] or '',
                row['minor'] or '',
                row['maori'] or '',
                row['picture'] or '',
                row['video'] or '',
                row['handshape'] or '',
                row['location']
            ]), file=f)


def write_sqlitefile(data, database_filename):
    if os.path.exists(database_filename):
        os.unlink(database_filename)
    db = sqlite3.connect(database_filename)
    db.execute(
        """
        create table words (
          gloss, minor, maori, picture, video, handshape, location, location_identifier, target, age_groups,
          contains_numbers boolean, hint, id, inflection_manner_and_degree boolean, inflection_plural boolean,
          inflection_temporal boolean, is_directional boolean, is_fingerspelling boolean, is_locatable boolean,
          one_or_two_handed boolean, related_to, usage, usage_notes, word_classes, gloss_normalized,
          minor_normalized, maori_normalized
        )
      """
    )

    for entry in data:
        target = "{}|{}|{}".format(
            normalise(entry['gloss_main']), normalise(entry['gloss_secondary']), normalise(entry['gloss_maori']))
        entry.update({
            "target": target,
            "gloss_normalized": normalise(entry["gloss_main"]),
            "minor_normalized": normalise(entry["gloss_secondary"]),
            "maori_normalized": normalise(entry["gloss_maori"]),
            "location_identifier": entry["location_name"],
            "location": normalize_location(entry["location_name"])
        })
        db.execute(
            """
            INSERT INTO words VALUES(
              :gloss_main,
              :gloss_secondary,
              :gloss_maori,
              '',
              '',
              :handshape,
              :location,
              :location_identifier,
              :target,
              :age_groups,
              :contains_numbers,
              :hint,
              :id,
              :inflection_manner_and_degree,
              :inflection_plural,
              :inflection_temporal,
              :is_directional,
              :is_fingerspelling,
              :is_locatable,
              :one_or_two_handed,
              :related_to,
              :usage,
              :usage_notes,
              :word_classes,
              :gloss_normalized,
              :minor_normalized,
              :maori_normalized
            )
          """, entry)
    db.commit()
    db.close()


def copy_images_to_one_folder(source, dest):
    if (os.path.isdir(dest)):
        shutil.rmtree(dest)
    os.makedirs(dest)

    # Warning: This is very shell-injectable
    os.system(f"cp {source}/*.png {dest}/ 2>/dev/null")

# Helper functions


def normalize_location(location_str):
    return re.sub(r'\A\d{2} - ', '', location_str)


def normalise(s):
    return (s.lower()
            .replace("ā", "a")
             .replace("ē", "e")
            .replace("é", "e")
             .replace("ī", "i")
            .replace("ō", "o")
            .replace("ū", "u"))
