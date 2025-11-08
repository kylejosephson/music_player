import os
import json
import pygame
from mutagen.mp3 import MP3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QProgressBar,
    QGraphicsDropShadowEffect, QFrame
)
from PyQt5.QtCore import QTimer, Qt, QEvent, QTime
from PyQt5.QtGui import QFont, QPixmap, QColor
from config import BASE_DIR


class PlayerTab(QWidget):
    def __init__(self):
        super().__init__()
        pygame.mixer.init()

        # -------- Load metadata (for album art + tags) --------
        self.metadata_path = os.path.join(BASE_DIR, "music_metadata.json")
        self.metadata = self.load_metadata()

        # -------- Main Layout --------
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

        # -------- “Now Playing Info” Section --------
        info_frame = QFrame()
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(40, 70, 0, 0)
        info_layout.setSpacing(40)  # ✅ add horizontal space between artwork and info
        info_frame.setLayout(info_layout)
        self.player_layout.addWidget(info_frame)

        # Album Art
        self.album_art_label = QLabel()
        self.album_art_label.setFixedSize(200, 200)
        self.album_art_label.setStyleSheet("background-color: #000; border-radius: 10px;")
        self.set_album_art(None)

        # Glow Effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setColor(QColor("#00FF66"))
        glow.setOffset(0, 0)
        self.album_art_label.setGraphicsEffect(glow)
        info_layout.addWidget(self.album_art_label, alignment=Qt.AlignTop)

        # Metadata (right side)
        self.metadata_layout = QVBoxLayout()
        self.metadata_layout.setSpacing(6)  # tighter vertical spacing
        info_layout.addLayout(self.metadata_layout)

        font_key = QFont("Consolas", 10)
        font_value = QFont("Consolas", 10, QFont.Bold)

        self.labels = {}
        fields = ["Title", "Artist", "Album", "Year", "Genre"]
        for field in fields:
            row = QHBoxLayout()
            row.setSpacing(8)  # closer key/value
            key_label = QLabel(f"{field}:")
            key_label.setFont(font_key)
            # dimmer key
            key_label.setStyleSheet("color: #00CC44;")
            val_label = QLabel("N/A")
            val_label.setFont(font_value)
            # brighter value (slightly more than the standard matrix green)
            val_label.setStyleSheet("color: #00FF88;")
            self.labels[field.lower()] = val_label
            row.addWidget(key_label)
            row.addWidget(val_label)
            row.addStretch()
            self.metadata_layout.addLayout(row)

        self.metadata_layout.addStretch()

        # 🔧 IMPORTANT: add the left player panel to the main layout
        self.layout.addLayout(self.player_layout, stretch=3)

        # ---------------- RIGHT: QUEUE AREA ----------------
        self.queue_layout = QVBoxLayout()
        self.queue_layout.setAlignment(Qt.AlignTop)

        self.queue_list = QListWidget()
        self.queue_list.itemDoubleClicked.connect(self.play_selected_song)
        self.queue_layout.addWidget(self.queue_list)

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
        self.playback_finished = False

        # --- Timer for progress ---
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start()

        self.progress_bar.installEventFilter(self)

    # -------------------------------------------------------------
    def load_metadata(self):
        """Load music_metadata.json into memory."""
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def set_album_art(self, artwork_path):
        """Set album art image or default."""
        if artwork_path and os.path.exists(artwork_path):
            pixmap = QPixmap(artwork_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(200, 200)
            pixmap.fill(QColor("#111"))
        self.album_art_label.setPixmap(pixmap)

    # -------------------------------------------------------------
    def add_song_to_queue(self, path: str):
        if path and path not in self.queue:
            self.queue.append(path)
            self.queue_list.addItem(os.path.basename(path))
            print(f"🎶 Added to queue: {os.path.basename(path)}")

    def clear_queue(self):
        pygame.mixer.music.stop()
        self.queue.clear()
        self.queue_list.clear()
        self.current_index = -1
        self.total_length = 0
        self.last_pos = 0.0
        self.seek_offset = 0.0
        self.is_paused = False
        self.playback_finished = False

        self.song_label.setText("🧹 Queue cleared successfully.")
        self.time_label.setText("0:00 / 0:00")
        self.progress_bar.setValue(0)

        # Reset info area
        self.set_album_art(None)
        for field in self.labels.values():
            field.setText("N/A")

    # -------------------------------------------------------------
    def play_selected_song(self, item):
        index = self.queue_list.row(item)
        self.play_song(index)

    def play_song(self, index):
        if 0 <= index < len(self.queue):
            self.playback_finished = False
            song_path = self.queue[index]

            if not os.path.exists(song_path):
                self.song_label.setText(f"⚠️ File missing: {os.path.basename(song_path)}")
                return

            try:
                pygame.mixer.music.load(song_path)
                pygame.mixer.music.play()
            except Exception as e:
                self.song_label.setText(f"⚠️ Error playing: {os.path.basename(song_path)}")
                print(f"⚠️ {e}")
                return

            self.current_index = index
            self.is_paused = False
            self.song_label.setText(f"🎵 Now Playing: {os.path.basename(song_path)}")
            self.progress_bar.setValue(0)
            self.last_update_time = QTime.currentTime()
            self.last_pos = 0.0
            self.seek_offset = 0.0

            # --- Duration ---
            try:
                audio = MP3(song_path)
                self.total_length = audio.info.length
            except Exception:
                self.total_length = 0
            self.time_label.setText(f"0:00 / {self.format_time(self.total_length)}")

            # --- Update Metadata + Art ---
            self.update_metadata_display(song_path)

    def update_metadata_display(self, song_path):
        """Display metadata and album art from JSON."""
        entry = self.metadata.get(song_path)
        if entry:
            self.labels["title"].setText(entry.get("title", "N/A"))
            self.labels["artist"].setText(entry.get("album_artist", "N/A"))
            self.labels["album"].setText(entry.get("album", "N/A"))
            self.labels["year"].setText(entry.get("year", "N/A"))
            self.labels["genre"].setText(entry.get("genre", "N/A"))

            art_path = entry.get("artwork")
            if art_path:
                full_path = os.path.join(BASE_DIR, art_path)
                self.set_album_art(full_path)
            else:
                self.set_album_art(None)
        else:
            for field in self.labels.values():
                field.setText("N/A")
            self.set_album_art(None)

    # -------------------------------------------------------------
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
            self.playback_finished = True
            self.song_label.setText("🎵 End of queue reached — stopping playback.")

    def play_previous(self):
        if self.queue and self.current_index > 0:
            self.play_song(self.current_index - 1)

    # -------------------------------------------------------------
    def update_progress(self):
        if self.total_length <= 0 or self.playback_finished:
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

        if not pygame.mixer.music.get_busy() and not self.is_paused and not self.playback_finished:
            self.play_next()

    def eventFilter(self, source, event):
        if source == self.progress_bar and event.type() == QEvent.MouseButtonPress:
            if self.total_length > 0:
                ratio = event.pos().x() / self.progress_bar.width()
                new_time = ratio * self.total_length
                pygame.mixer.music.play(start=new_time)
                self.seek_offset = new_time
                self.is_paused = False
                self.playback_finished = False
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
