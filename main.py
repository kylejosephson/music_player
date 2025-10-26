import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from player_tab import PlayerTab
from playlist_tab import PlaylistTab
from library_tab import LibraryTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kyle's Music Player")
        self.setGeometry(200, 100, 1000, 600)

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Tab system
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Player Tab
        self.player_tab = PlayerTab()
        self.tabs.addTab(self.player_tab, "Player")

        # Playlist Tab (requires reference to PlayerTab)
        self.playlist_tab = PlaylistTab(self.player_tab)
        self.tabs.addTab(self.playlist_tab, "Playlists")

        # Library Tab
        self.library_tab = LibraryTab()
        self.tabs.addTab(self.library_tab, "Library")

        # Connect Library → Player queue
        self.library_tab.add_to_queue_signal.connect(self.player_tab.add_song_to_queue)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
