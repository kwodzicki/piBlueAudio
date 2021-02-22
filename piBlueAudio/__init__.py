import logging
from logging import handlers

import os

LOG     = logging.getLogger(__name__)
LOG.setLevel( logging.DEBUG )

LOGFILE = '/var/log/BluetoothCLT.log'
LOGFILE = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'BluetoothCTL', 'BluetoothCLT.log')

os.makedirs( os.path.dirname( LOGFILE ), exist_ok = True )

RFH = handlers.RotatingFileHandler( LOGFILE, maxBytes = 2**20, backupCount=1 )
RFH.setFormatter(logging.Formatter( '%(asctime)s [%(levelname)s] %(message)s' ) )
RFH.setLevel( logging.DEBUG )
LOG.addHandler( RFH )

del RFH
