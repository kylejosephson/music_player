import os
import json
import requests
import msal
from datetime import datetime
from pathlib import Path
from msal import SerializableTokenCache

# ============================================
# CONFIGURATION
# ============================================
CLIENT_ID = "66c23531-a11d-4108-b037-f7547b9ea2ee"
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Files.ReadWrite", "User.Read"]

# Use a global token cache under AppData\Local\MusicPlayer
APPDATA_PATH = Path(os.getenv("LOCALAPPDATA", "")) / "MusicPlayer"
APPDATA_PATH.mkdir(parents=True, exist_ok=True)

TOKEN_CACHE_FILE = APPDATA_PATH / "token_cache.json"
PLAYLIST_FILE = "playlists.json"
BACKUP_FILE = "playlists_backup_onedrive.json"

print(f"🔒 Using global token cache: {TOKEN_CACHE_FILE}")

# ============================================
# AUTHENTICATION (Persistent + Auto Refresh)
# ============================================
def get_access_token(force_refresh=False):
    """Authenticate user and return a valid access token with persistent MSAL cache."""
    cache = SerializableTokenCache()
    if TOKEN_CACHE_FILE.exists():
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            cache.deserialize(f.read())

    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)

    # Try to use cached account
    accounts = app.get_accounts()
    result = None
    if accounts and not force_refresh:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # If silent token is missing or expired, refresh automatically
    if not result or "access_token" not in result:
        if accounts:
            print("🔄 Token expired — refreshing silently...")
            result = app.acquire_token_silent_with_error(SCOPES, account=accounts[0])
        if not result or "access_token" not in result:
            print("🔐 Silent refresh failed. User re-authentication required.")
            flow = app.initiate_device_flow(scopes=SCOPES)
            if "user_code" not in flow:
                raise Exception("Device flow failed to start. Please try again.")
            print("\n🔐 To sign in:")
            print(f"➡ Go to: {flow['verification_uri']}")
            print(f"➡ Enter this code: {flow['user_code']}")
            print("Then return here once signed in...\n")
            result = app.acquire_token_by_device_flow(flow)

    # Save updated cache (including new refresh tokens)
    if cache.has_state_changed:
        TOKEN_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(cache.serialize())

    if "access_token" in result:
        if force_refresh:
            print("✅ Token successfully refreshed and re-cached.")
        else:
            print("✅ Login successful! Token cached for future use.")
        return result["access_token"]
    else:
        raise Exception(f"Authentication failed: {result.get('error_description')}")

# ============================================
# ONEDRIVE SYNC
# ============================================
def upload_playlist_to_onedrive():
    """Upload local playlists.json to OneDrive root directory."""
    if not os.path.exists(PLAYLIST_FILE):
        print("⚠️ playlists.json not found.")
        return

    try:
        token = get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        upload_url = "https://graph.microsoft.com/v1.0/me/drive/root:/playlists.json:/content"

        with open(PLAYLIST_FILE, "rb") as f:
            response = requests.put(upload_url, headers=headers, data=f)

        # Auto-retry once if token expired mid-upload
        if response.status_code == 401:
            print("🔁 Token expired during upload — refreshing and retrying...")
            token = get_access_token(force_refresh=True)
            headers["Authorization"] = f"Bearer {token}"
            with open(PLAYLIST_FILE, "rb") as f:
                response = requests.put(upload_url, headers=headers, data=f)

        if response.status_code in (200, 201):
            print(f"✅ playlists.json uploaded to OneDrive at {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
        else:
            print(f"❌ Upload failed: {response.status_code} {response.text}")

    except Exception as e:
        print(f"⚠️ Upload error: {e}")


def download_playlist_from_onedrive():
    """Download playlists.json from OneDrive to local folder."""
    try:
        token = get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        url = "https://graph.microsoft.com/v1.0/me/drive/root:/playlists.json:/content"
        response = requests.get(url, headers=headers)

        # Retry if token expired
        if response.status_code == 401:
            print("🔁 Token expired during download — refreshing and retrying...")
            token = get_access_token(force_refresh=True)
            headers["Authorization"] = f"Bearer {token}"
            response = requests.get(url, headers=headers)

        if response.status_code == 200:
            if os.path.exists(PLAYLIST_FILE):
                backup_folder = "backups"
                os.makedirs(backup_folder, exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_path = os.path.join(backup_folder, f"playlist_local_backup_{timestamp}.json")
                os.rename(PLAYLIST_FILE, backup_path)
                print(f"🕒 Local backup created: {backup_path}")

            with open(PLAYLIST_FILE, "wb") as f:
                f.write(response.content)
            print(f"✅ playlists.json downloaded from OneDrive successfully.")
        else:
            print(f"❌ Download failed: {response.status_code} {response.text}")

    except Exception as e:
        print(f"⚠️ Download error: {e}")

# ============================================
# TESTING (Run this file directly)
# ============================================
if __name__ == "__main__":
    print("🎵 OneDrive Sync Utility")
    print("1. Upload playlists.json to OneDrive")
    print("2. Download playlists.json from OneDrive")
    choice = input("Select an option (1/2): ").strip()

    if choice == "1":
        upload_playlist_to_onedrive()
    elif choice == "2":
        download_playlist_from_onedrive()
    else:
        print("❌ Invalid selection.")
