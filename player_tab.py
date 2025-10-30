import os
import pygame
from mutagen.mp3 import MP3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QProgressBar, QFileDialog
)
from PyQt5.QtCore import QTimer, Qt, QEvent, QTime
from PyQt5.QtGui import QFont


class PlayerTab(QWidget):
    def __init__(self):
        super().__init__()
        pygame.mixer.init()

        self.layout = QHBoxLayout(self)

        # ---------------- LEFT: PLAYER AREA ----------------
        self.player_layout = QVBoxLayout()
        self.player_layout.setAlignment(Qt.AlignTop)

        # Header / Song label
        self.song_label = QLabel("No song playing")
        self.song_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.song_label.setAlignment(Qt.AlignCenter)
        self.player_layout.addWidget(self.song_label)

        # Play / Pause button
        self.play_button = QPushButton("Play / Pause")
        self.play_button.setFixedHeight(40)
        self.play_button.clicked.connect(self.play_pause)
        self.player_layout.addWidget(self.play_button, alignment=Qt.AlignCenter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e1e1e;
                border-radius: 8px;
                border: 1px solid #333;
            }
            QProgressBar::chunk {
                background-color: #39ff14;
                border-radius: 8px;
            }
        """)
        self.player_layout.addWidget(self.progress_bar)

        # Time label
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setFont(QFont("Consolas", 10))
        self.time_label.setAlignment(Qt.AlignCenter)
        self.player_layout.addWidget(self.time_label)

        self.layout.addLayout(self.player_layout, stretch=3)

        # ---------------- RIGHT: QUEUE AREA ----------------
        self.queue_layout = QVBoxLayout()
        self.queue_layout.setAlignment(Qt.AlignTop)

        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.itemDoubleClicked.connect(self.play_selected_song)
        self.queue_layout.addWidget(self.queue_list)

        # Previous / Clear / Next controls
        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.play_previous)
        controls_layout.addWidget(self.prev_button)

        self.clear_button = QPushButton("Clear Queue")
        self.clear_button.clicked.connect(self.clear_queue)
        controls_layout.addWidget(self.clear_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.play_next)
        controls_layout.addWidget(self.next_button)

        self.queue_layout.addLayout(controls_layout)
        self.layout.addLayout(self.queue_layout, stretch=2)

        # --- Internal state ---
        self.queue = []
        self.current_index = -1
        self.is_paused = False
        self.total_length = 0
        self.last_pos = 0.0
        self.seek_offset = 0.0
        self.last_update_time = QTime.currentTime()

        # --- Timer for progress ---
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start()

        self.progress_bar.installEventFilter(self)

    # -------------------------------------------------------------
    #                       QUEUE MANAGEMENT
    # -------------------------------------------------------------
    def add_song_to_queue(self, path: str):
        if path and path not in self.queue:
            self.queue.append(path)
            self.queue_list.addItem(os.path.basename(path))
            print(f"🎶 Added to queue: {os.path.basename(path)}")

    def clear_queue(self):
        # Stop any music currently playing
        pygame.mixer.music.stop()

        # Clear all queue data
        self.queue.clear()
        self.queue_list.clear()
        self.current_index = -1
        self.total_length = 0
        self.last_pos = 0.0
        self.seek_offset = 0.0
        self.is_paused = False

        # Reset display
        self.song_label.setText("🧹 Queue cleared successfully.")
        self.time_label.setText("0:00 / 0:00")
        self.progress_bar.setValue(0)
        print("🧹 Queue cleared successfully and playback stopped.")
        
    # -------------------------------------------------------------
    #                       PLAYBACK CONTROL
    # -------------------------------------------------------------
    def play_selected_song(self, item):
        index = self.queue_list.row(item)
        self.play_song(index)

    def play_song(self, index):
        if 0 <= index < len(self.queue):
            song_path = self.queue[index]
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            self.current_index = index
            self.is_paused = False

            self.song_label.setText(f"🎵 Now Playing: {os.path.basename(song_path)}")
            self.progress_bar.setValue(0)
            self.last_update_time = QTime.currentTime()
            self.last_pos = 0.0
            self.seek_offset = 0.0

            audio = MP3(song_path)
            self.total_length = audio.info.length
            self.time_label.setText(f"0:00 / {self.format_time(self.total_length)}")

    def play_pause(self):
        if not self.queue:
            return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.last_update_time = QTime.currentTime()
        elif pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_paused = True
        else:
            self.play_song(0)

    def play_next(self):
        if self.queue and self.current_index + 1 < len(self.queue):
            self.play_song(self.current_index + 1)
        elif self.current_index + 1 >= len(self.queue):
            pygame.mixer.music.stop()
            self.song_label.setText("🎵 End of queue reached — stopping playback.")
            print("🎵 End of queue reached — stopping playback.")

    def play_previous(self):
        if self.queue and self.current_index > 0:
            self.play_song(self.current_index - 1)

    # -------------------------------------------------------------
    #                       PROGRESS & SEEK
    # -------------------------------------------------------------
    def update_progress(self):
        if self.total_length <= 0:
            return

        pos_ms = pygame.mixer.music.get_pos()
        elapsed_ms = self.last_update_time.msecsTo(QTime.currentTime())
        self.last_update_time = QTime.currentTime()

        raw_pos = (pos_ms / 1000.0) + self.seek_offset
        predicted_pos = self.last_pos + (elapsed_ms / 1000.0)
        smoothed_pos = (0.8 * predicted_pos) + (0.2 * raw_pos)
        smoothed_pos = max(0, min(smoothed_pos, self.total_length))
        self.last_pos = smoothed_pos

        progress = int((smoothed_pos / self.total_length) * 100)
        self.progress_bar.setValue(min(progress, 100))
        self.time_label.setText(
            f"{self.format_time(smoothed_pos)} / {self.format_time(self.total_length)}"
        )

        if not pygame.mixer.music.get_busy() and not self.is_paused:
            self.play_next()

    def eventFilter(self, source, event):
        if source == self.progress_bar and event.type() == QEvent.MouseButtonPress:
            if self.total_length > 0:
                ratio = event.pos().x() / self.progress_bar.width()
                new_time = ratio * self.total_length
                pygame.mixer.music.play(start=new_time)
                self.seek_offset = new_time
                self.is_paused = False
                self.last_update_time = QTime.currentTime()
                self.last_pos = new_time
                self.progress_bar.setValue(int(ratio * 100))
                self.time_label.setText(
                    f"{self.format_time(new_time)} / {self.format_time(self.total_length)}"
                )
                return True
        return super().eventFilter(source, event)

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
