import os
import json
import shutil
from datetime import datetime
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from PIL import Image
from io import BytesIO

from config import ROAMING_DIR, LOCAL_DIR, DEFAULT_MUSIC_DIR


# ----------------------------------------------------------
# Ensure required directories exist
# ----------------------------------------------------------
BACKUP_DIR = os.path.join(ROAMING_DIR, "backups")
ARTWORK_DIR = os.path.join(LOCAL_DIR, "cache", "artwork")
OUTPUT_JSON = os.path.join(ROAMING_DIR, "music_metadata.json")

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(ARTWORK_DIR, exist_ok=True)


# ----------------------------------------------------------
# Save embedded artwork
# ----------------------------------------------------------
def save_artwork(mp3_path, stem):
    """Extract and save embedded album art. Returns relative artwork path or ''. """

    try:
        audio = ID3(mp3_path)
        for key in audio.keys():
            if key.startswith("APIC"):
                artwork_data = audio[key].data
                img = Image.open(BytesIO(artwork_data))
                filename = f"{stem}.jpg"
                full_path = os.path.join(ARTWORK_DIR, filename)
                img.convert("RGB").save(full_path, "JPEG")

                # store relative path (inside LOCAL_DIR)
                return os.path.relpath(full_path, LOCAL_DIR)

    except Exception:
        pass

    return ""


# ----------------------------------------------------------
# Extract metadata for a single MP3
# ----------------------------------------------------------
def extract_metadata(mp3_path):
    """Return a dictionary of tags for one MP3 file."""

    try:
        tags = EasyID3(mp3_path)
    except Exception:
        tags = {}

    stem = os.path.splitext(os.path.basename(mp3_path))[0]

    metadata = {
        "title": tags.get("title", [stem])[0],
        "album_artist": tags.get("albumartist", [""])[0],
        "album": tags.get("album", [""])[0],
        "publisher": tags.get("organization", [""])[0],
        "disc_number": tags.get("discnumber", [""])[0],
        "track_number": tags.get("tracknumber", [""])[0],
        "total_discs": tags.get("disctotal", [""])[0] if "disctotal" in tags else "",
        "year": tags.get("date", [""])[0],
        "genre": tags.get("genre", [""])[0],
        "composer": tags.get("composer", [""])[0],
        "artwork": "",
    }

    rel_art = save_artwork(mp3_path, stem)
    if rel_art:
        metadata["artwork"] = rel_art

    return metadata


# ----------------------------------------------------------
# Make backup of music_metadata.json
# ----------------------------------------------------------
def backup_metadata_file():
    if not os.path.exists(OUTPUT_JSON):
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"music_metadata_{timestamp}.json"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    try:
        shutil.copy2(OUTPUT_JSON, backup_path)
    except Exception:
        return

    # keep only latest 10
    try:
        backups = sorted(
            [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR)
             if f.startswith("music_metadata_")],
            key=os.path.getmtime,
            reverse=True
        )
        for old in backups[10:]:
            os.remove(old)
    except Exception:
        pass


# ----------------------------------------------------------
# PUBLIC FUNCTION:
# Rebuild metadata library (called by LibraryTab)
# ----------------------------------------------------------
def rebuild_music_metadata():
    music_dir = DEFAULT_MUSIC_DIR

    # Load existing metadata
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}
    else:
        metadata = {}

    backup_metadata_file()

    found = set()
    new_count = 0

    for root, _, files in os.walk(music_dir):
        for f in files:
            if f.lower().endswith(".mp3"):
                full_path = os.path.join(root, f)
                found.add(full_path)

                if full_path not in metadata:
                    metadata[full_path] = extract_metadata(full_path)
                    new_count += 1

    # files removed from library
    removed = set(metadata.keys()) - found
    for dead in removed:
        art_rel = metadata[dead].get("artwork", "")
        if art_rel:
            art_abs = os.path.join(LOCAL_DIR, art_rel)
            if os.path.exists(art_abs):
                try:
                    os.remove(art_abs)
                except Exception:
                    pass
        del metadata[dead]

    # Save updated file
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    return {
        "total": len(metadata),
        "new": new_count,
        "removed": len(removed),
    }
