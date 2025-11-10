import os

# ----------------------------------------------------------
# 🧩 Kyle’s Music Player – Configuration & Paths
# ----------------------------------------------------------
# This file defines all persistent folders and data locations.
# It ensures your app always uses the same trusted directories
# (no matter where the EXE or dev code runs from).
# ----------------------------------------------------------

APP_NAME = "KyleMusicPlayer"

# === 1️⃣ Define the core Windows AppData directories ===
ROAMING_DIR = os.path.join(os.getenv("APPDATA"), APP_NAME)      # For user data (playlists, metadata, backups)
LOCAL_DIR   = os.path.join(os.getenv("LOCALAPPDATA"), APP_NAME) # For cache, artwork, and other large files

# === 2️⃣ OneDrive integration path (auto-detected) ===
# Used for cross-device backup and playlist sync.
# This resolves safely even if OneDrive is disabled.
ONEDRIVE_DATA_DIR = os.path.join(
    os.path.expanduser("~"),
    "OneDrive",
    "MusicPlayerData"
)
os.makedirs(ONEDRIVE_DATA_DIR, exist_ok=True)

# === 3️⃣ Make sure those folders exist safely ===
# These only create folders if missing — they NEVER delete or overwrite files.
os.makedirs(ROAMING_DIR, exist_ok=True)
os.makedirs(LOCAL_DIR, exist_ok=True)
os.makedirs(os.path.join(LOCAL_DIR, "cache", "artwork"), exist_ok=True)
os.makedirs(os.path.join(ROAMING_DIR, "backups"), exist_ok=True)

# === 4️⃣ Define standard file locations ===
PLAYLISTS_FILE = os.path.join(ROAMING_DIR, "playlists.json")
METADATA_FILE  = os.path.join(ROAMING_DIR, "music_metadata.json")
CACHE_FILE     = os.path.join(LOCAL_DIR, "library_cache.json")
ARTWORK_DIR    = os.path.join(LOCAL_DIR, "cache", "artwork")
BACKUP_DIR     = os.path.join(ROAMING_DIR, "backups")

# === 5️⃣ Optional: Define your main music source (customize this freely) ===
DEFAULT_MUSIC_DIR = os.path.expandvars(r"%USERPROFILE%\Music")

# === 6️⃣ Version tag (for internal migrations later) ===
APP_VERSION = "1.0.0"

# === 7️⃣ Sanity check (development only) ===
if __name__ == "__main__":
    print(f"✅ {APP_NAME} configuration loaded.")
    print(f"Roaming data : {ROAMING_DIR}")
    print(f"Local cache  : {LOCAL_DIR}")
    print(f"OneDrive dir : {ONEDRIVE_DATA_DIR}")
    print(f"Playlists    : {PLAYLISTS_FILE}")
    print(f"Metadata     : {METADATA_FILE}")
    print(f"Artwork dir  : {ARTWORK_DIR}")
    print(f"Backups dir  : {BACKUP_DIR}")
