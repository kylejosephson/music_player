import os
import shutil
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
    QHBoxLayout, QProgressBar, QApplication, QFrame
)
from PyQt5.QtCore import Qt, QTimer


class SyncTab(QWidget):
    def __init__(
        self,
        music_dir="C:\\Users\\kylej\\Music",
        onedrive_music_dir="C:\\Users\\kylej\\OneDrive\\Music",
        onedrive_data_dir="C:\\Users\\kylej\\OneDrive\\MusicPlayerData"
    ):
        super().__init__()

        self.music_dir = music_dir
        self.onedrive_music_dir = onedrive_music_dir
        self.onedrive_data_dir = onedrive_data_dir
        self.local_playlist_path = os.path.join(os.getcwd(), "playlists.json")
        self.cloud_playlist_path = os.path.join(self.onedrive_data_dir, "playlists.json")

        os.makedirs(self.onedrive_data_dir, exist_ok=True)
        self.last_playlist_timestamp = None

        # --- Main Layout ---
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Header
        self.status_label = QLabel("☁️ OneDrive Sync — Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00FF66;")
        main_layout.addWidget(self.status_label)

        # Last sync
        self.last_sync_label = QLabel("Last synced: never")
        self.last_sync_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.last_sync_label)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.hide()
        main_layout.addWidget(self.progress)

        # --- Split Layout ---
        split_layout = QHBoxLayout()
        main_layout.addLayout(split_layout)

        # ========== LEFT (Playlists) ==========
        left_frame = QFrame()
        left_layout = QVBoxLayout()
        left_frame.setLayout(left_layout)

        self.playlist_label = QLabel("📜 Playlist Status")
        self.playlist_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.playlist_label)

        self.playlist_list = QListWidget()
        left_layout.addWidget(self.playlist_list)

        # Playlist button row (side-by-side)
        playlist_button_row = QHBoxLayout()
        self.playlist_sync_btn = QPushButton("☁️ Sync Playlists")
        self.playlist_sync_btn.clicked.connect(self.sync_playlists)

        self.force_refresh_btn = QPushButton("🔄 Force Refresh Playlists")
        self.force_refresh_btn.clicked.connect(self.force_refresh_playlists)

        playlist_button_row.addWidget(self.playlist_sync_btn)
        playlist_button_row.addWidget(self.force_refresh_btn)
        left_layout.addLayout(playlist_button_row)

        # ========== RIGHT (Songs) ==========
        right_frame = QFrame()
        right_layout = QVBoxLayout()
        right_frame.setLayout(right_layout)

        self.song_label = QLabel("🎵 Song Status")
        self.song_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.song_label)

        self.song_list = QListWidget()
        right_layout.addWidget(self.song_list)

        # Centered sync songs button
        song_button_row = QHBoxLayout()
        song_button_row.addStretch()
        self.song_sync_btn = QPushButton("☁️ Sync Songs")
        self.song_sync_btn.clicked.connect(self.sync_songs)
        song_button_row.addWidget(self.song_sync_btn)
        song_button_row.addStretch()
        right_layout.addLayout(song_button_row)

        # --- Add frames to split layout ---
        split_layout.addWidget(left_frame)
        split_layout.addWidget(right_frame)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_playlist_changes)
        self.timer.start(3000)

        self.refresh_status()

    # --------------------------------------------------
    def check_playlist_changes(self):
        """Detect changes to playlists.json and refresh instantly."""
        if os.path.exists(self.local_playlist_path):
            modified = os.path.getmtime(self.local_playlist_path)
            if self.last_playlist_timestamp is None or modified != self.last_playlist_timestamp:
                self.last_playlist_timestamp = modified
                self.refresh_status()

    # --------------------------------------------------
    def refresh_status(self):
        """Rescan playlists and songs, showing detailed differences."""
        import json
        self.status_label.setText("🔍 Scanning...")
        QApplication.processEvents()

        if os.path.exists(self.local_playlist_path):
            self.last_playlist_timestamp = os.path.getmtime(self.local_playlist_path)
        else:
            self.last_playlist_timestamp = None

        self.playlist_list.clear()
        self.song_list.clear()

        local_exists = os.path.exists(self.local_playlist_path)
        cloud_exists = os.path.exists(self.cloud_playlist_path)

        # --- PLAYLIST COMPARISON ---
        if not local_exists and not cloud_exists:
            self.playlist_list.addItem("⚠️ No playlists found")
        elif local_exists and not cloud_exists:
            self.playlist_list.addItem("⬆ Upload → playlists.json (no cloud copy yet)")
        elif cloud_exists and not local_exists:
            self.playlist_list.addItem("⬇ Download → playlists.json (missing local copy)")
        else:
            try:
                with open(self.local_playlist_path, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                with open(self.cloud_playlist_path, "r", encoding="utf-8") as f:
                    cloud_data = json.load(f)

                if isinstance(local_data, dict) and "playlists" in local_data:
                    local_data = local_data["playlists"]
                if isinstance(cloud_data, dict) and "playlists" in cloud_data:
                    cloud_data = cloud_data["playlists"]

                if not isinstance(local_data, dict) or not isinstance(cloud_data, dict):
                    self.playlist_list.addItem("⚠️ Invalid playlist format detected.")
                    return

                local_names = set(local_data.keys())
                cloud_names = set(cloud_data.keys())

                missing_in_cloud = local_names - cloud_names
                missing_in_local = cloud_names - local_names

                changed_playlists = [
                    name for name in (local_names & cloud_names)
                    if local_data[name] != cloud_data[name]
                ]

                total_playlists = len(local_names.union(cloud_names))
                out_of_sync_count = len(missing_in_cloud) + len(missing_in_local) + len(changed_playlists)

                if out_of_sync_count == 0:
                    self.playlist_list.addItem("✅ Playlists synced (timestamps & contents match)")
                    self.playlist_list.addItem(f"All {total_playlists} playlists already synced.")
                else:
                    if missing_in_cloud:
                        for name in sorted(missing_in_cloud):
                            self.playlist_list.addItem(f"⬆ Upload → New playlist: {name}")
                    if missing_in_local:
                        for name in sorted(missing_in_local):
                            self.playlist_list.addItem(f"⬇ Download → Missing locally: {name}")
                    if changed_playlists:
                        for name in sorted(changed_playlists):
                            self.playlist_list.addItem(f"⚠️ Modified → {name}")

                    self.playlist_list.addItem(f"Total out of sync: {out_of_sync_count} of {total_playlists}")

            except Exception as e:
                self.playlist_list.addItem(f"⚠️ Error reading playlists: {e}")

        # --- SONG COMPARISON ---
        local_songs = self._get_songs(self.music_dir)
        cloud_songs = self._get_songs(self.onedrive_music_dir)

        to_upload = [s for s in local_songs if s not in cloud_songs]
        to_download = [s for s in cloud_songs if s not in local_songs]

        for s in to_upload:
            self.song_list.addItem(f"⬆ Upload → {os.path.basename(s)}")
        for s in to_download:
            self.song_list.addItem(f"⬇ Download → {os.path.basename(s)}")

        if not to_upload and not to_download:
            self.song_list.addItem("✅ All songs synced")

        self.status_label.setText("☁️ OneDrive Sync — Ready")

    # --------------------------------------------------
    def _get_songs(self, path):
        songs = []
        if not os.path.exists(path):
            return songs
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith(".mp3"):
                    songs.append(os.path.relpath(os.path.join(root, f), path))
        return songs

    # --------------------------------------------------
    def sync_playlists(self):
        threading.Thread(target=self._sync_playlists_thread, daemon=True).start()

    def _sync_playlists_thread(self):
        self._show_progress("Uploading playlists.json...")
        local_file = self.local_playlist_path
        cloud_file = self.cloud_playlist_path

        if os.path.exists(local_file):
            os.makedirs(os.path.dirname(cloud_file), exist_ok=True)
            shutil.copy2(local_file, cloud_file)
            self.status_label.setText("✅ Uploaded playlist to OneDrive.")
            self.last_sync_label.setText(
                f"Last synced: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}"
            )
        else:
            self.status_label.setText("⚠️ No local playlists.json found.")

        self._hide_progress()
        self.refresh_status()

    # --------------------------------------------------
    def sync_songs(self):
        threading.Thread(target=self._sync_songs_thread, daemon=True).start()

    def _sync_songs_thread(self):
        self._show_progress("Syncing songs...")
        local_songs = self._get_songs(self.music_dir)
        cloud_songs = self._get_songs(self.onedrive_music_dir)

        to_upload = [s for s in local_songs if s not in cloud_songs]
        to_download = [s for s in cloud_songs if s not in local_songs]

        total = len(to_upload) + len(to_download)
        done = 0

        for rel_path in to_upload:
            src = os.path.join(self.music_dir, rel_path)
            dest = os.path.join(self.onedrive_music_dir, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            done += 1
            self.progress.setValue(int(done / max(total, 1) * 100))

        for rel_path in to_download:
            src = os.path.join(self.onedrive_music_dir, rel_path)
            dest = os.path.join(self.music_dir, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            done += 1
            self.progress.setValue(int(done / max(total, 1) * 100))

        self.status_label.setText("✅ Sync complete.")
        self.last_sync_label.setText(
            f"Last synced: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}"
        )
        self._hide_progress()
        self.refresh_status()

    # --------------------------------------------------
    def force_refresh_playlists(self):
        """Manual refresh limited to playlist area."""
        self.status_label.setText("🔁 Refreshing playlists...")
        QApplication.processEvents()
        self.refresh_status()
        self.status_label.setText("✅ Playlist status refreshed")
        QTimer.singleShot(2000, lambda: self.status_label.setText("☁️ OneDrive Sync — Ready"))

    # --------------------------------------------------
    def _show_progress(self, message):
        self.status_label.setText(message)
        self.progress.setValue(0)
        self.progress.show()

    def _hide_progress(self):
        self.progress.hide()
        self.progress.setValue(0)
