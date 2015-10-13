import json

import gevent
import gevent.lock
import gevent.pool

from argh import arg
from oauth2client.client import SignedJwtAssertionCredentials
import gspread

from cutting import process

SHEET_ID = '1ujf2QYjhlhJx4snZR1Ek5KXR-kA0b7cY5NdS3hu7h4I'

with open('creds.json') as f:
	CREDS = json.load(f)

# We don't know if gspread is thread-safe/gevent-safe, let's assume no
gspread_lock = gevent.lock.RLock()

def open_sheet()
	cred_object = SignedJwtAssertionCredentials(
		CREDS['client_email'],
		CREDS['private_key'],
		['https://spreadsheets.google.com/feeds'],
	)
	with gspread_lock:
		client = gspread.authorize(cred_object)
		return client.open_by_key(SHEET_ID).sheet1


def get_rows(sheet):
	"""
	Returns each row except the first as a dict, with keys taken from first row.
	Also adds 1-based row index under key 'id'
	"""
	with gspread_lock:
		rows = sheet.get_all_records()
	for n, row in enumerate(rows):
		row['id'] = n + 1
	return rows


def update_column(sheet, row_id, column, value):
	"""In given row, sets the column with given column name (value in first row) to value"""
	with gspread_lock:
		col_id = sheet.row_values(1).index(column) + 1
		sheet.update_cell(row_id, col_id, value)


def get_rows_to_do(sheet, restart_in_progress=False):
	"""Return all rows that are ready to be cut. If restart_in_progress, also include rows listed
	as already being cut (this is useful for recovery if they were interrupted)"""
	for row in get_rows(sheet):
		if row['Processed by VST'] == 'Ready to Cut':
			yield row
		elif restart_in_progress and row['Processed by VST'] == 'Cutting In Progress':
			yield row


def start_jobs(jobs, sheet, restart_in_progress=False):
	"""Find any new jobs to do and start them in the background"""
	for row in get_rows_to_do(sheet, restart_in_progress=restart_in_progress):
		jobs.spawn(process, row)


def main(interval=60, restart_in_progress=False):
	jobs = gevent.pool.Group()
	sheet = open_sheet()
	while True:
		start_jobs(jobs, sheet, restart_in_progress=restart_in_progress)
		restart_in_progress = False # restart in progress on first pass only (if at all)
		gevent.sleep(interval)


if __name__ == '__main__':
	argh.dispatch_command(main)
