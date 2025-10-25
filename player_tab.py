# player_tab.py
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QHBoxLayout, QFileDialog, QLabel
from PyQt5.QtCore import QTimer
from playback_engine import PlaybackEngine

class PlayerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = PlaybackEngine()
        self.songs = []
        self.current_index = -1

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.title_label = QLabel("No song playing")
        layout.addWidget(self.title_label)

        self.add_button = QPushButton("Add Songs")
        self.add_button.clicked.connect(self.add_songs)
        layout.addWidget(self.add_button)

        self.playlist = QListWidget()
        self.playlist.itemDoubleClicked.connect(self.play_selected)
        layout.addWidget(self.playlist)

        controls = QHBoxLayout()
        self.play_pause_button = QPushButton("Play/Pause")
        self.play_pause_button.clicked.connect(self.play_pause)
        controls.addWidget(self.play_pause_button)

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.play_previous)
        controls.addWidget(self.prev_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.play_next)
        controls.addWidget(self.next_button)

        layout.addLayout(controls)

        # Timer to auto-play next song
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.check_song_end)
        self.timer.start()

    def add_songs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select MP3 files", "", "Music Files (*.mp3)")
        for file in files:
            if file not in self.songs:
                self.songs.append(file)
                self.playlist.addItem(os.path.basename(file))

    def play_selected(self, item):
        index = self.playlist.row(item)
        self.play_song(index)

    def play_song(self, index):
        if 0 <= index < len(self.songs):
            self.current_index = index
            filepath = self.songs[index]
            self.engine.load(filepath)
            self.engine.play()
            self.title_label.setText(f"Now Playing: {os.path.basename(filepath)}")
            self.playlist.setCurrentRow(index)

    def play_pause(self):
        if self.engine.is_actively_playing():
            self.engine.pause()
        else:
            if self.current_index == -1 and self.songs:
                self.play_song(0)
            else:
                self.engine.play()

    def play_next(self):
        if self.songs:
            next_index = (self.current_index + 1) % len(self.songs)
            self.play_song(next_index)

    def play_previous(self):
        if self.songs:
            prev_index = (self.current_index - 1) % len(self.songs)
            self.play_song(prev_index)

    def check_song_end(self):
        # Only go to next song if the current one finished naturally
        if not self.engine.is_actively_playing() and not self.engine.is_paused() and self.current_index != -1:
            self.play_next()