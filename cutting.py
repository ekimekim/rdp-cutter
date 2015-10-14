
import logging
import os
import string
from glob import glob
from uuid import uuid4

from easycmd import cmd

from common import update_column


def process(row):
	"""For given row, perform the cutting process"""

	def update_state(state):
		update_column(row['id'], 'Processed by VST', state)

	try:

		update_state('Cutting in Progress - Downloading')
		filebase = '/tmp/{}'.format(uuid4())
		source_file = youtube_dl(row['YouTube Link'], '{}-source'.format(filebase))

		update_state('Cutting in Progress - Processing')
		dest_file = '{}-cut.m4a'.format(filebase)
		convert(
			source=source_file,
			dest=dest_file,
			start=parse_time(row['Start Time']),
			end=parse_time(row['End Time']),
			title=row['Song'],
			artist=row['Artist'],
			category=row['Category'],
			fade_in=parse_fade(row['Fade In?']),
			fade_out=parse_fade(row['Fade Out?']),
		)

		update_state('Cutting in Progress - Uploading')
		name = row['Song'] or 'no-title'.format(row['id'])
		name = name.replace(' ', '_')
		name = ''.join(c for c in name.lower() if c in string.letters + string.digits + '._-')
		name = '{}-{}'.format(row['id'], name)
		url = upload(dest_file, name)
		update_column(row['id'], 'Processed Link', url)

	except Exception:
		logging.exception("Error while cutting {}".format(row))
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
		cut_args += ['-t', end - start]

	map_args = ['-map', '0:a']

	filters = []
	if fade_in:
		filters.append(format_filter('afade', type='in', start_time=0, duration=fade_in))
	if fade_out:
		# we need to know duration, hopefully we can work it out from inputs
		# if we can't, we fall back to an ffprobe call
		if not end:
			end = get_audio_length(source)
		if not start:
			start = 0
		duration = end - start
		filters.append(format_filter('afade', type='out', start_time=duration-fade_out, duration=fade_out))
	filter_args = ['-filter', ','.join(filters)] if filters else []

	metadata = dict(title=title, artist=artist, genre=category)
	metadata_args = sum((
		['-metadata', '{}={}'.format(k, ffescape(v))]
		for k, v in metadata.items() if v
	), [])

	output_args = ['-strict', '-2'] + map_args + filter_args + metadata_args + [dest]
	input_args = cut_args + ['-i', source]
	cmd(['ffmpeg', '-y'] + input_args + output_args)


def get_audio_length(filename):
	args = [
		'ffprobe',
		'-select_streams', 'a:0',
		'-show_entries', 'format=duration',
		'-of', 'default=noprint_wrappers=1:nokey=1',
		filename,
	]
	output = cmd(args)
	return int(output)


def upload(source, name):
	_, ext = os.path.splitext(source)
	name = '{}.{}'.format(name, ext.lstrip('.'))
	cmd(['scp', source, 'tyranicmoron:public_html/rdp/{}'.format(name)])
	return 'http://tyranicmoron.uk/~ekimekim/rdp/{}'.format(name)


if __name__ == '__main__':
	# for testing
	import sys, logging
	logging.basicConfig(level=logging.DEBUG)
	source, dest, start, end, title, artist, category, fade_in, fade_out = sys.argv[1:]
	convert(source, dest, int(start), int(end), title, artist, category, int(fade_in), int(fade_out))
