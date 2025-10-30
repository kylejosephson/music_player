import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QHBoxLayout, QInputDialog, QLabel
from PyQt5.QtCore import Qt

class PlaylistTab(QWidget):
    def __init__(self, player_tab):
        super().__init__()
        self.player_tab = player_tab
        self.playlists_file = os.path.join(os.getcwd(), "playlists.json")
        self.playlists = {}

        # --- Layout setup ---
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # Playlist info label (styled like player’s info area)
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
        layout.addWidget(self.info_label)

        # Playlist list
        self.playlist_list = QListWidget()
        self.playlist_list.itemDoubleClicked.connect(self.load_playlist_to_queue)
        layout.addWidget(self.playlist_list)

        # Buttons
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create Playlist")
        self.create_button.clicked.connect(self.create_playlist)
        button_layout.addWidget(self.create_button)

        self.delete_button = QPushButton("Delete Playlist")
        self.delete_button.clicked.connect(self.delete_playlist)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.load_playlists()

    # -----------------------------------------------------------
    # Load / Save
    # -----------------------------------------------------------
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
        self.refresh_playlist_list()

    def save_playlists(self):
        try:
            with open(self.playlists_file, "w", encoding="utf-8") as f:
                json.dump(self.playlists, f, indent=4)
            print(f"💾 Playlists saved to {self.playlists_file}")
        except Exception as e:
            print(f"⚠️ Error saving playlists: {e}")

    def refresh_playlist_list(self):
        self.playlist_list.clear()
        for name in sorted(self.playlists.keys()):
            self.playlist_list.addItem(name)

    # -----------------------------------------------------------
    # Playlist Management
    # -----------------------------------------------------------
    def create_playlist(self):
        name, ok = QInputDialog.getText(self, "Create Playlist", "Enter playlist name:")
        if ok and name:
            if name not in self.playlists:
                self.playlists[name] = []
                self.save_playlists()
                self.refresh_playlist_list()
                print(f"💾 Playlists saved successfully.")
                self._info(f"✅ Playlist '{name}' created")
            else:
                self._info(f"⚠️ Playlist '{name}' already exists")

    def delete_playlist(self):
        selected = self.playlist_list.currentItem()
        if not selected:
            self._info("⚠️ No playlist selected")
            return
        name = selected.text()
        if name in self.playlists:
            del self.playlists[name]
            self.save_playlists()
            self.refresh_playlist_list()
            self._info(f"🗑️ Playlist '{name}' deleted")

    def add_to_playlist(self, name, song_path):
        if name not in self.playlists:
            self.playlists[name] = []
        if song_path not in self.playlists[name]:
            self.playlists[name].append(song_path)
            self.save_playlists()
            print(f"🎶 Added '{song_path}' to playlist '{name}'")

    def load_playlist_to_queue(self, item):
        name = item.text()
        songs = self.playlists.get(name, [])
        if songs:
            self.player_tab.queue = list(songs)
            self.player_tab.queue_list.clear()
            for song in songs:
                self.player_tab.queue_list.addItem(os.path.basename(song))
            self.player_tab.current_index = -1  # prevent auto-play
            self.player_tab.is_paused = False
            print(f"🎵 Playlist '{name}' loaded into queue.")
            self._info(f"🎵 Playlist '{name}' loaded into queue")
        else:
            self._info(f"⚠️ Playlist '{name}' is empty")

    # -----------------------------------------------------------
    # Info message helper (persistent)
    # -----------------------------------------------------------
    def _info(self, message: str):
        """Display message persistently at top of playlist tab."""
        self.info_label.setText(message)
