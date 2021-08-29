from gtts import gTTS
from pygame import mixer
import os

AUDIO_PLAYBACK_FILENAME = "/mnt/ramdisk/audio_play_back.mp3"
ACKNOWLEGED_SOUND = "/home/pi/python-projects/acknowlegded.mp3"

def audio_playback(text):
    tts = gTTS(text=text, lang='en-us')
    tts.save(AUDIO_PLAYBACK_FILENAME)
    mixer.init()
    mixer.music.load(AUDIO_PLAYBACK_FILENAME)
    mixer.music.play()
    while mixer.music.get_busy():
        pass
    os.remove(AUDIO_PLAYBACK_FILENAME)

def audio_acknowlegded_playback():
    mixer.init()
    mixer.music.load(ACKNOWLEGED_SOUND)
    mixer.music.play()
    while mixer.music.get_busy():
        pass
    os.remove(ACKNOWLEGED_SOUND)
