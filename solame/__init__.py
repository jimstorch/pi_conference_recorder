
"""
Wrap the Lame encoder shared library using the CTypes module.  The Lame library should
be installed with: 

    Using ~2,477 kB:

        sudo apt install lame 
        
    Or using ~1,063 kB:

        sudo apt install libmp3lame-dev

    Or using ~ 478 kB:

        sudo apt install libmp3lame0
"""

import ctypes
from ctypes.util import find_library

STEREO = int(0)
JOINT_STEREO = int(1)
MONO = int(3)

# Load the library
_lib = ctypes.CDLL(find_library('mp3lame'))
if _lib == None:
    raise ImportError('Unable to load shared library: mp3lame')

# Init.  The default is a  Joint-Stereo, 44.1khz, 128kbps CBR at Quality 5
_lib.lame_init.argtypes = []
_lib.lame_init.restype = ctypes.c_void_p
# Get a pointer to the internal Global Flags structure
_gfp = _lib.lame_init()


def init_parameters():
    """
    Apply the settings in the global flags.  MUST be invoked before encoding!!!
    """
    _lib.lame_init_params.argtypes = [ctypes.c_void_p]
    _lib.lame_init_params.restype = ctypes.c_int
    _lib.lame_init_params(_gfp)


def get_version():
    """
    Return the version number of libmp3lame.so/dll as a string.
    """
    _lib.get_lame_version.argtypes = []
    _lib.get_lame_version.restype = ctypes.c_char_p
    return _lib.get_lame_version().decode('ascii')


def set_sample_rate(sample_rate):
    """
    Tell lame what sample rate the PCM buffer was encoded at.  Default is 44100hz.
    """
    _lib.lame_set_in_samplerate.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _lib.lame_set_in_samplerate.restype = ctypes.c_int
    _lib.lame_set_in_samplerate(_gfp, sample_rate)


def get_sample_rate():
    """
    Return the current sample setting from Lame's global flags.
    """
    _lib.lame_get_in_samplerate.argtypes = [ctypes.c_void_p]
    _lib.lame_get_in_samplerate.restype = ctypes.c_int
    return _lib.lame_get_in_samplerate(_gfp)


def set_num_channels(chan_count):
    """
    Set the number of channels, 1 = mono, 2 = stereo.  Stereo is not currently working.
    """
    _lib.lame_set_num_channels.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _lib.lame_set_num_channels.restype = ctypes.c_int
    _lib.lame_set_num_channels(_gfp, chan_count)


def get_num_channels():
    """
    Return the current number of channels from Lame's global flags.
    """
    _lib.lame_get_num_channels.arttypes = [ctypes.c_void_p]
    _lib.lame_get_num_channels.restype = ctypes.c_int
    return _lib.lame_get_num_channels(_gfp)


def set_mode(mode):
    """
    Set the encoding mode; 0 = Stereo, 1 = Joint Stereo, 3 = Mono.
    Mode 2 (dual channel) is not supported by Lame.
    """
    _lib.lame_set_mode.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _lib.lame_set_mode.restype = ctypes.c_int
    _lib.lame_set_mode(_gfp, mode)


def get_mode():
    """
    Return the encoding mode from Lame's global flags.
    """
    _lib.lame_get_mode.argtypes = [ctypes.c_void_p]
    _lib.lame_get_mode.restype = ctypes.c_int
    return _lib.lame_get_mode(_gfp)


def set_bit_rate(bit_rate):
    """
    Set the encoding bit rate (in Khz).  Default is 128.
    Probably the most important Lame setting as the encoder will overrride other settings to comply.
    """
    _lib.lame_set_brate.argtypes = [ctypes.c_void_p]
    _lib.lame_set_brate.restype = ctypes.c_int
    _lib.lame_set_brate(_gfp, bit_rate)


def get_bit_rate():
    """
    Return the encoding bit rate (in Khz) from Lame's global flags.
    """
    _lib.lame_get_brate.argtypes = [ctypes.c_void_p]
    _lib.lame_get_brate.restype = ctypes.c_int
    return _lib.lame_get_brate(_gfp)


def set_quality(quality):
    """
    Set the quality on the encoding process 0 - 9. Lower is better quality.
    This is about encoding speed, not file size. Default is 5.
    """
    if quality < 0 or quality > 9:
        raise ValueError('Quality must be 0-9.')
    _lib.lame_set_quality.argtypes = [ctypes.c_void_p]
    _lib.lame_set_quality.restype = ctypes.c_int
    _lib.lame_set_quality(_gfp, quality)


def get_quality():
    """
    Return the encoding quality from Lame's global flags.
    """
    _lib.lame_get_quality.argtypes = [ctypes.c_void_p]
    _lib.lame_get_quality.restype = ctypes.c_int
    return _lib.lame_get_quality(_gfp)


def encode_buffer_interleaved(pcm_data):
    """
    I am a broken monster that will kill your eardrums.
    """
    _lib.lame_encode_buffer_interleaved.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                                    ctypes.c_int, ctypes.POINTER(ctypes.c_char), ctypes.c_int]
    _lib.lame_encode_buffer_interleaved.restype = ctypes.c_int
    num_samples = int(len(pcm_data) / 2)
    mp3buffer_size = int(1.25 * num_samples + 7200)
    mp3buffer = (ctypes.c_char * mp3buffer_size)()
    mp3buffer_used = _lib.lame_encode_buffer_interleaved(
        _gfp, pcm_data, num_samples, mp3buffer, mp3buffer_size)
    print(mp3buffer_used)
    return mp3buffer[0:int(mp3buffer_used)]


def encode_buffer(pcm_data):
    """
    Given a buffer of 16 bit PCM data, encode it to a block of MP3. 
    Currently, I only work in mono.
    """
    _lib.lame_encode_buffer.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                        ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_char), ctypes.c_int]
    _lib.lame_encode_buffer.restype = ctypes.c_int
    num_samples = int(len(pcm_data) / 2) # 16 bits per Sample
    mp3buffer_size = int(1.25 * num_samples + 7200)
    mp3buffer = (ctypes.c_char * mp3buffer_size)()
    # Seems hacky to pass the same PCM data in both channels but the second
    # channel seems to be mandatory even when mono encoding from mono sources.
    # Looking at the lame header, it appears that Lame averages both into a mono channel.
    mp3buffer_used = _lib.lame_encode_buffer(
        _gfp, pcm_data, pcm_data, num_samples, mp3buffer, mp3buffer_size)
    # print(mp3buffer_used)
    return mp3buffer[0:mp3buffer_used]


def encode_flush():
    """
    Flush the encoding buffers and return final frames (if any).
    """
    _lib.lame_encode_flush.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
    _lib.lame_encode_flush.restype = ctypes.c_int
    mp3buffer = (ctypes.c_char * 7200)()
    mp3buffer_used = _lib.lame_encode_flush(_gfp, mp3buffer, int(7200))
    # print(mp3buffer_used)
    return mp3buffer[0:mp3buffer_used]


def close():
    """
    Free internal data structures.
    """
    _lib.lame_close.restype = ctypes.c_int
    _lib.lame_close.argtypes = [ctypes.c_void_p]
    _lib.lame_close(_gfp)
