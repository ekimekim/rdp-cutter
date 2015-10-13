import json

import gevent
import gevent.pool

import argh

from common import open_sheet, get_rows
from cutting import process


with open('config.json') as f:
	CONFIG = json.load(f)



def get_rows_to_do(sheet, restart_in_progress=False):
	"""Return all rows that are ready to be cut. If restart_in_progress, also include rows listed
	as already being cut (this is useful for recovery if they were interrupted)"""
	for row in get_rows(sheet):
		if row['Processed by VST'] == 'Ready to Cut':
			yield row
		elif restart_in_progress and row['Processed by VST'].startswith('Cutting In Progress'):
			yield row


def start_jobs(jobs, sheet, restart_in_progress=False):
	"""Find any new jobs to do and start them in the background"""
	for row in get_rows_to_do(sheet, restart_in_progress=restart_in_progress):
		jobs.spawn(process, row)


def main(interval=60, restart_in_progress=False):
	jobs = gevent.pool.Group()
	sheet = open_sheet(CONFIG['sheet_id'], CONFIG['creds'])
	while True:
		start_jobs(jobs, sheet, restart_in_progress=restart_in_progress)
		restart_in_progress = False # restart in progress on first pass only (if at all)
		gevent.sleep(interval)


if __name__ == '__main__':
	argh.dispatch_command(main)
