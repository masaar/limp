#!/usr/bin/python3

import argparse, os, logging, datetime

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, 'version.txt')) as f:
	__version__ = f.read()

parser = argparse.ArgumentParser()
parser.add_argument('--version', help='Show LIMP version and exit', action='version', version='LIMPd v{}'.format(__version__))
parser.add_argument('--install-deps', help='Install dependencies for LIMP and packages', action='store_true')
parser.add_argument('--env', help='Choose specific env')
parser.add_argument('--debug', help='Enable debug mode', action='store_true')
parser.add_argument('--log', help='Enable debug mode and log all debug messages to log file', action='store_true')
parser.add_argument('--packages', help='List of packages separated by commas to be loaded')
parser.add_argument('-p', '--port', help='Set custom port [default 8081]')
parser.add_argument('--test', help='Run specified test')
parser.add_argument('--test-flush', help='Flush previous test data collections', action='store_true')
parser.add_argument('--test-force', help='Force running all test steps even if one is failed', action='store_true')
parser.add_argument('--test-env', help='Run tests on selected env rather than sandbox env', action='store_true')
parser.add_argument('--test-breakpoint', help='Create debugger breakpoint upon failure of test.', action='store_true')
args = parser.parse_args()

logger = logging.getLogger('limp')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s  [%(levelname)s]  %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.setLevel(logging.INFO)

# [DOC] Parse runtime args
if args.install_deps:
	logger.setLevel(logging.DEBUG)
	logger.debug('Detected install_deps flag.')
	import subprocess, sys, os.path
	logger.debug('Attempting to install dependencies of LIMP.')
	subprocess.call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
	__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	dirs = [d for d in os.listdir(os.path.join(__location__, 'modules')) if os.path.isdir(os.path.join(__location__, 'modules', d))]
	for package in dirs:
		logger.debug('Checking package \'%s\' for \'requirements.txt\' file.', package)
		if os.path.exists(os.path.join(__location__, 'modules', package, 'requirements.txt')):
			logger.debug('File \'requirements.txt\' found! Attempting to install package dependencies.')
			subprocess.call([sys.executable, '-m', 'pip', 'install', '-r', os.path.join(__location__, 'modules', package, 'requirements.txt')])
	exit()

# [DOC] Check for logging options
if args.log:
	logger.removeHandler(handler)
	if not os.path.exists(os.path.join(__location__, 'logs')):
		os.makedirs(os.path.join(__location__, 'logs'))
	handler = logging.FileHandler(filename=os.path.join(__location__, 'logs', '{}.log'.format((datetime.datetime.utcnow().strftime('%d-%b-%Y')))))
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

from config import Config
Config._limp_version = __version__
Config.test = args.test
Config.test_flush = args.test_flush
Config.test_force = args.test_force
Config.test_env = args.test_env
Config.test_breakpoint = args.test_breakpoint
Config.env = args.env or os.getenv('ENV') or None
try:
	port = int(args.port)
except:
	port = os.getenv('PORT') or 8081
	logger.warning('Port should be in integer format. Defaulting to %s.', port)
if args.debug or args.test or os.getenv('DEBUG'):
	Config.debug = True
	logger.setLevel(logging.DEBUG)
packages = args.packages
if packages:
	packages = args.packages.split(',') + ['core']

from app import run_app

run_app(packages, port)