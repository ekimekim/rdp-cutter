import json

import gevent
import gevent.pool

import argh

from common import open_sheet, get_rows
from cutting import process


with open('config.json') as f:
	CONFIG = json.load(f)


def get_rows_to_do(sheet, restart_in_progress=False, restart_errors=False):
	"""Return all rows that are ready to be cut. If restart_in_progress, also include rows listed
	as already being cut (this is useful for recovery if they were interrupted).
	If restart_errors, re-attempt any jobs that errored."""
	for row in get_rows(sheet):
		if row['Processed by VST'] == 'Ready to Cut':
			yield row
		elif restart_in_progress and row['Processed by VST'].startswith('Cutting In Progress'):
			yield row
		elif restart_errors and row['Processed by VST'].startswith('Cutting Error'):
			yield row


def start_jobs(jobs, sheet, **kwargs):
	"""Find any new jobs to do and start them in the background"""
	for row in get_rows_to_do(sheet, **kwargs):
		jobs.spawn(process, row)


def main(interval=60, restart_in_progress=False, restart_errors=False):
	jobs = gevent.pool.Group()
	sheet = open_sheet(CONFIG['sheet_id'], CONFIG['creds'])
	try:
		while True:
			start_jobs(jobs, sheet, restart_in_progress=restart_in_progress, restart_errors=restart_errors)
			restart_in_progress = False # restart in progress on first pass only (if at all)
			gevent.sleep(interval)
	except KeyboardInterrupt:
		print "Waiting for {} jobs".format(len(jobs.greenlets))
		jobs.join()


if __name__ == '__main__':
	argh.dispatch_command(main)
