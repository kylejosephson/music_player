import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# --- Local imports ---
from player_tab import PlayerTab
from playlist_tab import PlaylistTab
from library_tab import LibraryTab
from sync_tab import SyncTab
from config import (
    ROAMING_DIR,
    LOCAL_DIR,
    ONEDRIVE_DATA_DIR,
    DEFAULT_MUSIC_DIR,
    APP_NAME,
)

# ----------------------------------------------------------
# 🧠 Environment setup — works in both dev & bundled EXE mode
# ----------------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS  # PyInstaller temporary runtime dir
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

# --- Terminal colors for startup log ---
GREEN = "\033[92m"
RESET = "\033[0m"

# --- Ensure critical data files exist ---
for filename in ["music_metadata.json", "playlists.json"]:
    file_path = os.path.join(ROAMING_DIR, filename)
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("{}")
        print(f"{GREEN}🧾 Created new file:{RESET} {file_path}")
    else:
        print(f"{GREEN}✅ Found existing file:{RESET} {file_path}")

print(f"{GREEN}💾 {APP_NAME} initialized successfully.{RESET}\n")


# ----------------------------------------------------------
# 🪩 Main Application Window
# ----------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kyle’s Music Player")
        self.setGeometry(300, 100, 1100, 700)

        # --- App icon (works for both .exe and dev mode) ---
        icon_path = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # --- Tab Container ---
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        self.tabs.setTabsClosable(False)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.setElideMode(Qt.ElideNone)
        self.setCentralWidget(self.tabs)

        # --- Player Tab ---
        self.player_tab = PlayerTab()
        self.tabs.addTab(self.player_tab, "🎵 Player")

        # --- Playlist Tab ---
        self.playlist_tab = PlaylistTab(self.player_tab)
        self.tabs.addTab(self.playlist_tab, "📜 Playlists")

        # --- Library Tab ---
        self.library_tab = LibraryTab(
            DEFAULT_MUSIC_DIR,
            add_to_player_queue_callback=self.player_tab.add_song_to_queue,
            add_to_playlist_queue_callback=self.playlist_tab.add_to_playlist_queue,
        )
        self.tabs.addTab(self.library_tab, "📚 Library")

        # --- Sync Tab ---
        self.sync_tab = SyncTab()
        self.tabs.addTab(self.sync_tab, "☁️ Sync")


# ----------------------------------------------------------
# 🚀 Application Entry Point
# ----------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Try to apply Matrix-style theme
    try:
        style_path = os.path.join(BASE_DIR, "style.qss")
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        print("✅ Loaded Matrix-style theme.")
    except Exception as e:
        print(f"⚠️ Could not load style.qss: {e}")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
