import logging

import os, re, time

from subprocess import Popen, PIPE, STDOUT
from threading import Thread, Event

from .audio import volume_max

CMD     = ['bluetoothctl']
MAC     = re.compile( '((?:[0-9A-F]{2}[:]?){6})' )
SLEEP   = 1.0

class BluetoothCTL( Thread ):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.log   = logging.getLogger(__name__)
    self._proc = None
    self._info = {'devices' : {}, 'controllers' : {}}

  def start(self, *args, **kwargs):
    super().start(*args, **kwargs)                                              # Start the thread
    time.sleep( SLEEP )                                                         # Wait to make sure it's started

  def run(self):
    self.log.debug('Thread started!')
    self._proc = Popen( CMD, stdin=PIPE, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
    line = self._proc.stdout.readline()                                         # Read line from stdout
    while line != '':                                                           # While line is NOT emtpy
      self.parseLine( line )                                                    # Parse the line
      line = self._proc.stdout.readline()                                       # Read another line
    self._proc.stdin.close()                                                    # Close stdin
    self._proc.stdout.close()                                                   # Close stdout
    self._proc = None                                                           # Set proc to None
    self.log.debug('Thread dead!')

  def sendCMD(self, cmd):
    """
    Send a command to the bluetoothctl subprocess
    
    Arguments:
      cmd (str) : Command to send to bluetoothctl

    Keyword arguments:
      None.

    Returns:
      None.

    """

    if self._proc:                                                              # If proc is set
      self._proc.stdin.write( f'{cmd}{os.linesep}' )                            # Write command to stdin
      self._proc.stdin.flush()                                                  # Flush stdin
      time.sleep( SLEEP )

  def exit(self, *args, **kwargs):
    """Issues 'exit' command to bluetoothctl to stop the process"""

    self.log.debug('Powering off bluetooth')
    self.power('off')
    self.log.debug('Issuing exit to bluetoothctl')
    self.sendCMD( 'exit' )

  def parseLine(self, line):
    """
    Parse information out of line from bluetoothctl information

    Arguments:
      line (str) : Line read from the bluetoothctl subprocess

    Keyword arguments:
      None.

    Returns:
      None.

    """

    line = line.rstrip()                                                        # Strip off return characters
    if 'Failed' in line:                                                        # If 'Failed' in line
      self.log.error( line )                                                    # Log error
      return                                                                    # Return from function

    mac = MAC.findall(line)                                                     # Try to find MAC address in line
    if len(mac) == 1:                                                           # If MAC found
      tmp    = line.split()                                                     # Split line on space
      status = tmp[0]                                                           # Get status [NEW], [CHG], [DEL]
      obj    = tmp[1]                                                           # Get object (Device/Controller)
      mac    = tmp[2]                                                           # Get MAC address
      info   = tmp[3:]                                                          # Get information
      if not any( stat in status for stat in ('NEW', 'CHG', 'DEL') ): return    # If none of the strings (NEW, CHG, DEL) in the status, just return

      if obj == 'Device':                                                       # If object is Device
        dev = self._info['devices']                                             # Set dev to dictionary of devices
      elif obj == 'Controller':                                                 # If object is controller
        dev = self._info['controllers']                                         # Set dev to dictionary of controller objects
      else:                                                                     # Else
        self.log.warning( f'Unknown object type: {obj}' )                       # Log error
        return                                                                  # Return
      self._macCheck(mac, dev)
      if 'NEW' in status:                                                       # If NEW is in status
        self.log.info( f'New device being added: {mac}' )                       # Log info
        if obj == 'Device':                                                     # If is Device object
          self.trust( mac )                                                     # Trust the device
      elif 'DEL' in status:                                                     # Else, if DEL in status
        self.log.info( f'Device being deleted: {mac}' )                         # Log info
        if mac in dev:
          del dev[mac]                                                          # Remove device from dictionary
      elif 'CHG' in status:                                                     # Else, if CHG in status
        self.log.debug( f'Device state changed: {info}' )                       # Log debug
        if info[0][-1] == ':':                                                  # If colon (:) in first element of info
          opt = info[0][:-1]                                                    # Get option name as first element of info without colon
          val = ' '.join(info[1:])                                              # Get value as all but first element of info joined on space
          if val == 'no':                                                       # If val is no
            val = False                                                         # Set val false
          elif val == 'yes':                                                    # Else, if val is yes
            val = True                                                          # Set val True
          dev[mac][opt] = val                                                   # Add option and value to object dictionary
          if opt.lower() == 'connected':
            self._connected( val )
      else:                                                                     # Else
        self.log.warning( f'Unrecognized command: {line}' )                     # Log warning

  def _macCheck(self, mac, dev):
    if mac not in dev:
      dev[mac] = {}

  def _connected(self, state):
    if state:                                                                   # If a device has connected, disable discoverable
      self.log.debug('Device connected, discoverable disabled' )
      self.discoverable( 'off' )                                                # Turn off discoveralbe
      volume_max()
    else:                                                                       # Else, a device has DISconnected
      nn = 0                                                                    # Initialize counters
      for dev in self._info['devices'].values():                                # Iterate over values in devices dictionary; don't care about device MAC, just device status
        for key, val in dev.items():                                            # Iterate over key/value pairs for device status
          if key.lower() == 'connected':                                        # If the key is connected
            nn += val                                                           # Increment nn by connected state (1 for connected, 0 for disconnnected)
            break                                                               # Break; don't need to keep iterating
      if nn > 0:                                                                # If nn is NOT zero, then other devices are connected
        self.log.debug('Other device(s) connected, discoverable NOT enabled' )
      else:
        self.log.debug('No other device(s) connected, discoverable enabled' )
        self.discoverable()                                                     # Enable discoverable

  def power(self, state='on'):
    """
    Change bluetooth power state

    Arguments:
      None.

    Keyword arguments:
      state (str) : Determines state of power (on,off). Default: on

    Returns:
      None.

    """

    self.log.debug(f'Changing power state: {state}')
    self.sendCMD( f'power {state}' )

  def discoverable(self, state='on'):
    """
    Change bluetooth discoverable state

    Arguments:
      None.

    Keyword arguments:
      state (str) : Determines state of power (on,off). Default: on

    Returns:
      None.

    """

    self.sendCMD( f'discoverable {state}' )

  def pairable(self, state='on'):
    """
    Change bluetooth pairable state

    Arguments:
      None.

    Keyword arguments:
      state (str) : Determines state of power (on,off). Default: on

    Returns:
      None.

    """

    self.sendCMD( f'pairable {state}' )


  def trust(self, mac):
    """
    Trust a device given MAC address 

    Arguments:
      mac (str) : MAC address of device to trust.

    Keyword arguments:
      None.

    Returns:
      None.

    """

    self.log.info( f'Device being trusted: {mac}' )                             # Log info
    self.sendCMD( f'trust {mac}' )                                              # Trust the device
