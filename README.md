A brief note here, because I don't have time to actually fix the problem:

There are several of my personal libraries that this code requires to be installed
that aren't on PyPI due to my own laziness.

The easiest way to install these such that the code will work will be to take the following files:
	libs/backoff.py
	libs/easycmd.py
	libs/gtools.py
from this git repo: https://github.com/ekimekim/pylibs
and put them in your PYTHONPATH such that they can be imported by rdp-cutter.

Again, sorry about this. I swear I'll fix this and get these libs properly PyPI'd soon.
