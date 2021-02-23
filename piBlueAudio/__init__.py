import logging
from logging import handlers

import os

# Set up logger for pacakge
LOG     = logging.getLogger(__name__)
LOG.setLevel( logging.DEBUG )

LOGFILE = '/tmp/BluetoothCLT.log'

os.makedirs( os.path.dirname( LOGFILE ), exist_ok = True )

RFH = handlers.RotatingFileHandler( LOGFILE, maxBytes = 2**20, backupCount=1 )
RFH.setFormatter(logging.Formatter( '%(asctime)s [%(levelname)s] %(message)s' ) )
RFH.setLevel( logging.DEBUG )
LOG.addHandler( RFH )

del RFH

# Name of the local sink in this computer
# You can get it by calling : pactl list short sinks
# AUDIOSINK="alsa_output.platform-bcm2835_AUD0.0.analog-stereo"
#AUDIOSINK="alsa_output.platform-bcm2835_audio.analog-stereo.equalizer"
#AUDIOSINK="alsa_output.platform-bcm2835_audio.analog-stereo"
AUDIOSINK    = "EQSink"     # Name of audio sink to use
RATE         = 44100        # Sample rate in Hz

# Audio Output for raspberry-pi
# 0=auto, 1=headphones, 2=hdmi.
AUDIO_OUTPUT = 1

# If on, this computer is not discovearable when an audio device is connected
# 0=off, 1=on
ENABLE_BT_DISCOVER=1



