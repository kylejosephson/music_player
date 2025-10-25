# main.py
import sys
from PyQt5.QtWidgets import QApplication, QTabWidget, QMainWindow
from player_tab import PlayerTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kyle's Music Player")
        self.setGeometry(200, 200, 800, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tabs
        self.player_tab = PlayerTab()
        self.tabs.addTab(self.player_tab, "Player")

        # Library and Playlist tabs will come later
        # self.library_tab = LibraryTab()
        # self.playlist_tab = PlaylistTab()
        # self.tabs.addTab(self.library_tab, "Library")
        # self.tabs.addTab(self.playlist_tab, "Playlists")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())