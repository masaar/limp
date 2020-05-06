import argparse, os, logging, datetime, sys

logger = logging.getLogger('limp')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s  [%(levelname)s]  %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.setLevel(logging.INFO)

__location__ = None
__version__ = None


def limp_cli():
	global sys, os

	global __location__, __version__

	if sys.version_info.major != 3 or sys.version_info.minor != 8:
		print('LIMP CLI can only run with Python3.8. Exiting.')
		exit()

	__location__ = os.path.realpath(
		os.path.join(os.getcwd(), os.path.dirname(__file__))
	)

	with open(os.path.join(__location__, 'data', 'version.txt')) as f:
		__version__ = f.read()

	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--version',
		help='Show LIMP version and exit',
		action='version',
		version=f'LIMP CLI v{__version__}',
	)

	subparsers = parser.add_subparsers(
		title='Commnad', description='LIMP CLI command to run', dest='command'
	)

	parser_create = subparsers.add_parser('create', help='Create new LIMP app')
	parser_create.set_defaults(func=create)
	parser_create.add_argument('app_name', type=str, help='Name of the app to create')
	parser_create.add_argument(
		'app_path',
		type=str,
		nargs='?',
		help='Path of the app to discover its dependecies. [default $CWD]',
		default='$CWD',
	)

	parser_install = subparsers.add_parser(
		'install_deps', help='Install dependencies of LIMP app'
	)
	parser_install.set_defaults(func=install_deps)
	parser_install.add_argument(
		'app_path',
		type=str,
		nargs='?',
		help='Path of the app to discover its dependecies. [default $CWD]',
		default='$CWD',
	)
	parser_install.add_argument(
		'--install-user',
		help='Install dependencies with `--user` option',
		action='store_true',
	)

	parser_launch = subparsers.add_parser('launch', help='Launch LIMP app')
	parser_launch.set_defaults(func=launch)
	parser_launch.add_argument(
		'app_path',
		type=str,
		nargs='?',
		help='Path of the app to discover its dependecies. [default $CWD]',
		default='$CWD',
	)
	parser_launch.add_argument('--env', help='Choose specific env')
	parser_launch.add_argument('--debug', help='Enable debug mode', action='store_true')
	parser_launch.add_argument(
		'--log',
		help='Enable debug mode and log all debug messages to log file',
		action='store_true',
	)
	parser_launch.add_argument('-p', '--port', help='Set custom port [default 8081]')
	parser_launch.add_argument(
		'--force-admin-check',
		help='Force ADMIN doc checked and updated, if ADMIN doc is changed',
		action='store_true',
	)
	parser_launch.add_argument(
		'--test-collections', help='Enable Test Collections Mode', action='store_true'
	)

	parser_test = subparsers.add_parser('test', help='Test LIMP app')
	parser_test.set_defaults(func=test)
	parser_test.add_argument('test_name', type=str, help='Name of the test to run')
	parser_test.add_argument(
		'app_path',
		type=str,
		nargs='?',
		help='Path of the app to discover its dependecies. [default $CWD]',
		default='$CWD',
	)
	parser_test.add_argument(
		'--skip-flush',
		help='Skip flushing previous test data collections',
		action='store_true',
	)
	parser_test.add_argument(
		'--force',
		help='Force running all test steps even if one is failed',
		action='store_true',
	)
	parser_test.add_argument(
		'--env',
		help='Run tests on selected env rather than sandbox env',
		action='store_true',
	)
	parser_test.add_argument(
		'--breakpoint',
		help='Create debugger breakpoint upon failure of test',
		action='store_true',
	)

	parser_ref = subparsers.add_parser(
		'generate_ref', help='Generate LIMP app reference'
	)
	parser_ref.set_defaults(func=generate_ref)
	parser_ref.add_argument(
		'app_path',
		type=str,
		nargs='?',
		help='Path of the app to discover its dependecies. [default $CWD]',
		default='$CWD',
	)

	args = parser.parse_args()
	args.func(args)
	
	exit()

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
			logger.debug(
				f'Checking package \'{package}\' for \'requirements.txt\' file.'
			)
			if os.path.exists(
				os.path.join(__location__, 'modules', package, 'requirements.txt')
			):
				logger.debug(
					'File \'requirements.txt\' found! Attempting to install package dependencies.'
				)
				subprocess.call(
					pip_command
					+ [
						os.path.join(
							__location__, 'modules', package, 'requirements.txt'
						)
					]
				)
		exit()

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


def create(args: argparse.Namespace):
	print('create function')
	print(args)
	exit()

def install_deps(args: argparse.Namespace):
	print('install_deps function')
	print(args)
	exit()

def launch(args: argparse.Namespace):
	global os
	global __version__, __location__
	# [DOC] Update Config with LIMP CLI args
	from limp.config import Config

	Config._limp_version = __version__
	Config._limp_location = __location__
	Config.test_collections = args.test_collections
	Config.env = args.env or os.getenv('ENV') or None
	Config.force_admin_check = (
		args.force_admin_check or os.getenv('LIMP_ADMIN_CHECK') or False
	)

	try:
		port = int(args.port)
	except:
		port = os.getenv('PORT') or 8081
		logger.warning(f'Port should be in integer format. Defaulting to {port}.')
	if args.debug or os.getenv('DEBUG'):
		Config.debug = True
		logger.setLevel(logging.DEBUG)

	import asyncio
	from limp.app import run_app

	app_path = args.app_path
	if app_path == '$CWD':
		app_path = os.getcwd()

	asyncio.run(run_app(port=port, app_path=app_path))

def test(args: argparse.Namespace):
	pass

def generate_ref(args: argparse.Namespace):
	# [DOC] Update Config with LIMP CLI args
	from limp.config import Config
	# [DOC] Check for generate_ref mode
	Config.generate_ref = args.generate_ref
	if Config.generate_ref:
		if not os.path.exists(os.path.join(__location__, 'refs')):
			os.makedirs(os.path.join(__location__, 'refs'))

limp_cli()