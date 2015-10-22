
import gevent.monkey
gevent.monkey.patch_all()

import json
import logging

import gevent
import gevent.pool

import argh
from backoff import Backoff

from common import open_sheet, get_rows, update_column
from cutting import process

MAX_JOBS = 8


with open('config.json') as f:
	CONFIG = json.load(f)


def get_rows_to_do(sheet, restart_in_progress=False, restart_errors=False, restart_all=False):
	"""Return all rows that are ready to be cut. If restart_in_progress, also include rows listed
	as already being cut (this is useful for recovery if they were interrupted).
	If restart_errors, re-attempt any jobs that errored.
	If restart_all, restart everything."""
	logging.info("Checking for new jobs")
	for row in get_rows(sheet):
		if row['Ready for VST'] != 'Ready':
			continue
		state = row['Processed by VST']
		if restart_all:
			yield row
		elif state == 'Not Yet' or not state:
			yield row
		elif restart_in_progress and state == 'In Progress':
			yield row
		elif restart_errors and state == 'Errored':
			yield row


def start_jobs(jobs, sheet, no_update_state=False, **kwargs):
	"""Find any new jobs to do and start them in the background"""
	for row in get_rows_to_do(sheet, **kwargs):
		logging.debug("Trying to start job {}".format(row['id']))
		jobs.wait_available()
		if not no_update_state:
			update_column(sheet, row['id'], 'Processed by VST', 'In Progress')
		jobs.spawn(process, sheet, row, no_update_state=no_update_state)
		logging.debug("Started job {}".format(row['id']))


def main(interval=10, restart_in_progress=False, restart_errors=False, restart_all=False, no_update_state=False, log_level='DEBUG', one_pass=False):
	class Stop(BaseException): pass
	logging.basicConfig(level=log_level)
	jobs = gevent.pool.Pool(MAX_JOBS)
	backoff = Backoff(1, 60)
	try:
		while True:
			try:
				sheet = open_sheet(CONFIG['sheet_id'], CONFIG['worksheet_title'], CONFIG['creds'])
				backoff.reset()
				while True:
					start_jobs(jobs, sheet, restart_in_progress=restart_in_progress, restart_errors=restart_errors, restart_all=restart_all, no_update_state=no_update_state)
					if one_pass:
						raise Stop
					restart_in_progress = False # restart in progress on first pass only (if at all)
					restart_all = False
					gevent.sleep(interval)
			except Exception:
				logging.exception("Main loop failure")
				gevent.sleep(backoff.get())
	except KeyboardInterrupt:
		logging.warning("Interrupt recieved")
		jobs.kill(block=True)
	except Stop:
		pass
	logging.info("Waiting for {} jobs".format(len(jobs.greenlets)))
	jobs.join()


if __name__ == '__main__':
	argh.dispatch_command(main)
