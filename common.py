
import logging

import gevent.lock

import gspread
from oauth2client.client import SignedJwtAssertionCredentials

# We don't know if gspread is thread-safe/gevent-safe, let's assume no
gspread_lock = gevent.lock.RLock()


def open_sheet(sheet_id, creds):
	cred_object = SignedJwtAssertionCredentials(
		creds['client_email'],
		creds['private_key'],
		['https://spreadsheets.google.com/feeds'],
	)
	with gspread_lock:
		client = gspread.authorize(cred_object)
		return client.open_by_key(sheet_id).sheet1


def get_rows(sheet):
	"""
	Returns each row except the first as a dict, with keys taken from first row.
	Also adds 1-based row index under key 'id'
	"""
	with gspread_lock:
		rows = sheet.get_all_records()
	for n, row in enumerate(rows):
		row['id'] = n + 2
	return rows


def update_column(sheet, row_id, column, value):
	"""In given row, sets the column with given column name (value in first row) to value"""
	with gspread_lock:
		col_id = sheet.row_values(1).index(column) + 1
		logging.debug("Updating cell ({},{}) = {!r}".format(row_id, col_id, value))
		sheet.update_cell(row_id, col_id, value)
