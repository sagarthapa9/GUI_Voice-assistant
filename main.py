import speech_recognition as sr
import pyaudio
import time
import wave
import threading
import os
from pixels import Pixels
import valib
import response
import glob
import logging
import pygame


if os.environ.get('DISPLAY','') == '':
    print('no display found. Using :0.0')
    os.environ.__setitem__('DISPLAY', ':0.0')

r = sr.Recognizer()
pygame.init()

SCREEN_HEIGHT =320
SCREEN_WIDTH = 400

black = (0,0,0)
alpha = (0,88,255)
white = (255,255,255)
red = (200,0,0)
green = (0,200,0)
bright_red = (255,0,0)
bright_green = (0,255,0)
blue = (16,166,240)

gameDisplay = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption('GUI Speech Recognition')
clock= pygame.time.Clock()
gameDisplay.fill(white)
pygame.font.init()

def close():
    pygame.quit()
    quit()

def message_display(text, color, count):
    test_font = pygame.font.Font('freesansbold.ttf',32)
    text_surf = test_font.render(text, True, color)
    screen_Height = 100
    text_rec = text_surf.get_rect(center=(SCREEN_WIDTH/2, screen_Height + (count * 40)))
    gameDisplay.blit(text_surf, text_rec)



def text_objects(text, font):
    textSurface = font.render(text, True, alpha)
    return textSurface, textSurface.get_rect()
    

RESPEAKER_RATE = 44100                  # Sample rate of the mic.
RESPEAKER_CHANNELS = 1                  # Number of channel of the input device.
RESPEAKER_WIDTH = 2
RESPEAKER_INDEX = 2                     # run the check_device_id.py to get the mic index.
CHUNK = 1024                            # Number of frames per buffer.
WAVE_OUTPUT_FILEPATH = "/mnt/ramdisk/"  # Directory location ocation of all the output files.
recognized_text = ''                    # Global variable for storing  audio converted text


class voice:
    """
    __init__ method will create pyaudio stream object
    for the entire session. This stream will be used
    every time for voice detection from microphone.
    """
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            rate=RESPEAKER_RATE,
            format=pyaudio.paInt16,
            input_device_index=RESPEAKER_INDEX,
            channels=RESPEAKER_CHANNELS,
            input=True,
            frames_per_buffer=CHUNK)

    """
    process() method reads data from pyaudio stream for given duration.
    After read, it creates audio frame and save it to .wav file.
    it generates new WAV file every time it gets called.
    """
    def process(self, RECORD_SECONDS):
        frames = []
        for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        out_filename = WAVE_OUTPUT_FILEPATH + str(time.time()) + ".wav"
        wf = wave.open(out_filename, 'wb')
        wf.setnchannels(RESPEAKER_CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.p.get_format_from_width(RESPEAKER_WIDTH)))
        wf.setframerate(RESPEAKER_RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return out_filename

    """
    voice_command_processor() method reads data from .wav file and convert into text.
    it is using speech_recognition library and recognize_google option to convert speech
    into text.
    """
    def voice_command_processor(self, filename):
        global recognized_text
        with sr.AudioFile(filename) as source:
            #r.adjust_for_ambient_noise(source=source, duration=0.5)
            wait_time = 3
            while True:
                audio = r.record(source, duration=3)
                if audio:
                    break
                time.sleep(1)
                wait_time = wait_time - 1
                if wait_time == 0:
                    break

            try:
                recognized_text = r.recognize_google(audio)
            except sr.UnknownValueError as e:
                pass
            except sr.RequestError as e:
                logger.error("service is down")
                pass
            os.remove(filename)
            return recognized_text

# px = Pixels()  # Initializing the Pixel class for RE-SPEAKER PiHAT LED.
# px.wakeup()
# time.sleep(2)
# px.off()

a = voice()    # Initializing the voice class.

"""
Infinite loop:
    1. Reading microphone for 3 sec and generation .wav file.
    2. Creating thread with voice_command_processor() method for converting speech to text.
    3. IF wake word is detected (in my case Gideon):

        a. Clearing recognized_text global variable.
        b. Turing on the LED.
        c. Audio reply with "how can i help you"
        d. Start reading from pyaudio stream for next 5 sec for question.
        e. Convert the audio to text using voice_command_processor().
        f. Process the text using process_text() method from response.py.
        g. once the processing done, it will remove all the files from the output directory.
        f. turn off the LED.
"""
if __name__ == '__main__':
    count = 0
    logger = logging.getLogger('voice assistant')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("/mnt/ramdisk/voice.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        file_name = a.process(3)
        logger.info("wake_word said :: " + recognized_text)
        print("wake_word said :: " + recognized_text)

        if "Google" in recognized_text:
            logger.info("wake word detected...")
            recognized_text = ''
            gameDisplay.fill(white)
            #px.wakeup()
            #valib.audio_acknowlegded_playback()
            valib.audio_playback('hello')
            time.sleep(0.5)
            command_file_name = a.process(5)
            a.voice_command_processor(command_file_name)
            logger.info("you said :: " + recognized_text)
            print("you said :: " + recognized_text)

            if recognized_text != '':
               count += 1
               message_display(recognized_text, green, count)
               pygame.display.update()
            #px.think()
            status = response.process_text(recognized_text, a)
            print(status)
            while status == '':
                pass

            if status != '':
                count +=1
                message_display(status, blue, count )
                pygame.display.update()
            count = 0
            files = glob.glob(os.path.join(WAVE_OUTPUT_FILEPATH + '*.wav'))
            for file in files:
                os.remove(file)
            recognized_text = ''
            #px.off()
        else:
            t1 = threading.Thread(target=a.voice_command_processor, args=(file_name,))
            t1.start()

        pygame.display.update()
        clock.tick(60)


