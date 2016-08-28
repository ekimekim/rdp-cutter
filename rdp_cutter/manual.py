import logging
import sys

from main import do_manual

if __name__ == '__main__':
	logging.basicConfig(level='DEBUG')
	do_manual(*sys.argv[1:])
