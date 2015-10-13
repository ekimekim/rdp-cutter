import gevent.lock


# We don't know if gspread is thread-safe/gevent-safe, let's assume no
gspread_lock = gevent.lock.RLock()


def update_column(sheet, row_id, column, value):
	"""In given row, sets the column with given column name (value in first row) to value"""
	with gspread_lock:
		col_id = sheet.row_values(1).index(column) + 1
		sheet.update_cell(row_id, col_id, value)
