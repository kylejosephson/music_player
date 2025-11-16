import os

# ----------------------------------------------------------
# 🧩 Kyle’s Music Player – Configuration & Paths
# ----------------------------------------------------------
APP_NAME = "KyleMusicPlayer"

# === 1️⃣ Define the core Windows AppData directories ===
ROAMING_DIR = os.path.join(os.getenv("APPDATA"), APP_NAME)
LOCAL_DIR   = os.path.join(os.getenv("LOCALAPPDATA"), APP_NAME)

# === 2️⃣ OneDrive integration path ===
ONEDRIVE_DATA_DIR = os.path.join(
    os.path.expanduser("~"),
    "OneDrive",
    "MusicPlayerData"
)
os.makedirs(ONEDRIVE_DATA_DIR, exist_ok=True)

# === 3️⃣ Ensure required directories exist ===
os.makedirs(ROAMING_DIR, exist_ok=True)
os.makedirs(LOCAL_DIR, exist_ok=True)
os.makedirs(os.path.join(LOCAL_DIR, "cache", "artwork"), exist_ok=True)
os.makedirs(os.path.join(ROAMING_DIR, "backups"), exist_ok=True)

# === 4️⃣ Standard file locations ===
PLAYLISTS_FILE = os.path.join(ROAMING_DIR, "playlists.json")
METADATA_FILE  = os.path.join(ROAMING_DIR, "music_metadata.json")
CACHE_FILE     = os.path.join(LOCAL_DIR, "library_cache.json")
ARTWORK_DIR    = os.path.join(LOCAL_DIR, "cache", "artwork")
BACKUP_DIR     = os.path.join(ROAMING_DIR, "backups")

# === 5️⃣ Default music directory ===
DEFAULT_MUSIC_DIR = os.path.expandvars(r"%USERPROFILE%\Music")

# === 6️⃣ Version tag ===
APP_VERSION = "1.0.0"


# ----------------------------------------------------------
# 🧪 Development Mode (only executed when running config.py directly)
# ----------------------------------------------------------
if __name__ == "__main__":
    # Avoid circular import unless running this file by itself
    try:
        from safe_print import safe_print
    except Exception:
        # Fallback if main.py not available
        def safe_print(x): print(x)

    safe_print(f"{APP_NAME} configuration loaded.")
    safe_print(f"Roaming data : {ROAMING_DIR}")
    safe_print(f"Local cache  : {LOCAL_DIR}")
    safe_print(f"OneDrive dir : {ONEDRIVE_DATA_DIR}")
    safe_print(f"Playlists    : {PLAYLISTS_FILE}")
    safe_print(f"Metadata     : {METADATA_FILE}")
    safe_print(f"Artwork dir  : {ARTWORK_DIR}")
    safe_print(f"Backups dir  : {BACKUP_DIR}")
