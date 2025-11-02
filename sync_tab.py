import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox
)
from PyQt5.QtCore import Qt
import onedrive_sync  # Reuses your working OneDrive sync script


class SyncTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        # ==========================================
        # HEADER / STATUS LABEL
        # ==========================================
        self.status_label = QLabel("Sync Manager Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                border-bottom: 1px solid #333;
            }
        """)
        self.layout().addWidget(self.status_label)

        # ==========================================
        # MAIN AREA: TWO WINDOWS (PLAYLIST / SONGS)
        # ==========================================
        main_area = QHBoxLayout()
        main_area.setAlignment(Qt.AlignTop)

        # --- LEFT: PLAYLIST SYNC WINDOW ---
        self.playlist_list = QListWidget()
        main_area.addWidget(self.playlist_list, stretch=1)

        # --- RIGHT: SONG SYNC WINDOW ---
        self.song_list = QListWidget()
        main_area.addWidget(self.song_list, stretch=1)

        self.layout().addLayout(main_area)

        # ==========================================
        # BUTTON AREA (SYNC BUTTONS UNDER EACH WINDOW)
        # ==========================================
        button_area = QHBoxLayout()
        button_area.setAlignment(Qt.AlignTop)

        # Playlist sync button
        self.playlist_sync_button = QPushButton("Sync Playlists")
        self.playlist_sync_button.clicked.connect(self.sync_playlists)
        button_area.addWidget(self.playlist_sync_button)

        # Song sync button
        self.song_sync_button = QPushButton("Sync Songs")
        self.song_sync_button.clicked.connect(self.sync_songs_placeholder)
        button_area.addWidget(self.song_sync_button)

        self.layout().addLayout(button_area)

        # Initialize lists
        self.refresh_sync_info()

    # ==========================================
    # REFRESH DISPLAY DATA
    # ==========================================
    def refresh_sync_info(self):
        """Display basic local playlist and song info."""
        self.playlist_list.clear()
        self.song_list.clear()

        # --- PLAYLIST INFO ---
        playlist_file = "playlists.json"
        if os.path.exists(playlist_file):
            with open(playlist_file, "r", encoding="utf-8") as f:
                playlists = json.load(f)
            self.playlist_list.addItem(f"Local playlists: {len(playlists)}")
            for name in playlists.keys():
                self.playlist_list.addItem(f" • {name}")
        else:
            self.playlist_list.addItem("⚠️ No local playlist file found.")

        # --- SONG INFO ---
        music_dir = "C:\\Users\\kylej\\Music"
        song_count = 0
        for root, _, files in os.walk(music_dir):
            for f in files:
                if f.lower().endswith(".mp3"):
                    song_count += 1
        self.song_list.addItem(f"Local songs found: {song_count}")
        self.song_list.addItem("(Future: Compare with OneDrive music folder)")

    # ==========================================
    # SYNC FUNCTIONS
    # ==========================================
    def sync_playlists(self):
        """Call OneDrive upload and refresh view."""
        try:
            self.status_label.setText("🔄 Syncing playlists with OneDrive...")
            onedrive_sync.upload_playlist_to_onedrive()
            self.status_label.setText(f"✅ Playlists synced successfully at {datetime.now().strftime('%I:%M %p')}")
        except Exception as e:
            self.status_label.setText("❌ Playlist sync failed")
            QMessageBox.warning(self, "Error", f"Playlist sync failed:\n{e}")
        finally:
            self.refresh_sync_info()

    def sync_songs_placeholder(self):
        """Placeholder for song sync (future feature)."""
        QMessageBox.information(self, "Coming Soon", "Song syncing will be available in a future update.")
        self.status_label.setText("ℹ️ Song sync placeholder executed.")


