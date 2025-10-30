import os
import json
import shutil
import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QInputDialog,
    QLabel, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt


class PlaylistTab(QWidget):
    def __init__(self, player_tab):
        super().__init__()
        self.player_tab = player_tab

        self.playlists_file = os.path.join(os.getcwd(), "playlists.json")
        self.backup_folder = os.path.join(os.getcwd(), "backups")
        os.makedirs(self.backup_folder, exist_ok=True)

        self.playlists = {}

        # ---- UI Layout -------------------------------------------------
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)

        # (center) Status / Header label
        self.info_label = QLabel("Playlist Manager Ready")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                border-bottom: 1px solid #333;
            }
        """)
        root.addWidget(self.info_label)

        # Spacer line
        spacer = QLabel("")
        spacer.setFixedHeight(8)
        root.addWidget(spacer)

        # Main two-column area
        columns = QHBoxLayout()
        columns.setAlignment(Qt.AlignTop)
        root.addLayout(columns)

        # LEFT: Saved Playlists + Delete button
        left_col = QVBoxLayout()
        left_col.setAlignment(Qt.AlignTop)
        columns.addLayout(left_col, stretch=1)

        self.saved_list = QListWidget()
        self.saved_list.itemDoubleClicked.connect(self.load_playlist_to_player_queue)
        left_col.addWidget(self.saved_list)

        self.delete_button = QPushButton("Delete Playlist")
        self.delete_button.clicked.connect(self.delete_playlist_with_confirm)
        left_col.addWidget(self.delete_button)

        # RIGHT: Name field (top-right), Queue list, Save button
        right_col = QVBoxLayout()
        right_col.setAlignment(Qt.AlignTop)
        columns.addLayout(right_col, stretch=1)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter playlist name...")
        right_col.addWidget(self.name_input)

        self.playlist_queue_list = QListWidget()
        right_col.addWidget(self.playlist_queue_list)

        self.save_button = QPushButton("Save Playlist")
        self.save_button.clicked.connect(self.save_playlist_from_queue)
        right_col.addWidget(self.save_button)

        # Internal builder queue
        self.playlist_queue = []

        # Load existing playlists file into left list
        self.load_playlists()

    # ------------------------------------------------------------------
    # Public callback for LibraryTab to add to the playlist-builder queue
    # ------------------------------------------------------------------
    def add_to_playlist_queue(self, path: str):
        if path and path not in self.playlist_queue:
            self.playlist_queue.append(path)
            self.playlist_queue_list.addItem(os.path.basename(path))
            print(f"🧱 [Playlist Builder] Added: {os.path.basename(path)}")

    # ------------------------------------------------------------------
    # Save / Load / Backup
    # ------------------------------------------------------------------
    def load_playlists(self):
        if os.path.exists(self.playlists_file):
            try:
                with open(self.playlists_file, "r", encoding="utf-8") as f:
                    self.playlists = json.load(f)
                print(f"✅ Loaded playlists from {self.playlists_file}")
            except Exception as e:
                print(f"⚠️ Error loading playlists: {e}")
        else:
            print("ℹ️ No playlists file found; starting fresh.")
            self.playlists = {}

        self.refresh_saved_list()

    def save_playlists(self):
        """Safely save playlists to file and automatically back them up."""
        try:
            with open(self.playlists_file, "w", encoding="utf-8") as f:
                json.dump(self.playlists, f, indent=4)
            print(f"💾 Playlists saved to {self.playlists_file}")
            self.backup_playlists()
        except Exception as e:
            print(f"⚠️ Error saving playlists: {e}")

    def backup_playlists(self):
        """Create a timestamped backup and keep only latest 50."""
        try:
            if os.path.exists(self.playlists_file) and os.path.getsize(self.playlists_file) > 0:
                ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_name = f"playlists_backup_{ts}.json"
                backup_path = os.path.join(self.backup_folder, backup_name)
                shutil.copy2(self.playlists_file, backup_path)
                print(f"🕒 Backup created: {backup_path}")

                backups = sorted(
                    [f for f in os.listdir(self.backup_folder) if f.startswith("playlists_backup_")],
                    key=lambda f: os.path.getmtime(os.path.join(self.backup_folder, f)),
                    reverse=True
                )
                if len(backups) > 50:
                    for old in backups[50:]:
                        try:
                            os.remove(os.path.join(self.backup_folder, old))
                            print(f"🧹 Removed old backup: {old}")
                        except Exception as e:
                            print(f"⚠️ Error removing old backup {old}: {e}")
        except Exception as e:
            print(f"⚠️ Error creating backup: {e}")

    def refresh_saved_list(self):
        self.saved_list.clear()
        for name in sorted(self.playlists.keys()):
            self.saved_list.addItem(name)

    # ------------------------------------------------------------------
    # Save playlist from the builder queue
    # ------------------------------------------------------------------
    def save_playlist_from_queue(self):
        name = self.name_input.text().strip()
        if not name:
            self._info("⚠️ Enter a playlist name before saving.")
            return
        if not self.playlist_queue:
            self._info("⚠️ Playlist queue is empty.")
            return

        self.playlists[name] = list(self.playlist_queue)
        self.save_playlists()
        self.refresh_saved_list()

        self._info(f"✅ Playlist '{name}' saved.")
        self.clear_playlist_queue()
        self.name_input.clear()

    def clear_playlist_queue(self):
        self.playlist_queue.clear()
        self.playlist_queue_list.clear()

    # ------------------------------------------------------------------
    # Delete saved playlist (with confirmation)
    # ------------------------------------------------------------------
    def delete_playlist_with_confirm(self):
        item = self.saved_list.currentItem()
        if not item:
            self._info("⚠️ No playlist selected.")
            return
        name = item.text()
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete playlist \"{name}\"?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if name in self.playlists:
                del self.playlists[name]
                self.save_playlists()
                self.refresh_saved_list()
                self._info(f"🗑️ Playlist '{name}' deleted.")

    # ------------------------------------------------------------------
    # Optional: double-click a saved playlist to load into PLAYER queue
    # ------------------------------------------------------------------
    def load_playlist_to_player_queue(self, item):
        name = item.text()
        songs = self.playlists.get(name, [])
        if songs:
            # Replace the player's queue with this saved playlist
            self.player_tab.queue = list(songs)
            self.player_tab.queue_list.clear()
            for song in songs:
                self.player_tab.queue_list.addItem(os.path.basename(song))
            self.player_tab.current_index = -1
            self.player_tab.is_paused = False
            print(f"🎵 Playlist '{name}' loaded into PLAYER queue.")
            self._info(f"🎵 Playlist '{name}' loaded into Player queue.")
        else:
            self._info(f"⚠️ Playlist '{name}' is empty.")

    # ------------------------------------------------------------------
    # Info message helper
    # ------------------------------------------------------------------
    def _info(self, message: str):
        self.info_label.setText(message)
