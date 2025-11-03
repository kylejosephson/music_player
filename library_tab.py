# library_tab.py
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt

AUDIO_EXTS = {".mp3", ".ogg", ".wav", ".flac", ".m4a"}  # keep the list; pygame mainly does mp3/ogg/wav

class LibraryTab(QWidget):
    def __init__(self, root_folder,
                 add_to_player_queue_callback,
                 add_to_playlist_queue_callback):
        super().__init__()
        self.root_folder = os.path.normpath(root_folder)
        self.add_to_player_queue = add_to_player_queue_callback
        self.add_to_playlist_queue = add_to_playlist_queue_callback

        # simple cache file near your project
        self.cache_file = os.path.join(os.getcwd(), "library_cache.json")
        self.library = []  # list of dicts: {"path": "...", "display": "..."}

        # UI
        layout = QVBoxLayout(self)
        self.header = QLabel("Library loaded")
        self.header.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.header)

        self.update_btn = QPushButton("Update Library")
        self.update_btn.clicked.connect(self.rescan_library)
        layout.addWidget(self.update_btn)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list)

        # load cache if present, else scan
        if self.load_cache():
            self.header.setText(f"Library loaded (cached)")
            self.populate_list()
        else:
            self.rescan_library()

    # ---------- scanning & caching ----------
    def rescan_library(self):
        files = []
        for dirpath, _, filenames in os.walk(self.root_folder):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in AUDIO_EXTS:
                    full = os.path.normpath(os.path.join(dirpath, fname))
                    # Build a readable label, but DO NOT derive the path from it
                    parent = os.path.basename(os.path.dirname(full))
                    display = f"{parent} - {fname}" if parent else fname
                    files.append({"path": full, "display": display})

        # Sort by display for nicer list
        files.sort(key=lambda x: x["display"].lower())
        self.library = files
        self.save_cache()
        self.populate_list()
        self.header.setText("Library updated")

    def populate_list(self):
        self.list.clear()
        for entry in self.library:
            item = QListWidgetItem(entry["display"])
            # Store the real absolute path with the item
            item.setData(Qt.UserRole, entry["path"])
            self.list.addItem(item)

    def load_cache(self):
        if not os.path.exists(self.cache_file):
            return False
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Validate a few entries still exist; if too many missing, force rescan
            valid = [e for e in data if os.path.exists(e.get("path",""))]
            if not valid:
                return False
            self.library = valid
            return True
        except Exception as e:
            print(f"⚠️ library cache load error: {e}")
            return False

    def save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.library, f, indent=2)
        except Exception as e:
            print(f"⚠️ library cache save error: {e}")

    # ---------- interactions ----------
    def on_item_double_clicked(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Error", f"File not found:\n{path}")
            return

        # Add to Player queue
        self.add_to_player_queue(path)

        # Also add to Playlist builder queue
        self.add_to_playlist_queue(path)

    # Optional helper you can call from a context menu, etc.
    def add_selected_to_playlist_builder(self):
        item = self.list.currentItem()
        if not item:
            return
        path = item.data(Qt.UserRole)
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Error", f"File not found:\n{path}")
            return
        self.add_to_playlist_queue(path)
