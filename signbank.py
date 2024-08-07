import csv
import os
import re
import shutil
import sqlite3
import time

import requests
from datetime import datetime
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import ChunkedEncodingError
from urllib3.exceptions import ProtocolError

DEFAULT_SIGNBANK_HOST = os.getenv("SIGNBANK_HOST", "https://signbank.nzsl.nz")
SIGNBANK_DATASET_ID = os.getenv("SIGNBANK_DATASET_ID", 1)
SIGNBANK_USERNAME = os.getenv("SIGNBANK_USERNAME")
SIGNBANK_PASSWORD = os.getenv("SIGNBANK_PASSWORD")
SIGNBANK_WEB_READY_TAG_ID = os.getenv("SIGNBANK_WEB_READY_TAG_ID")

##
# Start a requests session that is authenticated to Signbank


def signbank_session():
    s = requests.Session()
    s.get(f"{DEFAULT_SIGNBANK_HOST}/accounts/login/")
    s.post(f"{DEFAULT_SIGNBANK_HOST}/accounts/login/",
           data={'username': SIGNBANK_USERNAME, 'password': SIGNBANK_PASSWORD,
                 'csrfmiddlewaretoken': s.cookies['csrftoken']},
           headers={'Referer': DEFAULT_SIGNBANK_HOST})

    return s

def get_from_s3(key):
    """
    Makes a GET request to S3, retrying a few times if it errors
    or if the connection is broken before giving up entirely

    :param key:
    :return:
    """
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1,
                    status_forcelist=[502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))

    # the above retry setup will handle occasional connection errors that are done
    # with a valid HTTP request, but they won't handle when the connection is just
    # broken, so we also have to explicitly catch protocol errors to attempt a retry
    try:
        return s.get(key)
    except (ProtocolError, ChunkedEncodingError):
        print("(had to retry get)", end=" ")
        time.sleep(2) # Wait a couple of seconds before retrying
        return get_from_s3(key)


##########################
# Dictionary data handling
##########################


def fetch_gloss_export_file(filename, filters = {}):
    session = signbank_session()
    response = session.get(f"{DEFAULT_SIGNBANK_HOST}/dictionary/advanced/",
                           params={**filters, "dataset": SIGNBANK_DATASET_ID, "format": 'CSV-standard'})
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
def fetch_gloss_asset_export_file(filename, filters = {}):
    session = signbank_session()

    video_response = session.get(f"{DEFAULT_SIGNBANK_HOST}/video/csv", params=filters)
    video_response.raise_for_status()
    with open(filename, "wb") as f:
        f.write(video_response.content)


def fetch_gloss_assets(data, database_filename, output_folder, download=True):
    if not os.path.exists(output_folder) and download:
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

    for entry in data:
        print(f"{entry['Gloss']} ({entry['Video_type']})", end=" ")
        gloss_parts = entry['Gloss'].split(':')
        if (len(gloss_parts) < 2):
            print(f"skipped - couldn't extract gloss ID")
            continue

        gloss_id = gloss_parts[-1]
        video_type = entry['Video_type']
        url = entry['Videofile']

        basename = normalize_asset_filename(entry['Title'])
        filename = os.path.join(output_folder, basename)

        if filename.endswith(".webm"):
            print("skipped - webm video")
            continue

        # We don't need to download videos, just know where they are
        if download and filename.endswith(".png"):
            if download and not os.path.exists(filename):
                asset_request = get_from_s3(entry['Videofile'])
                with open(filename, "wb") as asset_file:
                    asset_file.write(asset_request.content)
                print("downloaded", end=", ")
            else:
                print("already downloaded", end=", ")
        elif download:
            print("not an image, skipping download", end=", ")

        # Update the words table with the picture, if this is an image and of type main
        if video_type == 'main' and filename.endswith('.png'):
            db.execute("UPDATE words SET picture = :basename WHERE id = :gloss_id",
                       {'basename': basename, 'gloss_id': gloss_id})
            print("assigned as main picture", end=", ")

        # Update the words table with the video URL, if this is a video and of type main
        if video_type == 'main' and filename.endswith('.mp4'):
            db.execute(
                "UPDATE words SET video = :url WHERE id = :gloss_id",
                {'gloss_id': gloss_id, 'url': url}
            )
            print("assigned as main video", end=", ")

        if video_type.startswith("finalexample"):
            # finalexample{1,2,3,4} - this won't scale to double digits
            display_order = int(video_type[-1])
            db.execute("UPDATE examples SET video = :url WHERE word_id = :gloss_id AND display_order = :display_order",
                       {'display_order': display_order, 'gloss_id': gloss_id, 'url': url})

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


