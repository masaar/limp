#!/usr/bin/python3

import argparse, os, logging, datetime, sys

if sys.version_info.major != 3 or sys.version_info.minor not in [7, 8]:
	print('LIMPd can only run with Python3.7 or Python3.8. Exiting.')
	exit()

if sys.version_info.minor == 7:
	try:
		import typing, typing_extensions  # noqa

		typing.Literal = typing_extensions.Literal
		typing.TypedDict = typing_extensions.TypedDict
	except:
		only_install_deps = True

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, 'version.txt')) as f:
	__version__ = f.read()

packages = []

parser = argparse.ArgumentParser()
parser.add_argument(
	'--version',
	help='Show LIMP version and exit',
	action='version',
	version=f'LIMPd v{__version__}',
)
parser.add_argument(
	'--install-deps',
	help='Install dependencies for LIMP and packages',
	action='store_true',
)
parser.add_argument(
	'--install-user',
	help='Install dependencies with `--user` option',
	action='store_true',
)
parser.add_argument('--env', help='Choose specific env')
parser.add_argument('--debug', help='Enable debug mode', action='store_true')
parser.add_argument(
	'--log',
	help='Enable debug mode and log all debug messages to log file',
	action='store_true',
)
parser.add_argument(
	'--packages', help='List of packages separated by commas to be loaded', nargs='*'
)
parser.add_argument('-p', '--port', help='Set custom port [default 8081]')
parser.add_argument('--test', help='Run specified test')
parser.add_argument(
	'--test-skip-flush',
	help='Skip flushing previous test data collections',
	action='store_true',
)
parser.add_argument(
	'--test-force',
	help='Force running all test steps even if one is failed',
	action='store_true',
)
parser.add_argument(
	'--test-env',
	help='Run tests on selected env rather than sandbox env',
	action='store_true',
)
parser.add_argument(
	'--test-breakpoint',
	help='Create debugger breakpoint upon failure of test',
	action='store_true',
)
parser.add_argument(
	'--test-collections', help='Enable Test Collections Mode', action='store_true'
)
parser.add_argument(
	'--generate-ref',
	help='Generate API reference for loaded packages',
	action='store_true',
)
args = parser.parse_args()

logger = logging.getLogger('limp')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s  [%(levelname)s]  %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.setLevel(logging.INFO)

# [DOC] Parse runtime args
if args.install_deps:
	# [DOC] Change logging level to debug
	logger.setLevel(logging.DEBUG)
	logger.debug('Detected install_deps flag.')
	# [DOC] Create standard call command list
	pip_command = [sys.executable, '-m', 'pip', 'install']
	# [DOC] Check for install_user glag to install dependencies with --user option
	if args.install_user:
		logger.debug('Detected install_user flag.')
		pip_command.append('--user')
	# [DOC] Add -r option to use requirements.txt files.
	pip_command.append('-r')
	# [DOC] Install LIMP dependencies
	import subprocess, sys, os.path

	logger.debug('Attempting to install dependencies of LIMP.')
	subprocess.call(pip_command + ['requirements.txt'])
	__location__ = os.path.realpath(
		os.path.join(os.getcwd(), os.path.dirname(__file__))
	)
	dirs = [
		d
		for d in os.listdir(os.path.join(__location__, 'modules'))
		if os.path.isdir(os.path.join(__location__, 'modules', d))
	]
	# [DOC] Iterate over packages to find requirements.txt files
	for package in dirs:
		logger.debug(f'Checking package \'{package}\' for \'requirements.txt\' file.')
		if os.path.exists(
			os.path.join(__location__, 'modules', package, 'requirements.txt')
		):
			logger.debug(
				'File \'requirements.txt\' found! Attempting to install package dependencies.'
			)
			subprocess.call(
				pip_command
				+ [os.path.join(__location__, 'modules', package, 'requirements.txt')]
			)
	exit()
else:
	try:
		only_install_deps
		logger.error(
			'You are running Python 3.7, and some libraries used in LIMP require backport libraries to run. You should start LIMPd with install_deps flag. Exiting.'
		)
		exit()
	except:
		pass

# [DOC] Check for logging options
if args.log:
	logger.removeHandler(handler)
	if not os.path.exists(os.path.join(__location__, 'logs')):
		os.makedirs(os.path.join(__location__, 'logs'))
	handler = logging.FileHandler(
		filename=os.path.join(
			__location__,
			'logs',
			f'{datetime.datetime.utcnow().strftime("%d-%b-%Y")}.log',
		)
	)
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

# [DOC] Update Config with LIMPd args
from config import Config

Config._limp_version = __version__
Config._limp_location = __location__
Config.test = args.test
Config.test_skip_flush = args.test_skip_flush
Config.test_force = args.test_force
Config.test_env = args.test_env
Config.test_breakpoint = args.test_breakpoint
Config.test_collections = args.test_collections
Config.env = args.env or os.getenv('ENV') or None

# [DOC] Check for generate_ref mode
Config.generate_ref = args.generate_ref
if Config.generate_ref:
	if not os.path.exists(os.path.join(__location__, 'refs')):
		os.makedirs(os.path.join(__location__, 'refs'))

try:
	port = int(args.port)
except:
	port = os.getenv('PORT') or 8081
	logger.warning(f'Port should be in integer format. Defaulting to {port}.')
if args.debug or os.getenv('DEBUG'):
	Config.debug = True
	logger.setLevel(logging.DEBUG)
packages = args.packages
if packages:
	packages = args.packages + ['core']

import asyncio
from app import run_app

asyncio.run(run_app(packages, port))
