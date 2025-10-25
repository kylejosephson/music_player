# playback_engine.py
import pygame

class PlaybackEngine:
    def __init__(self):
        pygame.mixer.init()
        self.current_song = None
        self.paused = False
        self.playing = False

    def load(self, filepath):
        """Load a song from the given file path."""
        self.current_song = filepath
        pygame.mixer.music.load(filepath)
        self.paused = False
        self.playing = False

    def play(self):
        """Play or resume the current song."""
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
        elif not self.playing:
            pygame.mixer.music.play()
            self.playing = True

    def pause(self):
        """Pause playback safely."""
        if self.playing and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True

    def stop(self):
        """Stop playback completely."""
        pygame.mixer.music.stop()
        self.playing = False
        self.paused = False

    def is_actively_playing(self):
        """
        Return True if a song is playing and not paused.
        Pygame's get_busy() returns False briefly when paused — 
        so we must use both flags.
        """
        return pygame.mixer.music.get_busy() and not self.paused

    def is_paused(self):
        """Return True if playback is currently paused."""
        return self.paused

    def get_pos(self):
        """Return current playback position (seconds)."""
        pos = pygame.mixer.music.get_pos()
        return max(0, pos / 1000)