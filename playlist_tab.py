# playlist_tab.py
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget,
    QHBoxLayout, QFileDialog, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt


class PlaylistTab(QWidget):
    def __init__(self, player_tab):
        super().__init__()
        self.player_tab = player_tab
        self.playlists_dir = "playlists"
        os.makedirs(self.playlists_dir, exist_ok=True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("Playlist Manager")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(title)

        # Playlist list
        self.playlist_list = QListWidget()
        self.playlist_list.itemDoubleClicked.connect(self.load_playlist)
        layout.addWidget(self.playlist_list)

        # Buttons
        controls = QHBoxLayout()
        self.save_button = QPushButton("Save Current Queue")
        self.save_button.clicked.connect(self.save_playlist)
        controls.addWidget(self.save_button)

        self.delete_button = QPushButton("Delete Playlist")
        self.delete_button.clicked.connect(self.delete_playlist)
        controls.addWidget(self.delete_button)
        layout.addLayout(controls)

        self.refresh_button = QPushButton("Refresh Playlist List")
        self.refresh_button.clicked.connect(self.refresh_playlist_list)
        layout.addWidget(self.refresh_button)

        self.setStyleSheet("""
            QWidget { background-color: #121212; color: white; }
            QPushButton { background-color: #1db954; border: none; padding: 5px 10px; border-radius: 5px; }
            QPushButton:hover { background-color: #1ed760; }
            QListWidget { background-color: #202020; border: 1px solid #333; }
        """)

        self.refresh_playlist_list()

    def refresh_playlist_list(self):
        self.playlist_list.clear()
        for f in os.listdir(self.playlists_dir):
            if f.endswith(".json"):
                self.playlist_list.addItem(f.replace(".json", ""))

    def save_playlist(self):
        if not self.player_tab.queue:
            QMessageBox.warning(self, "Empty Queue", "There are no songs to save.")
            return

        name, _ = QFileDialog.getSaveFileName(
            self, "Save Playlist As", self.playlists_dir, "Playlist Files (*.json)"
        )
        if name:
            if not name.endswith(".json"):
                name += ".json"
            with open(name, "w") as f:
                json.dump(self.player_tab.queue, f, indent=4)
            QMessageBox.information(self, "Saved", "Playlist saved successfully!")
            self.refresh_playlist_list()

    def load_playlist(self, item):
        path = os.path.join(self.playlists_dir, f"{item.text()}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                songs = json.load(f)
            self.player_tab.queue = songs
            self.player_tab.queue_list.clear()
            for song in songs:
                self.player_tab.queue_list.addItem(os.path.basename(song))
            QMessageBox.information(self, "Loaded", f"Playlist '{item.text()}' loaded!")

    def delete_playlist(self):
        selected = self.playlist_list.currentItem()
        if not selected:
            return
        name = selected.text()
        path = os.path.join(self.playlists_dir, f"{name}.json")
        if os.path.exists(path):
            os.remove(path)
            QMessageBox.information(self, "Deleted", f"Playlist '{name}' deleted!")
            self.refresh_playlist_list()
