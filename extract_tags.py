import os
import json
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
from PIL import Image
from io import BytesIO

# === CONFIGURATION ===
MUSIC_DIR = r"C:\Users\kylej\Music"
OUTPUT_JSON = "music_metadata.json"
ARTWORK_DIR = os.path.join("cache", "artwork")

# === Ensure folders exist ===
os.makedirs(ARTWORK_DIR, exist_ok=True)

# === Helper: Save artwork bytes to image file ===
def save_artwork(tag, filename_stem):
    """Extract and save album art (if found) to cache/artwork/, return its path."""
    try:
        audio = ID3(tag)
        for key in audio.keys():
            if key.startswith("APIC"):
                artwork_data = audio[key].data
                image = Image.open(BytesIO(artwork_data))
                artwork_filename = f"{filename_stem}.jpg"
                artwork_path = os.path.join(ARTWORK_DIR, artwork_filename)
                image.convert("RGB").save(artwork_path, "JPEG")
                return artwork_path
    except Exception:
        pass
    return ""  # No artwork found


# === Helper: Extract metadata for one file ===
def extract_metadata(mp3_path):
    """Return a dict of tag data for a single MP3 file."""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        tags = EasyID3(mp3_path)
    except Exception:
        # Non-ID3 file or unreadable
        tags = {}

    # Derive a safe filename stem (for artwork)
    filename_stem = os.path.splitext(os.path.basename(mp3_path))[0]

    # Extract fields safely
    metadata = {
        "title": tags.get("title", [filename_stem])[0],
        "album_artist": tags.get("albumartist", [""])[0],
        "album": tags.get("album", [""])[0],
        "publisher": tags.get("organization", [""])[0],
        "disc_number": tags.get("discnumber", [""])[0],
        "track_number": tags.get("tracknumber", [""])[0],
        "total_discs": tags.get("disctotal", [""])[0] if "disctotal" in tags else "",
        "year": tags.get("date", [""])[0],
        "genre": tags.get("genre", [""])[0],
        "composer": tags.get("composer", [""])[0],
        "artwork": ""
    }

    # Try to extract embedded artwork
    artwork_path = save_artwork(mp3_path, filename_stem)
    if artwork_path:
        metadata["artwork"] = artwork_path

    return metadata


# === Main routine ===
def build_metadata_library():
    print(f"🎧 Scanning music directory: {MUSIC_DIR}")
    music_metadata = {}
    count_total = 0
    count_with_tags = 0
    count_with_art = 0

    for root, _, files in os.walk(MUSIC_DIR):
        for file in files:
            if file.lower().endswith(".mp3"):
                count_total += 1
                full_path = os.path.join(root, file)
                meta = extract_metadata(full_path)
                if any(v for k, v in meta.items() if k != "artwork"):
                    count_with_tags += 1
                if meta["artwork"]:
                    count_with_art += 1
                music_metadata[full_path] = meta

    # Save to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(music_metadata, f, indent=4, ensure_ascii=False)

    print(f"✅ Metadata extraction complete.")
    print(f"   Total songs processed: {count_total}")
    print(f"   Songs with tag data:   {count_with_tags}")
    print(f"   Songs with artwork:    {count_with_art}")
    print(f"📁 Output: {OUTPUT_JSON}")
    print(f"🖼 Artwork cache: {ARTWORK_DIR}")


if __name__ == "__main__":
    build_metadata_library()