def prune_orphan_assets(database_filename):
    db = sqlite3.connect(database_filename)
    cursor = db.cursor()
    cursor.execute(
        """
        DELETE FROM videos
        WHERE word_id NOT IN (SELECT word_id FROM words);
        """
    )
    deleted_records = cursor.rowcount
    print(f"Pruned {deleted_records} assets not associated with a word")



def normalize_asset_filename(filename):
    normalized_filename = filename.replace('-', '_').lower()
    num_of_periods = normalized_filename.count('.')
    if (num_of_periods > 1):
        normalized_filename = normalized_filename.replace(
            '.', '_', num_of_periods - 1)

        return normalized_filename
    else:
        return normalized_filename


# The .dat file is used by the Android application, rather than SQLite, for
# historical reasons. It only includes the data required by the application, not
# including new data added to the SQLite database.

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

# The SQLite database is used by all primary applications other than the Android application.
# It includes a table containing the core dictionary data (words), and references to assets (videos).
# Generally, vocabulary follows historical terminology rather than aligning with Signbank at this stage.


def write_sqlitefile(data, database_filename):
    if os.path.exists(database_filename):
        os.unlink(database_filename)
    db = sqlite3.connect(database_filename)

    version = datetime.utcnow().strftime("%Y%m%d")
    db.execute(f"PRAGMA user_version = {version}")

    db.execute(
        """
        create table words (
          gloss, minor, maori, picture, video, handshape, location, location_identifier, variant_number, target, age_groups,
          contains_numbers boolean, hint, id PRIMARY KEY, inflection_manner_and_degree boolean, inflection_plural boolean,
          inflection_temporal boolean, is_directional boolean, is_fingerspelling boolean, is_locatable boolean,
          one_or_two_handed boolean, related_to, usage, usage_notes, word_classes, gloss_normalized,
          minor_normalized, maori_normalized
        )
      """
    )

    for entry in data:
        target = "{}|{}|{}".format(
            normalise(entry['gloss_main']), normalise(entry['gloss_secondary']), normalise(entry['gloss_maori']))

        # Transform 'True'/'False' to boolean values - 0/1
        entry = {k: v if v not in ("True", "False") else (
            1 if v == "True" else 0) for k, v in entry.items()}

        # Augment entry with additional attributes
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
              :variant_number,
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
            ) ON CONFLICT DO NOTHING
          """, entry)
        add_examples(entry, db)
        add_topics(entry, db)
    db.commit()
    db.close()


def add_topics(entry, db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS topics (name varchar PRIMARY KEY UNIQUE)")
    db.execute("CREATE TABLE IF NOT EXISTS word_topics (word_id, topic_name)")
    for topic_name in entry["semantic_field"].split("; "):
        topic_name = topic_name.strip()
        if not topic_name:
            continue
        db.execute("INSERT INTO topics VALUES (:name) ON CONFLICT DO NOTHING",
                   {"name": topic_name})
        db.execute("INSERT INTO word_topics VALUES (:word_id, :topic_name) ON CONFLICT DO NOTHING",
                   {"word_id":  entry["id"], "topic_name": topic_name})

def add_examples(entry, db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS examples (word_id, display_order, sentence, translation, video)")

    for i in [1, 2, 3, 4]:
        sentence = entry[f"videoexample{i}"]
        if not sentence:
            continue

        db.execute(
            "INSERT INTO examples VALUES (:word_id, :display_order, :sentence, :translation, NULL)",
            {
                "word_id": entry["id"],
                "display_order": i,
                "sentence": sentence,
                "translation": entry[f"videoexample{i}_translation"]
            }
        )

def copy_images_to_one_folder(source, dest):
    if (os.path.isdir(dest)):
        shutil.rmtree(dest)
    os.makedirs(dest)

    # Warning: This is very shell-injectable
    os.system(f"cp {source}/*.png {dest}/ 2>/dev/null")

# Helper functions


def normalize_location(location_str):
    return re.sub(r'\A\d{2} - ', '', location_str)

##
# Replace accented characters with their lowercased, unaccented equivalents.
# Note that this is a non-exhaustive list, and there are more resilient ways to do this.


def normalise(s):
    return (s.lower()
            .replace("ā", "a")
             .replace("ē", "e")
            .replace("é", "e")
             .replace("ī", "i")
            .replace("ō", "o")
            .replace("ū", "u"))
