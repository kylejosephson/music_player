import os
import json
import requests
import msal
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================
CLIENT_ID = "66c23531-a11d-4108-b037-f7547b9ea2ee"
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Files.ReadWrite", "User.Read"]

# === Global Token Cache (Option B) ===
# Store the token globally so all future versions (desktop, phone, etc.) can share it
APPDATA_DIR = os.path.join(os.getenv("LOCALAPPDATA"), "MusicPlayer")
os.makedirs(APPDATA_DIR, exist_ok=True)
TOKEN_CACHE_FILE = os.path.join(APPDATA_DIR, "token_cache.json")

print(f"🔒 Using global token cache: {TOKEN_CACHE_FILE}")
PLAYLIST_FILE = "playlists.json"
BACKUP_FILE = "playlists_backup_onedrive.json"


# ============================================
# AUTHENTICATION
# ============================================
def load_token_cache():
    """Load cached tokens if available."""
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_token_cache(token_data):
    """Save tokens to local cache."""
    with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=4)


def get_access_token():
    """Authenticate the user and return a valid access token."""
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

    token_data = load_token_cache()
    if token_data:
        accounts = app.get_accounts()
        result = app.acquire_token_silent(SCOPES, account=accounts[0]) if accounts else None
        if result and "access_token" in result:
            return result["access_token"]

    # Interactive login (first time)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise Exception("Device flow failed to start. Please try again.")
    print("\n🔐 To sign in:")
    print(f"➡ Go to: {flow['verification_uri']}")
    print(f"➡ Enter this code: {flow['user_code']}")
    print("Then return here once signed in...\n")

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        save_token_cache(result)
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

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    upload_url = "https://graph.microsoft.com/v1.0/me/drive/root:/playlists.json:/content"

    with open(PLAYLIST_FILE, "rb") as f:
        response = requests.put(upload_url, headers=headers, data=f)

    if response.status_code in (200, 201):
        print(f"✅ playlists.json uploaded to OneDrive at {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
    else:
        print(f"❌ Upload failed: {response.status_code} {response.text}")


def download_playlist_from_onedrive():
    """Download playlists.json from OneDrive to local folder."""
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    url = "https://graph.microsoft.com/v1.0/me/drive/root:/playlists.json:/content"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Backup current local file before overwriting
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
