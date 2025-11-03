🎵 Kyle’s Music Player

A custom-built Python + PyQt5 desktop music player with playlist management, OneDrive sync integration, and local library caching.

🚀 Features
🎶 Music Player Tab

Play, pause, skip, and seek songs

Real-time progress bar with smooth updates

Automatic queue management and looping control

📜 Playlist Manager

Create, save, delete, and load playlists

Auto-backup system with timestamped copies

Double-click to instantly load a playlist into the player

📚 Music Library

Scans your local music directory automatically

Caches results for faster load times

Double-click songs to add to both player and playlist builder

☁️ OneDrive Sync

Syncs playlists and songs between local and cloud

Detects missing or out-of-sync playlists (lists names)

“Force Refresh” button for manual control

🧠 Tech Stack

Language: Python 3.11+

Framework: PyQt5 (GUI)

Audio Engine: Pygame + Mutagen

Cloud Sync: Microsoft Graph API via MSAL

Version Control: Git + GitHub

🗂 Project Structure

C:\Dev\Music_Player_Folder

main.py — App entry point

player_tab.py — Music player logic

playlist_tab.py — Playlist manager UI + backend

library_tab.py — Library management and cache

sync_tab.py — OneDrive sync interface

onedrive_sync.py — Handles Graph API authentication

library_cache.json — Cached library metadata

playlists.json — Saved playlists

.gitignore — Ignore file for safe Git commits

🧰 Requirements

Install dependencies with:
pip install -r requirements.txt

🧑‍💻 Usage

Run the app using:
python main.py

Your local music folder (C:\Users\<YourName>\Music) will automatically populate in the Library tab.

☁️ Sync Notes

Playlists are mirrored to OneDrive:
C:\Users<YourName>\OneDrive\MusicPlayerData

Songs are mirrored between:

Local: C:\Users<YourName>\Music

Cloud: C:\Users<YourName>\OneDrive\Music

🖼 Screenshots

Player Tab | Playlist Manager | Library | Sync Tab

(Add your screenshots here later.)

To add screenshots:

Create a folder named assets/ in your project root.

Place your screenshots there.

Update the README to point to your images.

🏗 Development Workflow

Work on new features in the dev branch

Test locally until stable

Merge into main

Push both branches to GitHub

⚙️ Author

Kyle Josephson
🎧 Software Engineer & Developer
github.com/kylejosephson

🛡 License

This project is for personal and educational use.
Not intended for redistribution or commercial resale without permission.