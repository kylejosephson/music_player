import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTreeWidget, 
    QTreeWidgetItem, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt

class LibraryTab(QWidget):
    def __init__(self, library_path, add_to_queue_callback):
        super().__init__()
        self.library_path = library_path
        self.cache_file = os.path.join(os.getcwd(), "library_cache.json")
        self.add_to_queue_callback = add_to_queue_callback

        # Layout setup
        layout = QVBoxLayout(self)
        self.update_button = QPushButton("🔄 Update Library")
        self.update_button.clicked.connect(self.update_library)
        layout.addWidget(self.update_button)

        # Status label for feedback (timestamp or message)
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Tree display for library
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Library"])
        self.tree.itemDoubleClicked.connect(self.handle_double_click)
        layout.addWidget(self.tree)

        # Try to load cached library or create one
        self.load_library_cache()

    # ---------------------------------------------------------
    # Scans the music directory and rebuilds the tree
    # ---------------------------------------------------------
    def update_library(self):
        if not os.path.exists(self.library_path):
            QMessageBox.warning(self, "Error", f"Path not found:\n{self.library_path}")
            return

        # Delete old cache first to ensure a full rebuild
        if os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
                print("🗑️ Old cache file removed. Rebuilding...")
            except Exception as e:
                print(f"⚠️ Could not remove old cache: {e}")

        library_data = {}
        for root, _, files in os.walk(self.library_path):
            for file in files:
                if file.lower().endswith(".mp3"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.library_path)
                    parts = rel_path.split(os.sep)
                    artist, album, song = self.parse_path(parts)
                    library_data.setdefault(artist, {}).setdefault(album, []).append(song)

        # Save and display new library data
        self.save_library_cache(library_data)
        self.display_library(library_data)

        # Update timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        self.status_label.setText(f"✅ Library updated: {timestamp}")
        print(f"✅ Library cache rebuilt successfully at {timestamp}")

        # Popup confirmation
        QMessageBox.information(self, "Library Updated", f"Library successfully updated!\n({timestamp})")

    # ---------------------------------------------------------
    # Builds artist→album→song hierarchy (supports missing albums)
    # ---------------------------------------------------------
    def parse_path(self, parts):
        artist = parts[0] if len(parts) > 0 else "Unknown Artist"
        if len(parts) == 2:  # artist/song.mp3
            album = "Unknown Album"
            song = parts[1]
        elif len(parts) > 2:  # artist/album/song.mp3
            album = parts[1]
            song = parts[-1]
        else:
            album = "Unknown Album"
            song = os.path.basename(parts[-1])
        return artist, album, song

    # ---------------------------------------------------------
    # Displays the library in the QTreeWidget
    # ---------------------------------------------------------
    def display_library(self, library_data):
        self.tree.clear()
        for artist, albums in sorted(library_data.items()):
            artist_item = QTreeWidgetItem([artist])
            for album, songs in sorted(albums.items()):
                album_item = QTreeWidgetItem([album])
                for song in sorted(songs):
                    # build path that works even if album is missing
                    song_path = os.path.join(
                        self.library_path,
                        artist,
                        album if album != "Unknown Album" else "",
                        song
                    )
                    song_item = QTreeWidgetItem([song])
                    song_item.setData(0, Qt.UserRole, song_path)
                    album_item.addChild(song_item)
                artist_item.addChild(album_item)
            self.tree.addTopLevelItem(artist_item)
        self.tree.expandAll()

    # ---------------------------------------------------------
    # Double-click to add a song to the queue
    # ---------------------------------------------------------
    def handle_double_click(self, item, column):
        path = item.data(0, Qt.UserRole)
        if path and os.path.isfile(path):
            self.add_to_queue_callback(path)
        else:
            print(f"⚠️ Could not add: file not found -> {path}")

    # ---------------------------------------------------------
    # Load or save cached library
    # ---------------------------------------------------------
    def save_library_cache(self, data):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_library_cache(self):
        if os.path.exists(self.cache_file):
            modified_time = datetime.fromtimestamp(os.path.getmtime(self.cache_file))
            formatted_time = modified_time.strftime("%Y-%m-%d %I:%M:%S %p")
            print(f"✅ Loaded library from cache. (last updated {formatted_time})")
            self.status_label.setText(f"📁 Loaded from cache: {formatted_time}")
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.display_library(data)
        else:
            print("⚙️ Cache not found. Scanning music folder...")
            self.update_library()
