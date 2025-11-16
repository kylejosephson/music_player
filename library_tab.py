# library_tab.py — Artist → Album → Song browser with thumbnails
import os
import sys
import json
from collections import defaultdict

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QMessageBox, QSpacerItem, QSizePolicy
)
from config import ROAMING_DIR, LOCAL_DIR

from safe_print import safe_print

AUDIO_EXTS = {".mp3", ".ogg", ".wav", ".flac", ".m4a"}


# --------- small utilities ---------
def _safe_get(d, *names, default=""):
    for n in names:
        if n in d:
            return d[n]
    lowered = {k.lower(): v for k, v in d.items()}
    for n in names:
        v = lowered.get(n.lower())
        if v is not None:
            return v
    return default


def _make_placeholder_icon(size: QSize) -> QIcon:
    w, h = size.width(), size.height()
    pm = QPixmap(w, h)
    pm.fill(QColor(0, 0, 0))
    p = QPainter(pm)
    p.setPen(QColor(0, 255, 102))  # Matrix Green Border
    p.drawRect(0, 0, w - 1, h - 1)
    p.end()
    return QIcon(pm)


def _icon_from_art(path, size: QSize) -> QIcon:
    """Load album art safely from permanent cache."""
    if path:
        full_path = path if os.path.isabs(path) else os.path.join(LOCAL_DIR, path)
        if os.path.exists(full_path):
            pm = QPixmap(full_path)
            if not pm.isNull():
                return QIcon(pm.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return _make_placeholder_icon(size)


class LibraryTab(QWidget):
    """
    Three-level browser:
      Level 'artists' -> list of artists
      Level 'albums'  -> albums for artist
      Level 'songs'   -> tracks for album
    Double-click on song adds it to Player queue + Playlist builder.
    """

    def __init__(
        self,
        root_folder,
        add_to_player_queue_callback,
        add_to_playlist_queue_callback,
        metadata_path=None
    ):
        super().__init__()

        self.root_folder = os.path.normpath(root_folder)
        self.add_to_player_queue = add_to_player_queue_callback
        self.add_to_playlist_queue = add_to_playlist_queue_callback

        # metadata path
        if metadata_path is None:
            self.metadata_path = os.path.join(ROAMING_DIR, "music_metadata.json")
        else:
            self.metadata_path = metadata_path

        # ensure dirs exist
        os.makedirs(ROAMING_DIR, exist_ok=True)
        os.makedirs(LOCAL_DIR, exist_ok=True)
        os.makedirs(os.path.join(LOCAL_DIR, "cache", "artwork"), exist_ok=True)

        # ensure metadata file exists
        if not os.path.exists(self.metadata_path):
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump({}, f)
            safe_print(f"Created new metadata file at {self.metadata_path}")  # ✅

        # navigation state
        self.level = "artists"
        self.current_artist = None
        self.current_album = None

        self.thumb_size = QSize(80, 60)
        self.songs = []
        self.by_artist = defaultdict(list)
        self.by_artist_album = defaultdict(lambda: defaultdict(list))
        self.album_art = {}

        # ---------- UI ----------
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header_row = QHBoxLayout()

        self.back_btn = QPushButton("⟵ Back")
        self.back_btn.setFixedHeight(32)
        self.back_btn.clicked.connect(self.on_back_clicked)
        self.back_btn.setEnabled(False)
        header_row.addWidget(self.back_btn, 0, Qt.AlignLeft)

        header_row.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.header_label = QLabel("Library — Artists")
        self.header_label.setAlignment(Qt.AlignCenter)
        header_row.addWidget(self.header_label, 0, Qt.AlignCenter)

        header_row.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.reload_btn = QPushButton("Reload Library")
        self.reload_btn.setFixedHeight(32)
        self.reload_btn.clicked.connect(self.rescan_and_reload)
        header_row.addWidget(self.reload_btn, 0, Qt.AlignRight)

        root.addLayout(header_row)

        self.list = QListWidget()
        self.list.setIconSize(self.thumb_size)
        self.list.itemDoubleClicked.connect(self.on_item_double_clicked)
        root.addWidget(self.list)

        self.reload_metadata()

    # ---------- Data loading ----------
    def reload_metadata(self):
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                songs = [{"path": p, **tags} for p, tags in data.items()]
            elif isinstance(data, list):
                songs = data
            elif isinstance(data, dict) and "songs" in data:
                songs = data["songs"]
            else:
                songs = []

            self.songs = songs
            self.by_artist.clear()
            self.by_artist_album.clear()
            self.album_art.clear()

            for s in self.songs:
                artist = _safe_get(s, "album_artist", "artist", "Album Artist") or "Unknown Artist"
                album = _safe_get(s, "album", "Album") or "Unknown Album"
                art = _safe_get(s, "artwork", "artwork_path", "art_path", "ArtworkPath")

                self.by_artist[artist].append(s)
                self.by_artist_album[artist][album].append(s)
                key = (artist, album)
                if key not in self.album_art:
                    self.album_art[key] = art

            self.level = "artists"
            self.back_btn.setEnabled(False)
            self.header_label.setText("Library — Artists")
            self.populate_artists()

            safe_print(f"Library loaded {len(self.songs)} songs from metadata.")  # ✅

        except Exception as e:
            QMessageBox.critical(self, "Metadata Error", f"Failed to read metadata:\n{e}")

    # ---------- List population ----------
    def populate_artists(self):
        self.list.clear()
        for artist in sorted(self.by_artist.keys(), key=str.lower):
            albums = self.by_artist_album[artist]
            art_path = None
            if albums:
                first_album = sorted(albums.keys(), key=str.lower)[0]
                art_path = self.album_art.get((artist, first_album))
            icon = _icon_from_art(art_path, self.thumb_size)
            item = QListWidgetItem(icon, artist)
            item.setData(Qt.UserRole, {"type": "artist", "artist": artist})
            self.list.addItem(item)

    def populate_albums(self, artist):
        self.list.clear()
        albums = self.by_artist_album.get(artist, {})
        for album in sorted(albums.keys(), key=str.lower):
            art_path = self.album_art.get((artist, album))
            icon = _icon_from_art(art_path, self.thumb_size)
            item = QListWidgetItem(icon, album)
            item.setData(Qt.UserRole, {"type": "album", "artist": artist, "album": album})
            self.list.addItem(item)

    def populate_songs(self, artist, album):
        self.list.clear()
        songs = self.by_artist_album.get(artist, {}).get(album, [])
        art_path = self.album_art.get((artist, album))
        icon = _icon_from_art(art_path, self.thumb_size)
        for s in songs:
            path = _safe_get(s, "path", "file_path", "Path")
            title = _safe_get(s, "title", "Title") or os.path.basename(path)
            track = _safe_get(s, "track_number", "track", "TrackNumber", "Track #")
            track_str = str(track[0]) if isinstance(track, (list, tuple)) and track else str(track or "")
            label = f"{track_str}. {title}" if track_str else title
            item = QListWidgetItem(icon, label)
            item.setData(Qt.UserRole, {"type": "song", "artist": artist, "album": album, "song": s})
            self.list.addItem(item)

    # ---------- Navigation ----------
    def on_back_clicked(self):
        if self.level == "songs":
            self.level = "albums"
            self.header_label.setText(f"{self.current_artist} — Albums")
            self.populate_albums(self.current_artist)
            self.current_album = None

        elif self.level == "albums":
            self.level = "artists"
            self.header_label.setText("Library — Artists")
            self.populate_artists()
            self.back_btn.setEnabled(False)

    def on_item_double_clicked(self, item):
        payload = item.data(Qt.UserRole) or {}
        typ = payload.get("type")

        if typ == "artist":
            self.current_artist = payload["artist"]
            self.level = "albums"
            self.header_label.setText(f"{self.current_artist} — Albums")
            self.populate_albums(self.current_artist)
            self.back_btn.setEnabled(True)

        elif typ == "album":
            self.current_artist = payload["artist"]
            self.current_album = payload["album"]
            self.level = "songs"
            self.header_label.setText(f"{self.current_artist} — {self.current_album}")
            self.populate_songs(self.current_artist, self.current_album)
            self.back_btn.setEnabled(True)

        elif typ == "song":
            song = payload.get("song", {})
            path = _safe_get(song, "path", "file_path", "Path")
            if not path or not os.path.exists(path):
                QMessageBox.warning(self, "Error", f"File not found:\n{path}")
                return
            self.add_to_player_queue(path)
            self.add_to_playlist_queue(path)

    # ---------- Rescan ----------
    def rescan_and_reload(self):
        try:
            # Import rebuild function from bundled module
            from tag_extractor import rebuild_music_metadata

            # Perform metadata rebuild
            result = rebuild_music_metadata()

            safe_print(
                f"Metadata rebuilt! Total={result['total']}, "
                f"New={result['new']}, Removed={result['removed']}"
            )

            # Reload library from metadata file
            self.reload_metadata()

            QMessageBox.information(
                self,
                "Reload Complete",
                "Library successfully rescanned and reloaded!"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Reload Error",
                f"Failed to rebuild library:\n{e}"
            )