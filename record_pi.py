#!/usr/bin/env python3

"""
    Conference Room Recorder
    Notes for Raspian:

        sudo apt install lame
        sudo apt install python3-pip
        sudo apt install libasound2-dev       
        sudo -H pip3 install pyalsaaudio
"""

import os
import sys
import time
from datetime import datetime
import alsaaudio
import solame as lame
from gpiozero import LED
from gpiozero import Button

USAGE = """
Usage: record.py [OPTION]...

  -d, --device      Specify the capture device.
  -h, --help        Print this message and exit.
  -l, --list        List capture devices and exit.
  -p, --path        Set the path to save MP3's to. 
  -r, --rate        Specify the capture devices rate; 44100, 48000, etc.
"""

MAX_RECORD_TIME = 60 * 60 * 3  # Three hours worth of seconds

# Button Blink Status Codes
GOOD = 1
FILE_PATH_ERROR = 2
DEVICE_OPEN_ERROR = 3
STREAM_OPEN_ERROR = 4
FILE_WRITE_ERROR = 5
BUFFER_OVERFLOW = 6

# Set up our GPIO
LED_GPIO = 18
BUTTON_GPIO = 24
led = LED(LED_GPIO)
led.off()

# Global for state control, True = recording
_RECORDING_STATE = False


def toggle_recording_state():
    """
    Callback function for gpiozero lib's Button.when_pressed property.
    Used to toggle whether we're in recording mode or not and to set the button LED state
    """
    global _RECORDING_STATE
    _RECORDING_STATE = not _RECORDING_STATE
    #led.value = _RECORDING_STATE
    print('recording_state', _RECORDING_STATE)
    if _RECORDING_STATE:
        led.blink(1,.5)
    else:
        led.off()


def led_blink(blinks):
    """
    Blink the record button light a series of times to indicate a status.
    """
    for _ in range(blinks):
        led.on()
        time.sleep(.5)
        led.off()
        time.sleep(.5)


def datestamp():
    """
    Give us a unique, sortable date-based file prefix in the format of '2019-12-31_2359.1234' .
    """
    return(datetime.now().strftime("%Y-%m-%d_%H%M.%S"))


"""
List audio devices and exit.
"""

for index, arg in enumerate(sys.argv):
    if arg in ['--list', '-l']:
        devices = alsaaudio.pcms(alsaaudio.PCM_CAPTURE)
        print("Listing audio capture hardware:")
        for device in devices:
            print('\t', device)
        exit()

for index, arg in enumerate(sys.argv):
    if arg in ['--help', '-h']:
        print(USAGE)
        exit()

# ok for onboard audio but for USB audio devices you'll probably need to specify it.
ALSA_DEVICE = 'default'
# TASCAM US 4x4 = plughw:CARD=US4x4,DEV=0
# Blue Yeti = plughw:CARD=Microphone,DEV=0

for index, arg in enumerate(sys.argv):
    if arg in ['--device', '-d'] and len(sys.argv) > index + 1:
        ALSA_DEVICE = sys.argv[index + 1]
        del sys.argv[index]
        del sys.argv[index]
        break

RATE = 44100  # Match the hardware rate or there will be trouble. Blue Yeti = 48000

for index, arg in enumerate(sys.argv):
    if arg in ['--rate', '-r'] and len(sys.argv) > index + 1:
        RATE = int(sys.argv[index + 1])
        del sys.argv[index]
        del sys.argv[index]
        break

RECORDING_PATH = "."

for index, arg in enumerate(sys.argv):
    if arg in ['--path', '-p'] and len(sys.argv) > index + 1:
        RECORDING_PATH = sys.argv[index + 1]
        del sys.argv[index]
        del sys.argv[index]
        break

if len(sys.argv) != 1:
    print(USAGE)
    exit()


if __name__ == "__main__":

    if not os.path.isdir(RECORDING_PATH):
        print('Recording path "%s" not accessible.' % RECORDING_PATH)
        led_blink(FILE_PATH_ERROR)
        quit()

    # Set the button callback
    button = Button(BUTTON_GPIO)
    button.when_pressed = toggle_recording_state

    # If we got this far, let's give an visual thumb's up
    led_blink(GOOD)

    # Configure Lame Encoder
    # It will stay open for the duration of the program
    lame.set_sample_rate(RATE)
    lame.set_num_channels(1)
    lame.set_mode(lame.MONO)
    lame.set_bit_rate(32)
    lame.init_parameters()

    while True:

        if _RECORDING_STATE:

            # Create pyAlsaAudio stream, settings
            capture = alsaaudio.PCM(
                alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, device=ALSA_DEVICE)
            capture.setchannels(1)
            capture.setrate(RATE)
            capture.setformat(alsaaudio.PCM_FORMAT_S16_LE)
            capture.setperiodsize(160)

            # Open a file descriptor for writing
            mp3filename = os.path.join(RECORDING_PATH, '%s.mp3' % datestamp())
            mp3file = open(mp3filename, 'wb')

            start_time = time.time()
            print('--> Recording %s started.' % mp3filename)

            while _RECORDING_STATE:

                # Grab some PCM data from the input device
                l, pcm = capture.read()
                if l:
                    mp3_data = lame.encode_buffer(pcm)
                    mp3file.write(mp3_data)

                # Have we been going too long?
                if time.time() - start_time >= MAX_RECORD_TIME:
                    toggle_recording_state()

            # Finish the MP3 encoding
            capture.close()
            mp3_data = lame.encode_flush()
            if len(mp3_data):
                mp3file.write(mp3_data)
            mp3file.close()
            print('--> %s finished.' % mp3filename)
