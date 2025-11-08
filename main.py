import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from player_tab import PlayerTab
from playlist_tab import PlaylistTab
from library_tab import LibraryTab
from sync_tab import SyncTab
from config import BASE_DIR

# --- Determine base directory (works for .exe or dev mode) ---
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS  # Temporary folder PyInstaller uses for bundled data
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)  # Ensure working directory matches executable

# --- Matrix console colors (optional visual check) ---
GREEN = "\033[92m"
RESET = "\033[0m"

# --- Ensure core files exist ---
for file in ["music_metadata.json", "playlists.json"]:
    path = os.path.join(BASE_DIR, file)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("{}")
        print(f"{GREEN}🧾 Created empty file:{RESET} {file}")
    else:
        print(f"{GREEN}✅ File exists:{RESET} {file}")

print(f"{GREEN}💾 Environment check complete — all systems ready.{RESET}\n")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kyle's Music Player")
        self.setGeometry(300, 100, 1100, 700)

        # --- Set window icon from bundled or local path ---
        icon_path = os.path.join(BASE_DIR, "icon.ico")
        self.setWindowIcon(QIcon(icon_path))

        # --- Tab Widget ---
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        self.tabs.setTabsClosable(False)
        self.tabs.tabBar().setExpanding(False)  # no forced stretching
        self.tabs.setElideMode(Qt.ElideNone)    # no text cutoff
        self.setCentralWidget(self.tabs)

        # --- Player Tab ---
        self.player_tab = PlayerTab()
        self.tabs.addTab(self.player_tab, "🎵 Player")

        # --- Playlist Tab ---
        self.playlist_tab = PlaylistTab(self.player_tab)
        self.tabs.addTab(self.playlist_tab, "📜 Playlists")

        # --- Library Tab ---
        self.library_tab = LibraryTab(
            "C:\\Users\\kylej\\Music",
            add_to_player_queue_callback=self.player_tab.add_song_to_queue,
            add_to_playlist_queue_callback=self.playlist_tab.add_to_playlist_queue
        )
        self.tabs.addTab(self.library_tab, "📚 Library")

        # --- Sync Tab ---
        self.sync_tab = SyncTab()
        self.tabs.addTab(self.sync_tab, "☁️ Sync")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # === Apply Matrix-style theme (works in EXE or dev mode) ===
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
