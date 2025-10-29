import os
import json
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QMessageBox
from PyQt5.QtCore import Qt


class LibraryTab(QWidget):
    def __init__(self, library_path, add_to_queue_callback):
        super().__init__()
        self.library_path = library_path
        self.add_to_queue_callback = add_to_queue_callback
        self.cache_file = os.path.join(os.getcwd(), "library_cache.json")
        self.library = {}
        self.last_updated = None

        # --- Layout setup ---
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Status label (last update time)
        self.status_label = QLabel("Library not loaded yet.")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Update button
        self.update_button = QPushButton("Update Library")
        self.update_button.clicked.connect(self.update_library)
        layout.addWidget(self.update_button)

        # Song list
        self.song_list = QListWidget()
        self.song_list.itemDoubleClicked.connect(self.add_selected_to_queue)
        layout.addWidget(self.song_list)

        # Load cache (if exists)
        self.load_library_cache()

    # ---------------------------------------------------------------
    # Load existing JSON cache or show message if none found
    # ---------------------------------------------------------------
    def load_library_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.library = json.load(f)
                self.last_updated = datetime.fromtimestamp(os.path.getmtime(self.cache_file)).strftime("%Y-%m-%d %I:%M:%S %p")
                print(f"✅ Loaded library from cache. (last updated {self.last_updated})")
                self.populate_library()
                self.status_label.setText(f"Library loaded (cached at {self.last_updated})")
            except Exception as e:
                print(f"⚠️ Error loading library cache: {e}")
        else:
            self.status_label.setText("No library cache found. Please update library.")

    # ---------------------------------------------------------------
    # Scan the file system and rebuild library (MP3 / FLAC / WAV)
    # ---------------------------------------------------------------
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
        start_time = datetime.now()
        valid_formats = (".mp3", ".flac", ".wav")

        for root, _, files in os.walk(self.library_path):
            for file in files:
                if file.lower().endswith(valid_formats):
                    rel_path = os.path.relpath(os.path.join(root, file), self.library_path)
                    parts = rel_path.split(os.sep)
                    artist, album, song = self.parse_path(parts)
                    library_data.setdefault(artist, {}).setdefault(album, []).append(song)

        # Save new cache
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(library_data, f, indent=4)

        # Update timestamp
        self.last_updated = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        print(f"✅ Library cache rebuilt successfully at {self.last_updated}")

        # Refresh UI
        self.library = library_data
        self.populate_library()

        # Log performance
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"⏱️ Library rebuild took {elapsed:.2f} seconds.")

        self.status_label.setText(f"Library updated at {self.last_updated} ({elapsed:.2f}s)")

    # ---------------------------------------------------------------
    # Parse folder structure into Artist / Album / Song
    # ---------------------------------------------------------------
    def parse_path(self, parts):
        artist = parts[0] if len(parts) > 0 else "Unknown Artist"
        album = parts[1] if len(parts) > 2 else "Unknown Album"
        song = parts[-1]
        return artist, album, song

    # ---------------------------------------------------------------
    # Populate the UI List Widget
    # ---------------------------------------------------------------
    def populate_library(self):
        self.song_list.clear()
        for artist, albums in self.library.items():
            for album, songs in albums.items():
                for song in songs:
                    self.song_list.addItem(f"{artist} - {album} - {song}")

    # ---------------------------------------------------------------
    # Add selected song to the player queue (MP3 / FLAC / WAV only)
    # ---------------------------------------------------------------
    def add_selected_to_queue(self, item):
        text = item.text()
        parts = text.split(" - ")
        if len(parts) < 2:
            return
        artist = parts[0]
        album = parts[1] if len(parts) > 2 else "Unknown Album"
        song = " - ".join(parts[2:]) if len(parts) > 2 else parts[-1]

        valid_formats = (".mp3", ".flac", ".wav")
        if not song.lower().endswith(valid_formats):
            print(f"⚠️ Skipped non-audio file: {song}")
            return

        full_path = os.path.join(self.library_path, artist, album, song)
        if os.path.exists(full_path):
            print(f"🎶 Added to queue: {song}")
            self.add_to_queue_callback(full_path)
        else:
            QMessageBox.warning(self, "Error", f"File not found:\n{full_path}")
