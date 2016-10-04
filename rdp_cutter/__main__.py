import gevent.monkey
gevent.monkey.patch_all()

import logging

import argh

from rdp_cutter.main import main

logging.basicConfig(level=logging.DEBUG)
argh.dispatch_command(main)
