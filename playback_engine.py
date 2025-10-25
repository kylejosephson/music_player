# playback_engine.py
import pygame

class PlaybackEngine:
    def __init__(self):
        pygame.mixer.init()
        self.current_song = None
        self.paused = False

    def load(self, filepath):
        self.current_song = filepath
        pygame.mixer.music.load(filepath)

    def play(self):
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
        else:
            pygame.mixer.music.play()

    def pause(self):
        pygame.mixer.music.pause()
        self.paused = True

    def stop(self):
        pygame.mixer.music.stop()
        self.paused = False

    def is_playing(self):
        return pygame.mixer.music.get_busy()

    def get_pos(self):
        return pygame.mixer.music.get_pos() / 1000  # seconds