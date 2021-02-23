import logging

import sys, os
import time
import glob
import subprocess as SP

from . import AUDIOSINK, RATE, AUDIO_OUTPUT, ENABLE_BT_DISCOVER

# User used to execute pulseaudio, an active session must be open to avoid errors
USER      = "pi"


def find( path, name):
  files = []
  for root, dirs, items in os.walk( path ):
    for item in items:
      if item == name:
        files.append( os.path.join( root, item ) )
  return files

## This function set volume to maximum and choose the right output
## return 0 on success
def volume_max():
  log = logging.getLogger( __name__ )
  log.info( "setting volume to maximum" )
  # Set the audio OUTPUT on raspberry pi
  # amixer cset numid=3 <n> 
  # where n is 0=auto, 1=headphones, 2=hdmi. 
  SP.call( ["amixer", "-c", str(AUDIO_OUTPUT), "cset", "numid=1", "100%"] )

  # Set volume level to 100 percent
  SP.call( ["amixer", "set", "Master", "100%"] )
  #return SP.call( ["pacmd", "set-sink-volume", "0", str(2**16)] )


## This function add the pulseaudio loopback interface from source to sink
## The source is set by the bluetooth mac address using XX_XX_XX_XX_XX_XX format.
## param: XX_XX_XX_XX_XX_XX
## return 0 on success


def add_from_mac():
  log = logging.getLogger(__name__)
  if len( sys.argv ) == 1: # zero params
    log.warning( "Mac not found" )
    return None

  mac = sys.argv[1] # Mac is parameter-1

  # Setting source name
  bluez_dev = f"bluez_source.{mac}"
  log.info(  f"bluez source: {mac}, {bluez_dev}" )
  # This script is called early, we just wait to be sure that pulseaudio discovered the device
  time.sleep( 1.0 )
  # Very that the source is present
  cmd = ["pactl", "list", "short"]
  try:
    confirm = bluez_dev in SP.check_output( cmd ).decode()
  except Exception as err:
    log.exception( "Error getting pactl list" )
    return None
  if confirm:
    log.info( f"Adding the loopback interface:  {bluez_dev}" )
    cmd = ["pactl", "load-module", "module-loopback", f"source={bluez_dev}", f"sink={AUDIOSINK}", f"rate={RATE}", "adjust_time=0" ]
    log.info( f"Adding loopback: {cmd}" )

    # This command route audio from bluetooth source to the local sink..
    # it's the main goal of this script
    return SP.call( cmd )
  else:
    log.error( f"Unable to find a bluetooth device compatible with pulsaudio using the following device: {bluez_dev}" )
    return -1

def readMAC( fpath ):
  log = logging.getLogger(__name__)
  log.info( f"Reading in MAC address from file : {fpath}" )
  if os.path.isfile( fpath ):
    with open(fpath, "r") as fid:
      mac = "_".join( fid.read().split(":") )
    return mac
  return None

## This function will detect the bluetooth mac address from input device and configure it.
## Lots of devices are seen as input devices. But Mac OS X is not detected as input
## return 0 on success
def detect_mac_from_input():
  log = logging.getLogger(__name__)

  log.info( "Detecting mac from input devices" )
  for dev in glob.glob("/sys/devices/virtual/input/input*"):
    fpath = os.path.join( dev, "name")
    mac   = readMAC( fpath )
    if mac:
      log.info( f"Read in mac {mac} from file {fpath}" )
      errCode = add_from_mac( mac )
      if errCode == 0: return 0
  return -1


## This function will detect the bt mac address from dev-path and configure it.
## Devpath is set by udev on device link
## return 0 on success
def detect_mac_from_devpath():
  log = logging.getLogger(__name__)
  devPath = os.environ.get("DEVPATH", False)
  if devPath: 
    log.info( "Detecting mac from DEVPATH" )
    path = f"/sys{devPath}"
    for dev in find( path, "address"):
      mac = readMAC( dev )
      if mac:
        errCode = add_from_mac( mac )
        if errCode == 0: return 0
    else:
      log.warning( "DEVPATH not set, wrong bluetooth device?" )
      return -2
    return -1 

def main():
  log = logging.getLogger(__name__)
  ## Detecting if an action is set
  action = os.environ.get("ACTION", None)
  log.info( action )
  if action is None:
    raise Exception( "The script must be called from udev." )
  
  # Switch case
  if action == "add":
    # Turn off bluetooth discovery before connecting existing BT device to audio
    if ENABLE_BT_DISCOVER == 1:
      log.info( "Set computer as hidden" )
      SP.call( ["sudo", "hciconfig", "hci0", "noscan"] )
    # Turn volume to max
    volume_max()
  
    # Detect BT Mac Address from input devices
    okay = detect_mac_from_input()
  
    # Detect BT Mac address from device path on a bluetooth event
    if okay != 0:
      if os.environ.get("$SUBSYSTEM", "") == "bluetooth":
        okay = detect_mac_from_devpath()
  
    # Check if the add was successfull, otherwise display all available sources
    if okay != 0:
      log.error( "Your bluetooth device is not detected!" )
      log.error( "Available sources are:" )
      log.error( SP.check_output( ["pactl", "list", "short", "sources"] ) )
    else:
      log.info( "Device successfully added" )

  
  elif action == "remove":
    # Turn on bluetooth discovery if device disconnects
    if ENABLE_BT_DISCOVER == 1:
      log.info( "Set computer as visible" )
      SP.call( ["sudo", "hciconfig", "hci0", "piscan"] )
      
    self.info( "Removed" )
  else:
    log.warning( f"Unsuported action: {action}" )


