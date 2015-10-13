from glob import glob
from uuid import uuid4

from easycmd import cmd

from common import update_column


def process(row):
	"""For given row, perform the cutting process"""

	def update_state(state):
		update_column(row['id'], 'Processed by VST', state)

	update_state('Cutting in Progress')
	try:

		filebase = '/tmp/{}'.format(uuid4())
		source_file = youtube_dl(row['YouTube Link'], '{}-source'.format(filebase))
		convert(
			source=source_file,
			dest='{}-cut.m4a'.format(filebase),
			start=parse_time(row['Start Time']),
			end=parse_time(row['End Time']),
			title=row['Song'],
			artist=row['Artist'],
			category=row['Category'],
			fade_in=parse_fade(row['Fade In?']),
			fade_out=parse_fade(row['Fade Out?']),
		)

	except Exception:
		update_state('Cutting Error')
		raise
	else:
		update_state('Cutting Complete')


def youtube_dl(link, filebase):
	cmd(['youtube-dl', link, '-o', '{}.%(ext)s'.format(filebase)])
	filename, = glob('{}.*'.format(filebase))
	return filename


def convert(source, dest, start, end, title, artist, category, fade_in, fade_out):

	def format_filter(name, **kwargs):
		return '{}={}'.format(name, ':'.join('{}={}'.format(k, v) for k, v in kwargs.items()))

	def ffescape(s):
		# our technique here, rather than trying to determine all special chars, is to put everything in '
		# except for ' itself, and escape that.
		s = s.replace("'", r"'\''")
		return "'{}'".format(s)

	cut_args = []
	if start:
		cut_args += ['-ss', start]
	if end:
		cut_args += ['-t', end]

	map_args = ['-map', '0:a']

	filter_args = []
	if fade_in:
		filter_args += ['-filter', format_filter('afade', type='in', duration=fade_in)]
	if fade_out:
		filter_args += ['-filter', format_filter('afade', type='out', start_time=end-fade_out, duration=fade_out)]

	metadata = dict(title=title, artist=artist, genre=category)
	metadata_args = sum((
		['-metadata', '{}={}'.format(k, ffescape(v))]
		for k, v in metadata.items() if v
	), [])

	output_args = map_args + filter_args + metadata_args + [dest]
	input_args = cut_args + ['-i', source]
	cmd(['ffmpeg'] + input_args + output_args)
