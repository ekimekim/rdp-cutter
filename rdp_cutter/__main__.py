import logging

import argh

from rdp_cutter.main import main

logging.basicConfig(level=logging.DEBUG)
argh.dispatch_command(main)
