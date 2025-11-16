import os
import json
import shutil
import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel,
    QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from config import ROAMING_DIR

from safe_print import safe_print


class PlaylistTab(QWidget):
    def __init__(self, player_tab):
        super().__init__()
        self.player_tab = player_tab

        # --- Permanent paths ---
        self.playlists_file = os.path.join(ROAMING_DIR, "playlists.json")
        self.backup_folder = os.path.join(ROAMING_DIR, "backups")
        os.makedirs(self.backup_folder, exist_ok=True)

        # --- Ensure playlists.json exists ---
        if not os.path.exists(self.playlists_file):
            with open(self.playlists_file, "w", encoding="utf-8") as f:
                json.dump({}, f)
            safe_print(f"Created new playlists file at {self.playlists_file}")

        self.playlists = {}

        # ---- UI Layout -------------------------------------------------
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)

        # Header label
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

        # Main area
        columns = QHBoxLayout()
        columns.setAlignment(Qt.AlignTop)
        root.addLayout(columns)

        # LEFT: Saved Playlists + Delete
        left_col = QVBoxLayout()
        left_col.setAlignment(Qt.AlignTop)
        columns.addLayout(left_col, stretch=1)

        self.saved_list = QListWidget()
        self.saved_list.itemDoubleClicked.connect(self.load_playlist_to_player_queue)
        left_col.addWidget(self.saved_list)

        self.delete_button = QPushButton("Delete Playlist")
        self.delete_button.clicked.connect(self.delete_playlist_with_confirm)
        left_col.addWidget(self.delete_button)

        # RIGHT: Builder Area
        right_col = QVBoxLayout()
        right_col.setAlignment(Qt.AlignTop)
        columns.addLayout(right_col, stretch=1)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter playlist name...")
        right_col.addWidget(self.name_input)

        self.playlist_queue_list = QListWidget()
        right_col.addWidget(self.playlist_queue_list)

        button_row = QHBoxLayout()
        button_row.setAlignment(Qt.AlignLeft)

        self.save_button = QPushButton("💾 Save Playlist")
        self.save_button.clicked.connect(self.save_playlist_from_queue)
        button_row.addWidget(self.save_button)

        self.clear_builder_button = QPushButton("🧹 Clear Builder")
        self.clear_builder_button.clicked.connect(self.clear_builder)
        button_row.addWidget(self.clear_builder_button)

        right_col.addLayout(button_row)

        # Internal builder
        self.playlist_queue = []

        # Load existing playlists
        self.load_playlists()

    # ------------------------------------------------------------------
    def add_to_playlist_queue(self, path: str):
        if path and path not in self.playlist_queue:
            self.playlist_queue.append(path)
            self.playlist_queue_list.addItem(os.path.basename(path))
            safe_print(f"[Playlist Builder] Added: {os.path.basename(path)}")  # ✅ fixed

    # ------------------------------------------------------------------
    # Save / Load / Backup
    # ------------------------------------------------------------------
    def load_playlists(self):
        if os.path.exists(self.playlists_file):
            try:
                with open(self.playlists_file, "r", encoding="utf-8") as f:
                    self.playlists = json.load(f)
                safe_print(f"Loaded playlists from {os.path.basename(self.playlists_file)}")  # ✅
            except Exception as e:
                safe_print(f"Error loading playlists: {e}")  # ✅
                self.playlists = {}
        else:
            self.playlists = {}
            safe_print("No playlists file found; starting fresh.")  # ✅

        self.refresh_saved_list()

    def save_playlists(self):
        """Safely save playlists and back them up."""
        try:
            with open(self.playlists_file, "w", encoding="utf-8") as f:
                json.dump(self.playlists, f, indent=4)

            safe_print(f"Playlists saved to {self.playlists_file}")  # ✅
            self.backup_playlists()
        except Exception as e:
            safe_print(f"Error saving playlists: {e}")  # ✅

    def backup_playlists(self):
        """Create a timestamped backup (keep latest 50)."""
        try:
            if os.path.exists(self.playlists_file) and os.path.getsize(self.playlists_file) > 0:
                ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_name = f"playlists_backup_{ts}.json"
                backup_path = os.path.join(self.backup_folder, backup_name)
                shutil.copy2(self.playlists_file, backup_path)

                safe_print(f"Backup created: {backup_path}")  # ✅

                # Cleanup backups
                backups = sorted(
                    [f for f in os.listdir(self.backup_folder) if f.startswith("playlists_backup_")],
                    key=lambda f: os.path.getmtime(os.path.join(self.backup_folder, f)),
                    reverse=True
                )
                for old in backups[50:]:
                    try:
                        os.remove(os.path.join(self.backup_folder, old))
                        safe_print(f"Removed old backup: {old}")  # ✅
                    except Exception as e:
                        safe_print(f"Error removing old backup {old}: {e}")  # ✅
        except Exception as e:
            safe_print(f"Error creating backup: {e}")  # ✅

    def refresh_saved_list(self):
        self.saved_list.clear()
        for name in sorted(self.playlists.keys()):
            self.saved_list.addItem(name)

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
    def clear_builder(self):
        if not self.playlist_queue:
            self._info("ℹ️ Builder is already empty.")
            return
        self.clear_playlist_queue()
        self._info("🧹 Playlist builder cleared. Ready to start fresh.")

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
    def load_playlist_to_player_queue(self, item):
        name = item.text()
        songs = self.playlists.get(name, [])
        if songs:
            self.player_tab.queue = list(songs)
            self.player_tab.queue_list.clear()
            for song in songs:
                self.player_tab.queue_list.addItem(os.path.basename(song))

            self.player_tab.current_index = -1
            self.player_tab.is_paused = False

            safe_print(f"Playlist '{name}' loaded into PLAYER queue.")  # ✅
            self._info(f"🎵 Playlist '{name}' loaded into Player queue.")
        else:
            self._info(f"⚠️ Playlist '{name}' is empty.")

    # ------------------------------------------------------------------
    def _info(self, message: str):
        """Display info messages in the header."""
        self.info_label.setText(message)
