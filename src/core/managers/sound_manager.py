import pygame as pg
from src.utils import load_sound, GameSettings

class SoundManager:
    def __init__(self):
        pg.mixer.init()
        pg.mixer.set_num_channels(GameSettings.MAX_CHANNELS)
        self.current_bgm = None
        self.master_volume = GameSettings.AUDIO_VOLUME   # 0.0 ~ 1.0
        self.is_muted = False
        
    def play_bgm(self, filepath: str):
        if self.current_bgm:
            self.current_bgm.stop()
        audio = load_sound(filepath)
        volume_to_use = 0 if self.is_muted else self.master_volume
        audio.set_volume(volume_to_use)
        audio.play(-1)
        self.current_bgm = audio
    def mute(self):
        self.is_muted = True
        if self.current_bgm:
            self.current_bgm.set_volume(0)

    def unmute(self):
        self.is_muted = False
        if self.current_bgm:
            self.current_bgm.set_volume(self.master_volume)
        
    def pause_all(self):
        pg.mixer.pause()

    def resume_all(self):
        pg.mixer.unpause()
        
    def play_sound(self, filepath, volume=0.7):
        sound = load_sound(filepath)
        sound.set_volume(volume)
        sound.play()

    def stop_all_sounds(self):
        pg.mixer.stop()
        self.current_bgm = None
          
        
    def set_volume(self, value: float):
        self.master_volume = max(0, min(1, value))
        if self.current_bgm and not self.is_muted:
            self.current_bgm.set_volume(self.master_volume)

    #notice set_volume is in pygame libarary and it has a file to tell you what pygame has that is mixer.pyi