# library_tab.py — Artist → Album → Song browser with thumbnails
import os
import json
from collections import defaultdict

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QMessageBox, QSpacerItem, QSizePolicy
)

AUDIO_EXTS = {".mp3", ".ogg", ".wav", ".flac", ".m4a"}

# --------- small utilities ---------
def _safe_get(d, *names, default=""):
    """Try multiple field names (case-insensitive-ish) from dict d."""
    for n in names:
        if n in d:
            return d[n]
    # be tolerant of different casings/underscores
    lowered = {k.lower(): v for k, v in d.items()}
    for n in names:
        v = lowered.get(n.lower())
        if v is not None:
            return v
    return default

def _make_placeholder_icon(size: QSize) -> QIcon:
    """Green-ish placeholder thumbnail for items without artwork."""
    w, h = size.width(), size.height()
    pm = QPixmap(w, h)
    pm.fill(QColor(0, 0, 0))
    p = QPainter(pm)
    # thin Matrix-green border
    p.setPen(QColor(0, 255, 102))
    p.drawRect(0, 0, w - 1, h - 1)
    p.end()
    return QIcon(pm)

def _icon_from_art(path, size: QSize) -> QIcon:
    if path and os.path.exists(path):
        pm = QPixmap(path)
        if not pm.isNull():
            return QIcon(pm.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return _make_placeholder_icon(size)

class LibraryTab(QWidget):
    """
    Three-level browser:
      Level 'artists' -> list of artists (with a sample album art thumb)
      Level 'albums'  -> albums for selected artist (album art)
      Level 'songs'   -> tracks for selected album (album art)
    Double-click on song adds to both Player queue and Playlist builder.
    """
    def __init__(self,
                 root_folder,  # kept for compatibility; not used by this browser
                 add_to_player_queue_callback,
                 add_to_playlist_queue_callback,
                 metadata_path=r"C:\Dev\Music_Player_Folder\music_metadata.json"):
        super().__init__()

        self.root_folder = os.path.normpath(root_folder)
        self.add_to_player_queue = add_to_player_queue_callback
        self.add_to_playlist_queue = add_to_playlist_queue_callback
        self.metadata_path = metadata_path

        # navigation state
        self.level = "artists"      # artists -> albums -> songs
        self.current_artist = None
        self.current_album = None

        # pre-sized icon
        self.thumb_size = QSize(80, 60)

        # data stores
        self.songs = []             # flat list of song dicts
        self.by_artist = defaultdict(list)     # artist -> [song dicts]
        self.by_artist_album = defaultdict(lambda: defaultdict(list))  # artist -> album -> [song dicts]
        self.album_art = dict()     # (artist, album) -> artwork_path (best guess)

        # ---------- UI ----------
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Header row with Back button (fixed top-left) and centered title
        header_row = QHBoxLayout()
        self.back_btn = QPushButton("⟵ Back")
        self.back_btn.setFixedHeight(32)
        self.back_btn.clicked.connect(self.on_back_clicked)
        self.back_btn.setEnabled(False)   # disabled on top-level
        header_row.addWidget(self.back_btn, 0, Qt.AlignLeft)

        header_row.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.header_label = QLabel("Library — Artists")
        self.header_label.setAlignment(Qt.AlignCenter)
        header_row.addWidget(self.header_label, 0, Qt.AlignCenter)

        header_row.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Optional reload button (reads metadata JSON again)
        self.reload_btn = QPushButton("Reload")
        self.reload_btn.setFixedHeight(32)
        self.reload_btn.clicked.connect(self.reload_metadata)
        header_row.addWidget(self.reload_btn, 0, Qt.AlignRight)

        root.addLayout(header_row)

        # Main list
        self.list = QListWidget()
        self.list.setIconSize(self.thumb_size)
        self.list.itemDoubleClicked.connect(self.on_item_double_clicked)
        root.addWidget(self.list)

        # load metadata and populate artists
        self.reload_metadata()

    # ---------- Data loading & indexing ----------
    def reload_metadata(self):
        """Read music_metadata.json (dict keyed by file path) and build indices."""
        try:
            if not os.path.exists(self.metadata_path):
                raise FileNotFoundError(f"Metadata file not found:\n{self.metadata_path}")

            with open(self.metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle dict-of-paths structure
            if isinstance(data, dict):
                songs = []
                for path, tags in data.items():
                    entry = {"path": path}
                    entry.update(tags)
                    songs.append(entry)
            elif isinstance(data, list):
                songs = data
            elif isinstance(data, dict) and "songs" in data:
                songs = data["songs"]
            else:
                songs = []

            self.songs = songs

            # Build indices
            self.by_artist.clear()
            self.by_artist_album.clear()
            self.album_art.clear()

            for s in self.songs:
                artist = _safe_get(s, "album_artist", "artist", "Album Artist")
                album = _safe_get(s, "album", "Album")
                path = _safe_get(s, "path", "file_path", "Path")
                art = _safe_get(s, "artwork", "artwork_path", "art_path", "ArtworkPath")

                artist = artist.strip() if isinstance(artist, str) else ""
                album = album.strip() if isinstance(album, str) else ""
                if not artist:
                    artist = "Unknown Artist"
                if not album:
                    album = "Unknown Album"

                self.by_artist[artist].append(s)
                self.by_artist_album[artist][album].append(s)

                key = (artist, album)
                if key not in self.album_art or not self.album_art[key]:
                    self.album_art[key] = art

            self.level = "artists"
            self.current_artist = None
            self.current_album = None
            self.back_btn.setEnabled(False)
            self.header_label.setText("Library — Artists")
            self.populate_artists()

        except Exception as e:
            QMessageBox.critical(self, "Metadata Error", f"Failed to read metadata:\n{e}")
    # ---------- Populate views ----------
    def populate_artists(self):
        self.list.clear()
        # sort artists alpha
        for artist in sorted(self.by_artist.keys(), key=lambda x: x.lower()):
            # pick an album (first) to get a thumbnail
            albums = self.by_artist_album[artist]
            art_path = None
            if albums:
                # choose the first album alphabetically for thumbnail
                first_album = sorted(albums.keys(), key=lambda x: x.lower())[0]
                art_path = self.album_art.get((artist, first_album))
            icon = _icon_from_art(art_path, self.thumb_size)

            item = QListWidgetItem(icon, artist)
            # store type & payload
            item.setData(Qt.UserRole, {"type": "artist", "artist": artist})
            self.list.addItem(item)

    def populate_albums(self, artist):
        self.list.clear()
        albums = self.by_artist_album.get(artist, {})
        for album in sorted(albums.keys(), key=lambda x: x.lower()):
            art_path = self.album_art.get((artist, album))
            icon = _icon_from_art(art_path, self.thumb_size)
            label = f"{album}"
            item = QListWidgetItem(icon, label)
            item.setData(Qt.UserRole, {"type": "album", "artist": artist, "album": album})
            self.list.addItem(item)

    def populate_songs(self, artist, album):
        self.list.clear()
        songs = self.by_artist_album.get(artist, {}).get(album, [])
        # get a shared album art for icon
        art_path = self.album_art.get((artist, album))
        icon = _icon_from_art(art_path, self.thumb_size)

        # Show "TrackNumber. Title" when possible; fall back to filename
        for s in songs:
            path = _safe_get(s, "path", "file_path", "Path")
            title = _safe_get(s, "title", "Title")
            track = _safe_get(s, "track_number", "track", "TrackNumber", "Track #")
            if not title:
                title = os.path.basename(path)

            if isinstance(track, (list, tuple)) and track:
                track_str = str(track[0])
            else:
                track_str = str(track) if track not in (None, "") else ""

            label = f"{track_str}. {title}" if track_str else title

            item = QListWidgetItem(icon, label)
            item.setData(Qt.UserRole, {"type": "song", "artist": artist, "album": album, "song": s})
            self.list.addItem(item)

    # ---------- Interactions ----------
    def on_back_clicked(self):
        if self.level == "songs":
            # go to albums for the current artist
            self.level = "albums"
            self.header_label.setText(f"{self.current_artist} — Albums")
            self.populate_albums(self.current_artist)
            # still can go back to artists
            self.back_btn.setEnabled(True)
            self.current_album = None
        elif self.level == "albums":
            # back to artists
            self.level = "artists"
            self.header_label.setText("Library — Artists")
            self.populate_artists()
            self.back_btn.setEnabled(False)

    def on_item_double_clicked(self, item: QListWidgetItem):
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
            # Double-click song -> add to BOTH queues
            self.add_to_player_queue(path)
            self.add_to_playlist_queue(path)

        else:
            # Safety: if an unknown type sneaks in, do nothing
            pass
