import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton
from PyQt5.QtCore import pyqtSignal

class LibraryTab(QWidget):
    add_to_queue_signal = pyqtSignal(str)  # emits song path to PlayerTab

    def __init__(self, music_dir="C:\\Users\\kylej\\Music"):
        super().__init__()
        self.music_dir = music_dir
        self.layout = QVBoxLayout(self)
        
        # Button to refresh the library
        self.refresh_button = QPushButton("Refresh Library")
        self.refresh_button.clicked.connect(self.load_library)
        self.layout.addWidget(self.refresh_button)
        
        # List of songs
        self.song_list = QListWidget()
        self.song_list.itemDoubleClicked.connect(self.add_selected_to_queue)
        self.layout.addWidget(self.song_list)
        
        self.songs = []  # list of (display_name, file_path)
        self.load_library()

    def load_library(self):
        """Scan music_dir for .mp3 files."""
        self.song_list.clear()
        self.songs.clear()
        for root, _, files in os.walk(self.music_dir):
            for file in files:
                if file.lower().endswith(".mp3"):
                    path = os.path.join(root, file)
                    parts = path.split(os.sep)
                    display_name = " - ".join(parts[-3:]) if len(parts) >= 3 else file
                    self.songs.append((display_name, path))
                    self.song_list.addItem(display_name)

    def add_selected_to_queue(self, item):
        """Emit selected song path to player tab."""
        index = self.song_list.row(item)
        song_path = self.songs[index][1]
        self.add_to_queue_signal.emit(song_path)
