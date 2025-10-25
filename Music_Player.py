import sys
import os
import time
import pygame
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QFileDialog, QListWidget, QHBoxLayout, QGraphicsDropShadowEffect,
    QLabel, QSlider
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor


# Clickable progress bar (seek support)
class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.pos().x()
            ratio = max(0.0, min(1.0, x / max(1, self.width())))
            new_val = int(self.minimum() + ratio * (self.maximum() - self.minimum()))
            self.setValue(new_val)
            self.sliderReleased.emit()
        super().mousePressEvent(event)


class MusicPlayer(QWidget):
    def __init__(self):
        super().__init__()
        pygame.mixer.init()
        self.setWindowTitle("Kyle's Music Player")
        self.setGeometry(300, 300, 600, 420)
        self.setMinimumSize(420, 320)

        # --- Window glow effect (fixed to prevent bleed) ---
        window_shadow = QGraphicsDropShadowEffect(self)
        window_shadow.setBlurRadius(25)
        window_shadow.setXOffset(0)
        window_shadow.setYOffset(0)
        window_shadow.setColor(QColor(0, 120, 215, 160))
        self.setGraphicsEffect(window_shadow)
        self.setStyleSheet("background-clip: border;")  # prevent interior glow bleeding

        # Layout
        root = QVBoxLayout(self)

        # Add Songs
        self.add_button = QPushButton("Add Songs")
        self.add_button.clicked.connect(self.add_songs)
        root.addWidget(self.add_button)

        # Playlist
        self.playlist = QListWidget()
        self.playlist.itemDoubleClicked.connect(self.play_selected_song)
        root.addWidget(self.playlist)

        # Progress bar + time label
        progress_row = QHBoxLayout()
        self.progress_slider = ClickableSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setFixedHeight(24)
        self.progress_slider.sliderReleased.connect(self.seek_from_slider)

        # Static neon-green progress bar style
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #2d2d2d;
                height: 10px;
                background: #141414;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #39ff14;
                border: 1px solid #39ff14;
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #39ff14, stop:1 #00cc00
                );
                border-radius: 5px;
            }
            QSlider::add-page:horizontal {
                background: #0d0d0d;
                border-radius: 5px;
            }
        """)
        slider_glow = QGraphicsDropShadowEffect(self.progress_slider)
        slider_glow.setBlurRadius(18)
        slider_glow.setXOffset(0)
        slider_glow.setYOffset(0)
        slider_glow.setColor(QColor(57, 255, 20, 90))
        self.progress_slider.setGraphicsEffect(slider_glow)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_row.addWidget(self.progress_slider, stretch=5)
        progress_row.addWidget(self.time_label, stretch=1)
        root.addLayout(progress_row)

        # Playback buttons
        controls = QHBoxLayout()
        self.prev_button = QPushButton("⏮ Previous")
        self.prev_button.clicked.connect(self.play_previous)
        controls.addWidget(self.prev_button)

        self.play_pause_button = QPushButton("▶ Play / ⏸ Pause")
        self.play_pause_button.clicked.connect(self.play_pause)
        controls.addWidget(self.play_pause_button)

        self.next_button = QPushButton("Next ⏭")
        self.next_button.clicked.connect(self.play_next)
        controls.addWidget(self.next_button)
        root.addLayout(controls)

        # Playback state
        self.songs = []
        self.current_index = -1
        self.paused = False
        self.song_length = 0.0
        self.current_pos = 0.0
        self._last_tick = time.perf_counter()

        # Update timer
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start()

    # ---------- Song management ----------
    def add_songs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select MP3 files", "", "Music Files (*.mp3)"
        )
        for f in files:
            if f not in self.songs:
                self.songs.append(f)
                self.playlist.addItem(os.path.basename(f))

    def play_selected_song(self, item):
        index = self.playlist.row(item)
        self.play_song(index)

    # ---------- Playback ----------
    def play_song(self, index: int):
        if 0 <= index < len(self.songs):
            self.current_index = index
            path = self.songs[index]
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self.paused = False
            self.playlist.setCurrentRow(index)
            try:
                self.song_length = pygame.mixer.Sound(path).get_length()
            except Exception:
                self.song_length = 0.0
            self.current_pos = 0.0
            self._last_tick = time.perf_counter()

    def play_pause(self):
        if not self.songs:
            return

        if self.current_index == -1:
            self.play_song(0)
            return

        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            self._last_tick = time.perf_counter()
        else:
            pygame.mixer.music.pause()
            self.paused = True

    def play_next(self):
        if self.songs:
            next_index = (self.current_index + 1) % len(self.songs)
            self.play_song(next_index)

    def play_previous(self):
        if self.songs:
            prev_index = (self.current_index - 1) % len(self.songs)
            self.play_song(prev_index)

    # ---------- Seeking ----------
    def seek_from_slider(self):
        if self.song_length <= 0 or self.current_index == -1:
            return
        frac = self.progress_slider.value() / 1000.0
        new_time = max(0.0, min(self.song_length, frac * self.song_length))
        pygame.mixer.music.play(start=new_time)
        self.paused = False
        self.current_pos = new_time
        self._last_tick = time.perf_counter()

    # ---------- Progress ----------
    def update_progress(self):
        now = time.perf_counter()
        dt = now - self._last_tick
        self._last_tick = now

        if self.current_index == -1 or self.song_length <= 0:
            self.time_label.setText("0:00 / 0:00")
            self.progress_slider.setValue(0)
            return

        if not self.paused and pygame.mixer.music.get_busy():
            self.current_pos += dt

        if self.current_pos < 0:
            self.current_pos = 0
        if self.current_pos > self.song_length:
            self.current_pos = self.song_length

        self.time_label.setText(f"{self._fmt(self.current_pos)} / {self._fmt(self.song_length)}")
        if self.song_length > 0:
            self.progress_slider.setValue(int((self.current_pos / self.song_length) * 1000))

        if not self.paused and (self.song_length - self.current_pos) <= 0.15:
            self.play_next()

    @staticmethod
    def _fmt(seconds: float) -> str:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02d}"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
            font-size: 12pt;
        }
        QPushButton {
            background-color: #2d2d2d;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 6px;
        }
        QPushButton:hover {
            background-color: #3d3d3d;
            border: 1px solid #0078d7;
        }
        QPushButton:pressed {
            background-color: #0078d7;
            color: white;
        }
        QListWidget {
            background-color: #252525;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 4px;
        }
    """)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())