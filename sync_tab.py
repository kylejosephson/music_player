import os
import shutil
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
    QHBoxLayout, QProgressBar, QApplication, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from config import ROAMING_DIR, LOCAL_DIR, ONEDRIVE_DATA_DIR

from safe_print import safe_print


class SyncTab(QWidget):
    def __init__(
        self,
        music_dir="C:\\Users\\kylej\\Music",
        onedrive_music_dir="C:\\Users\\kylej\\OneDrive\\Music",
        onedrive_data_dir=ONEDRIVE_DATA_DIR
    ):
        super().__init__()

        # --- Core folders ---
        self.music_dir = music_dir
        self.onedrive_music_dir = onedrive_music_dir
        self.onedrive_data_dir = onedrive_data_dir
        os.makedirs(self.onedrive_data_dir, exist_ok=True)

        # --- Local data paths ---
        self.local_playlist_path = os.path.join(ROAMING_DIR, "playlists.json")
        self.local_library_path = os.path.join(ROAMING_DIR, "library_cache.json")
        self.local_metadata_path = os.path.join(ROAMING_DIR, "music_metadata.json")
        self.local_artwork_dir = os.path.join(LOCAL_DIR, "cache", "artwork")

        os.makedirs(self.local_artwork_dir, exist_ok=True)

        self.last_playlist_timestamp = None

        # --- UI Layout ---
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.status_label = QLabel("☁️ OneDrive Sync — Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00FF66;")
        main_layout.addWidget(self.status_label)

        self.last_sync_label = QLabel("Last synced: never")
        self.last_sync_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.last_sync_label)

        self.progress = QProgressBar()
        self.progress.hide()
        main_layout.addWidget(self.progress)

        # --- Split layout ---
        split_layout = QHBoxLayout()
        main_layout.addLayout(split_layout)

        # ========== LEFT: Playlists ==========
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)

        self.playlist_label = QLabel("📜 Playlist Status")
        self.playlist_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.playlist_label)

        self.playlist_list = QListWidget()
        left_layout.addWidget(self.playlist_list)

        playlist_button_row = QHBoxLayout()
        self.playlist_sync_btn = QPushButton("☁️ Backup Playlists")
        self.playlist_sync_btn.clicked.connect(self.sync_playlists)

        self.force_refresh_btn = QPushButton("🔄 Force Refresh")
        self.force_refresh_btn.clicked.connect(self.force_refresh_playlists)

        self.backup_now_btn = QPushButton("🧠 Backup Now")
        self.backup_now_btn.clicked.connect(self.manual_backup_now)

        playlist_button_row.addWidget(self.playlist_sync_btn)
        playlist_button_row.addWidget(self.force_refresh_btn)
        playlist_button_row.addWidget(self.backup_now_btn)
        left_layout.addLayout(playlist_button_row)

        # ========== RIGHT: Songs ==========
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)

        self.song_label = QLabel("🎵 Song Status")
        self.song_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.song_label)

        self.song_list = QListWidget()
        right_layout.addWidget(self.song_list)

        song_button_row = QHBoxLayout()
        song_button_row.addStretch()
        self.song_sync_btn = QPushButton("☁️ Sync Songs")
        self.song_sync_btn.clicked.connect(self.sync_songs)
        song_button_row.addWidget(self.song_sync_btn)
        song_button_row.addStretch()
        right_layout.addLayout(song_button_row)

        split_layout.addWidget(left_frame)
        split_layout.addWidget(right_frame)

        # --- Timer ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_playlist_changes)
        self.timer.start(3000)

        self.refresh_status()

    # --------------------------------------------------
    def check_playlist_changes(self):
        if os.path.exists(self.local_playlist_path):
            modified = os.path.getmtime(self.local_playlist_path)
            if self.last_playlist_timestamp is None or modified != self.last_playlist_timestamp:
                self.last_playlist_timestamp = modified
                self.refresh_status()

    # --------------------------------------------------
    def refresh_status(self):
        import json
        self.status_label.setText("🔍 Scanning...")
        QApplication.processEvents()

        self.playlist_list.clear()
        self.song_list.clear()

        local_exists = os.path.exists(self.local_playlist_path)
        latest_backup = self._find_latest_backup(prefix="playlists_backup_")

        # PLAYLIST STATUS
        if not local_exists and not latest_backup:
            self.playlist_list.addItem("⚠️ No local playlist or backups found.")
        elif local_exists and not latest_backup:
            self.playlist_list.addItem("⬆ Backup needed → No playlist backups yet.")
        elif latest_backup and not local_exists:
            self.playlist_list.addItem(f"⬇ Restore → Missing local playlists.json (latest backup: {latest_backup})")
        else:
            try:
                local_path = self.local_playlist_path
                backup_path = os.path.join(self.onedrive_data_dir, latest_backup)

                with open(local_path, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                with open(backup_path, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)

                # Normalize structure
                if isinstance(local_data, dict) and "playlists" in local_data:
                    local_data = local_data["playlists"]
                if isinstance(backup_data, dict) and "playlists" in backup_data:
                    backup_data = backup_data["playlists"]

                local_names = set(local_data.keys())
                backup_names = set(backup_data.keys())

                missing_in_backup = local_names - backup_names
                missing_in_local = backup_names - local_names
                changed_playlists = [
                    name for name in (local_names & backup_names)
                    if local_data[name] != backup_data[name]
                ]

                total_playlists = len(local_names.union(backup_names))
                out_of_sync = len(missing_in_backup) + len(missing_in_local) + len(changed_playlists)

                if out_of_sync == 0:
                    self.playlist_list.addItem(f"✅ All {total_playlists} playlists match latest backup.")
                else:
                    if missing_in_backup:
                        for name in sorted(missing_in_backup):
                            self.playlist_list.addItem(f"⬆ Needs backup → New playlist: {name}")
                    if missing_in_local:
                        for name in sorted(missing_in_local):
                            self.playlist_list.addItem(f"⬇ Missing locally → {name}")
                    if changed_playlists:
                        for name in sorted(changed_playlists):
                            self.playlist_list.addItem(f"⚠️ Modified → {name}")

                    self.playlist_list.addItem(f"Total out of sync: {out_of_sync} of {total_playlists}")

            except Exception as e:
                self.playlist_list.addItem(f"⚠️ Error comparing playlists: {e}")

        # SONG STATUS
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
    def _find_latest_backup(self, prefix):
        backups = [
            f for f in os.listdir(self.onedrive_data_dir)
            if f.startswith(prefix) and f.endswith(".json")
        ]
        if not backups:
            return None
        return max(backups, key=lambda f: os.path.getmtime(os.path.join(self.onedrive_data_dir, f)))

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
        threading.Thread(target=self._backup_playlists_thread, daemon=True).start()

    def _backup_playlists_thread(self):
        self._show_progress("Backing up playlists...")
        if os.path.exists(self.local_playlist_path):
            timestamp = datetime.now().strftime("%Y-%m-%d_%I-%M-%p")
            dest_file = os.path.join(self.onedrive_data_dir, f"playlists_backup_{timestamp}.json")
            shutil.copy2(self.local_playlist_path, dest_file)
            self.status_label.setText(f"✅ Playlist backed up as {os.path.basename(dest_file)}")
            self.backup_all_data()
        else:
            self.status_label.setText("⚠️ No local playlists.json found.")
        self._hide_progress()
        self.refresh_status()

    # --------------------------------------------------
    def backup_all_data(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%I-%M-%p")
        backup_dir = self.onedrive_data_dir
        os.makedirs(backup_dir, exist_ok=True)

        files_to_backup = {
            self.local_library_path: f"library_backup_{timestamp}.json",
            self.local_metadata_path: f"metadata_backup_{timestamp}.json",
        }

        backed_up = []
        for src, dst in files_to_backup.items():
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(backup_dir, dst))
                backed_up.append(os.path.basename(dst))

        if os.path.exists(self.local_artwork_dir):
            art_dest = os.path.join(backup_dir, f"artwork_backup_{timestamp}")
            shutil.copytree(self.local_artwork_dir, art_dest, dirs_exist_ok=True)
            backed_up.append("artwork folder")

        if backed_up:
            self.status_label.setText(f"💾 Backup complete: {', '.join(backed_up)}")
        else:
            self.status_label.setText("⚠️ No data files found to backup.")

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

        self.status_label.setText("✅ Song sync complete.")
        self.backup_all_data()
        self.last_sync_label.setText(f"Last synced: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
        self._hide_progress()
        self.refresh_status()

    # --------------------------------------------------
    def force_refresh_playlists(self):
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

    def manual_backup_now(self):
        self.status_label.setText("💾 Backing up data now...")
        QApplication.processEvents()
        self.backup_all_data()
        QTimer.singleShot(2500, lambda: self.status_label.setText("☁️ OneDrive Sync — Ready"))
