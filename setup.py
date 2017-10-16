from setuptools import setup, find_packages

setup(
	name='rdp_cutter',
	version='0.0.1',
	author='Mike Lang',
	author_email='mikelang3000@gmail.com',
	description='Google sheets bot for RDP cutting',
	packages=find_packages(),
	install_requires=[
		"argh",
		"gevent",
		"gspread",
		"oauth2client",
	],
)
