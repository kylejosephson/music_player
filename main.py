import sys, time, os

# ----------------------------------------------------------
# Prevent PyInstaller first-run extraction errors
# ----------------------------------------------------------
if getattr(sys, 'frozen', False):
    meipath = sys._MEIPASS
    retries = 0
    while retries < 30:  # up to ~3 seconds
        if os.path.exists(meipath):
            break
        time.sleep(0.1)
        retries += 1

from safe_print import safe_print

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
# Environment setup — works in both dev & bundled EXE mode
# ----------------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS  # PyInstaller runtime dir
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

# --- Terminal colors for startup log ---
GREEN = "\033[92m"
RESET = "\033[0m"

# ----------------------------------------------------------
# Embedded Matrix-style QSS (no external style.qss required)
# ----------------------------------------------------------
STYLE_QSS = """
/* =============================================
   🎵 Kyle’s Music Player - Matrix Clean Edition
   Compatible with Desktop & Android
   ============================================= */

QWidget {
    background-color: #000000;
    color: #00FF66;
    font-family: "VT323", monospace;
    font-size: 20px;
}

/* --- Tabs --- */
QTabWidget::pane {
    border: 1px solid #00FF33;
    background-color: #000000;
    border-radius: 10px;
}

QTabBar::tab {
    background-color: #000000;
    color: #00FF66;
    border: 1px solid #00FF33;
    border-radius: 8px;
    padding: 10px 30px;
    margin: 4px;
    font-size: 22px;
}

QTabBar::tab:selected {
    background-color: #001a00;
    border: 1px solid #00FF99;
    color: #00FF99;
}

QTabBar::tab:hover {
    background-color: #002800;   /* subtle hover on desktop */
    color: #00FF99;
}

QTabBar::tab:pressed {
    background-color: #004400;   /* touch feedback for Android */
}

/* --- Buttons --- */
QPushButton {
    background-color: #000000;
    border: 1px solid #00FF33;
    border-radius: 10px;
    padding: 6px 16px;
    font-size: 20px;
    color: #00FF66;
}
QPushButton:hover {
    background-color: #002800;
    border: 1px solid #00FF99;
    color: #00FF99;
}
QPushButton:pressed {
    background-color: #004400;
    color: #00FF99;
}

/* --- Labels --- */
QLabel {
    color: #00FF66;
    font-size: 22px;
    font-weight: bold;
}

/* --- Lists --- */
QListWidget {
    border: 1px solid #00FF33;
    border-radius: 10px;
    background-color: #000000;
    color: #00FF66;
    font-size: 18px;
    selection-background-color: #003300;
    selection-color: #00FF99;
}

/* --- Progress Bar --- */
QProgressBar {
    border: 1px solid #00FF33;
    border-radius: 8px;
    background-color: #0a0a0a;
    height: 18px;
    color: #00FF66;
}
QProgressBar::chunk {
    background-color: #00FF33;
    border-radius: 8px;
}

/* --- Scrollbars --- */
QScrollBar:vertical {
    background: #000000;
    width: 12px;
    border: 1px solid #00FF33;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #00FF33;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #00FF99;
}
"""

# --- Ensure critical data files exist (in roaming appdata) ---
for filename in ["music_metadata.json", "playlists.json"]:
    file_path = os.path.join(ROAMING_DIR, filename)
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("{}")
        safe_print(f"{GREEN}🧾 Created new file:{RESET} {file_path}")
    else:
        safe_print(f"{GREEN}✅ Found existing file:{RESET} {file_path}")

safe_print(f"{GREEN}💾 {APP_NAME} initialized successfully.{RESET}\n")


# ----------------------------------------------------------
# Main Application Window
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
# Application Entry Point
# ----------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Apply embedded Matrix-style theme
    try:
        app.setStyleSheet(STYLE_QSS)
        safe_print("✅ Loaded embedded Matrix-style theme.")
    except Exception as e:
        safe_print(f"⚠️ Failed to apply embedded style: {e}")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
