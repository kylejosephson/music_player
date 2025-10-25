# player_tab.py
import os
import pygame
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget,
    QHBoxLayout, QFileDialog, QLabel, QProgressBar
)
from PyQt5.QtCore import QTimer, Qt, QEvent, QTime
from playback_engine import PlaybackEngine


class PlayerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = PlaybackEngine()
        self.songs = []
        self.current_index = -1
        self.total_length = 0
        self.seek_offset = 0
        self.last_pos = 0.0
        self.last_update_time = QTime.currentTime()

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Title
        self.title_label = QLabel("No song playing")
        layout.addWidget(self.title_label)

        # Add Songs
        self.add_button = QPushButton("Add Songs")
        self.add_button.clicked.connect(self.add_songs)
        layout.addWidget(self.add_button)

        # Playlist
        self.playlist = QListWidget()
        self.playlist.itemDoubleClicked.connect(self.play_selected)
        layout.addWidget(self.playlist)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #202020;
                border: 1px solid #404040;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #00ff99;
                border-radius: 5px;
            }
        """)
        self.progress_bar.installEventFilter(self)
        layout.addWidget(self.progress_bar)

        # Time label
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.time_label)

        # Controls
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

        # Timer (runs fast for smooth progress)
        self.timer = QTimer()
        self.timer.setInterval(50)  # 20 FPS
        self.timer.timeout.connect(self.update_progress)
        self.timer.start()

    # --- Core Functions ---
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
            self.seek_offset = 0
            self.last_pos = 0.0
            self.last_update_time = QTime.currentTime()

            try:
                self.total_length = pygame.mixer.Sound(filepath).get_length()
            except Exception:
                self.total_length = 0

            self.progress_bar.setValue(0)
            self.time_label.setText(f"0:00 / {self.format_time(self.total_length)}")

    def play_pause(self):
        if self.engine.is_actively_playing():
            self.engine.pause()
        else:
            if self.current_index == -1 and self.songs:
                self.play_song(0)
            else:
                self.engine.play()
                # resume smoothly
                self.last_update_time = QTime.currentTime()
                self.last_pos = self.engine.get_pos() + self.seek_offset

    def play_next(self):
        if self.songs:
            next_index = (self.current_index + 1) % len(self.songs)
            self.play_song(next_index)

    def play_previous(self):
        if self.songs:
            prev_index = (self.current_index - 1) % len(self.songs)
            self.play_song(prev_index)

    # --- Progress & Smoothness ---
    def update_progress(self):
        if self.engine.current_song and not self.engine.is_paused():
            raw_pos = self.engine.get_pos() + self.seek_offset
            elapsed_ms = self.last_update_time.msecsTo(QTime.currentTime())
            self.last_update_time = QTime.currentTime()

            # smooth position interpolation (blend real with predicted)
            predicted_pos = self.last_pos + (elapsed_ms / 1000.0)
            smoothed_pos = (0.8 * predicted_pos) + (0.2 * raw_pos)
            smoothed_pos = max(0, min(smoothed_pos, self.total_length))

            self.last_pos = smoothed_pos

            if self.total_length > 0:
                progress = int((smoothed_pos / self.total_length) * 100)
                self.progress_bar.setValue(min(progress, 100))
                self.time_label.setText(
                    f"{self.format_time(smoothed_pos)} / {self.format_time(self.total_length)}"
                )

            # end-of-song detection
            if (
                not self.engine.is_actively_playing()
                and not self.engine.is_paused()
                and self.current_index != -1
            ):
                self.play_next()

    def eventFilter(self, source, event):
        if source == self.progress_bar and event.type() == QEvent.MouseButtonPress:
            if self.total_length > 0:
                ratio = event.pos().x() / self.progress_bar.width()
                new_time = ratio * self.total_length
                pygame.mixer.music.play(start=new_time)
                self.seek_offset = new_time
                self.engine.paused = False
                self.engine.playing = True
                self.last_update_time = QTime.currentTime()
                self.last_pos = new_time
                self.progress_bar.setValue(int(ratio * 100))
                self.time_label.setText(
                    f"{self.format_time(new_time)} / {self.format_time(self.total_length)}"
                )
                return True
        return super().eventFilter(source, event)

    # --- Helpers ---
    @staticmethod
    def format_time(seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
