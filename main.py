import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from player_tab import PlayerTab
from playlist_tab import PlaylistTab
from library_tab import LibraryTab
from sync_tab import SyncTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kyle's Music Player")
        self.setGeometry(300, 100, 800, 500)

        # Tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Player tab
        self.player_tab = PlayerTab()
        self.tabs.addTab(self.player_tab, "🎵 Player")

        # Playlist tab
        self.playlist_tab = PlaylistTab(self.player_tab)
        self.tabs.addTab(self.playlist_tab, "📜 Playlists")

        # Library tab (dual callbacks: to player queue AND playlist-builder queue)
        self.library_tab = LibraryTab(
            "C:\\Users\\kylej\\Music",
            add_to_player_queue_callback=self.player_tab.add_song_to_queue,
            add_to_playlist_queue_callback=self.playlist_tab.add_to_playlist_queue
        )
        self.tabs.addTab(self.library_tab, "📚 Library")

        self.sync_tab = SyncTab()
        self.tabs.addTab(self.sync_tab, "☁️ Sync")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
