import os
import glob
import shutil
import time

# === CONFIGURATION ===
ONEDRIVE_DATA_DIR = os.path.expandvars(r"%USERPROFILE%\OneDrive\MusicPlayerData")
KEEP_COUNT = 2  # Number of newest backups to keep

def cleanup_backups(prefix):
    """Keep only the newest KEEP_COUNT JSON backups for each prefix."""
    pattern = os.path.join(ONEDRIVE_DATA_DIR, f"{prefix}_backup_*.json")
    backups = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)

    if len(backups) <= KEEP_COUNT:
        print(f"✅ {prefix.capitalize()}: {len(backups)} backups found — no cleanup needed.")
        return

    to_delete = backups[KEEP_COUNT:]
    for file_path in to_delete:
        try:
            os.remove(file_path)
            print(f"🗑️ Deleted old {prefix} backup → {os.path.basename(file_path)}")
        except Exception as e:
            print(f"⚠️ Could not delete {file_path}: {e}")

def cleanup_artwork_backups():
    """Clean up artwork backup folders (keep newest N)."""
    all_folders = [
        f for f in os.listdir(ONEDRIVE_DATA_DIR)
        if f.startswith("artwork_backup_")
    ]
    all_folders = sorted(
        all_folders,
        key=lambda f: os.path.getmtime(os.path.join(ONEDRIVE_DATA_DIR, f)),
        reverse=True
    )

    to_delete = all_folders[KEEP_COUNT:]
    for folder in to_delete:
        full_path = os.path.join(ONEDRIVE_DATA_DIR, folder)
        try:
            shutil.rmtree(full_path, ignore_errors=False)
            print(f"🧹 Deleted old artwork backup → {folder}")
        except PermissionError:
            print(f"⚠️ Skipped locked folder (OneDrive busy): {folder}")
        except Exception as e:
            print(f"⚠️ Could not delete {folder}: {e}")
        time.sleep(0.1)

def main():
    print("\n=== 🎵 Kyle's OneDrive Backup Cleanup ===")
    print(f"Target directory: {ONEDRIVE_DATA_DIR}\n")

    cleanup_backups("library")
    cleanup_backups("metadata")
    cleanup_backups("playlists")
    cleanup_artwork_backups()

    print("\n✅ Cleanup complete! Only the newest backups were kept.\n")

if __name__ == "__main__":
    main()
