from limp import __version__

from typing import Literal, Any

import argparse, os, logging, datetime, sys, subprocess, asyncio, traceback, shutil, urllib.request, re, tarfile, string, random

logger = logging.getLogger('limp')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s  [%(levelname)s]  %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.setLevel(logging.INFO)


def limp_cli():
	global sys, os

	if sys.version_info.major != 3 or sys.version_info.minor != 8:
		print('LIMP CLI can only run with Python3.8. Exiting.')
		exit()

	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--version',
		help='Show LIMP version and exit',
		action='version',
		version=f'LIMP CLI v{__version__}',
	)

	subparsers = parser.add_subparsers(
		title='Command', description='LIMP CLI command to run', dest='command'
	)

	parser_create = subparsers.add_parser('create', help='Create new LIMP app')
	parser_create.set_defaults(func=create)
	parser_create.add_argument('app_name', type=str, help='Name of the app to create')
	parser_create.add_argument(
		'app_path',
		type=str,
		nargs='?',
		help='Path to create new LIMP app. [default .]',
		default='.',
	)
	parser_create.add_argument(
		'--default-config',
		help='Create new LIMP app with default config',
		action='store_true',
	)

	parser_install = subparsers.add_parser(
		'install_deps', help='Install dependencies of LIMP app'
	)
	parser_install.set_defaults(func=install_deps)
	parser_install.add_argument(
		'app_path',
		type=str,
		nargs='?',
		help='Path of the app to discover its dependencies. [default .]',
		default='.',
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
		help='Path of the app to discover its dependencies. [default .]',
		default='.',
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
		help='Path of the app to discover its dependencies. [default .]',
		default='.',
	)
	parser_test.add_argument('--env', help='Choose specific env')
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
		'--use-env',
		help='Run tests on selected env rather than sandbox env',
		action='store_true',
	)
	parser_test.add_argument(
		'--breakpoint',
		help='Create debugger breakpoint upon failure of test',
		action='store_true',
	)
	parser_test.add_argument('--debug', help='Enable debug mode', action='store_true')

	parser_ref = subparsers.add_parser(
		'generate_ref', help='Generate LIMP app reference'
	)
	parser_ref.set_defaults(func=generate_ref)
	parser_ref.add_argument(
		'app_path',
		type=str,
		nargs='?',
		help='Path of the app to discover its dependencies. [default .]',
		default='.',
	)
	parser_ref.add_argument('--debug', help='Enable debug mode', action='store_true')

	args = parser.parse_args()
	if args.command:
		args.func(args)
	else:
		parser.print_help()


def create(args: argparse.Namespace):
	global os, subprocess

	if args.app_name == 'limp_app':
		logger.error(
			'Value for \'app_name\' CLI Arg is invalid. Name can\'t be \'limp_app\''
		)
		exit(1)
	elif not re.match(r'^[a-z_]+$', args.app_name):
		logger.error(
			'Value for \'app_name\' CLI Arg is invalid. Name should have only small letters and underscores.'
		)
		exit(1)
	
	app_config = {
		# [REF]: https://stackoverflow.com/a/47073723/2393762
		'admin_password': ['__ADMIN_PASSWORD__', ''.join([random.choice(string.ascii_letters + string.digits + string.punctuation ) for n in range(18)]).replace('\'', '^')],
		'anon_token_suffix': ['__ANON_TOKEN_SUFFIX__', ''.join([random.choice(string.digits) for n in range(24)])]
	}

	envs_defaults = {
		'dev_local': 'mongodb://localhost',
		'dev_server': 'mongodb://admin:admin@mongodb',
		'prod': 'mongodb://admin:admin@prod',
	}

	if not args.default_config:
		# [DOC] Allow user to specify custom config per the following Config Attrs
		logger.info('Not detected \'default-config\' CLI Arg. Attempting to create LIMP app with custom Config.')
		logger.info('If you would like to have app created with default config, stop the process, and re-run LIMP CLI with \'default-config\' CLI Arg.')
		# [DOC] envs: data_server
		logger.info('\'envs\' Config Attr provides environment-specific configuration. You will be required to specify \'data_server\' for each of the default available LIMP environments, namely \'dev_local\', \'dev_server\', and \'prod\'.')
		for env in envs_defaults.keys():
			while True:
				config_attr_val = input(f'\n> What would be the value for \'data_server\' Config Attr for environment \'{env}\'; The connection string to connect to your MongoDB host? [{envs_defaults[env]}]\n- ')
				if not config_attr_val:
					logger.info(f'Setting \'data_server\' Config Attr for environment \'{env}\' to default \'{envs_defaults[env]}\'.')
					app_config[f'{env}:data_server'] = [f'__{env.upper()}_DATA_SERVER__', (config_attr_val := envs_defaults[env])]
				else:
					logger.info(f'Setting \'data_server\' Config Attr for environment \'{env}\' to: \'{config_attr_val}\'.')
					app_config[f'{env}:data_server'] = [f'__{env.upper()}_DATA_SERVER__', config_attr_val]
				break
		# [DOC] env
		while True:
			config_attr_val = input('\n> What would be the value for \'env\'; Config Attr for default environnement to be used when invoking LIMP CLI \'launch\' command? [$__env.ENV]\n- ')
			if not config_attr_val:
				logger.info('Setting \'env\' Config Attr to default: \'$__env.ENV\'.')
				app_config['data_name'] = ['limp_data', (config_attr_val := '$__env.ENV')]
				break
			elif config_attr_val not in list(envs_defaults.keys()) and not re.match(r'^\$__env\.[A-Za-z_]+$', config_attr_val):
				logger.error('\'env\' Config Attr can only be one of the environments names defined in \'envs\' Config Attr, or a valid Env Variable.')
			else:
				logger.info(f'Setting \'env\' Config Attr to: \'{config_attr_val}\'.')
				app_config['env'] = ['__ENV__', config_attr_val]
				break
		# [DOC] data_name
		while True:
			config_attr_val = input('\n> What would be the value for \'data_name\'; Config Attr for database name to be created on \'data_server\'? [limp_data]\n- ')
			if not config_attr_val:
				logger.info('Setting \'data_name\' Config Attr to default: \'limp_data\'.')
				app_config['data_name'] = ['__DATA_NAME__', (config_attr_val := 'limp_data')]
				break
			elif not re.match(r'^[a-zA-Z0-9\-_]+$', config_attr_val):
				logger.error('\'data_name\' Config Attr can\'t have special characters other than underscores and hyphens in it.')
			else:
				logger.info(f'Setting \'data_name\' Config Attr to: \'{config_attr_val}\'.')
				app_config['data_name'] = ['__DATA_NAME__', config_attr_val]
				break
		# [DOC] locales
		while True:
			config_attr_val = input('\n> What would be the comma-separated, language_COUNTRY-formatted value for \'locales\'; Config Attr for localisations of your app? [ar_AE, en_AE]\n- ')
			if not config_attr_val:
				logger.info('Setting \'locales\' Config Attr to default: \'ar_AE, en_AE\'.')
				locales = ['ar_AE', 'en_AE']
				app_config['locales'] = ['__LOCALES__', (config_attr_val := 'ar_AE\', \'en_AE')]
				break
			else:
				try:
					locales = [re.match(r'^([a-z]{2}_[A-Z]{2})$', locale.strip()).group(0) for locale in config_attr_val.split(',')]
					logger.info(f'Setting \'locales\' Config Attr to: \'{config_attr_val}\'.')
					app_config['locales'] = ['__LOCALES__', '\', \''.join(locales)]
					break
				except:
					logger.error('An exception occurred while attempting to process value provided.')
					logger.error('\'locales\' Config Attr value should be provided as comma-separated, language_COUNTRY-formatted list of localisations.')
		# [DOC] locale
		while True:
			config_attr_val = input('\n> What would be the value for \'locale\'; Config Attr for default localisation of your app? [first value of \'locales\' Config Attr]\n- ')
			if not config_attr_val:
				logger.info(f'Setting \'locale\' Config Attr to first value of \'locales\' Config Attr: \'{locales[0]}\'.')
				app_config['locale'] = ['__LOCALE__', (config_attr_val := locales[0])]
				break
			elif config_attr_val not in locales:
				logger.error('\'locale\' Config Attr can only be one of the localisations defined in \'locales\' Config Attr.')
			else:
				logger.info(f'Setting \'locale\' Config Attr to: \'{config_attr_val}\'.')
				app_config['locale'] = ['__LOCALE__', config_attr_val]
				break
		# [DOC] admin_doc: email
		while True:
			config_attr_val = input('\n> What would be the value for \'admin_doc\'.\'email\'; Config Attr? [admin@app.limp.localhost]\n- ')
			if not config_attr_val:
				logger.info('Setting \'admin_doc\'.\'email\' Config Attr to default: \'admin@app.limp.localhost\'.')
				app_config['admin_doc:email'] = ['__ADMIN_DOC_EMAIL__', (config_attr_val := 'admin@app.limp.localhost')]
				break
			elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', config_attr_val):
				logger.error('\'admin_doc\'.\'email\' Config Attr value is not a valid email address.')
			else:
				logger.info(f'Setting \'admin_doc\'.\'email\' Config Attr to: \'{config_attr_val}\'.')
				app_config['admin_doc:email'] = ['__ADMIN_DOC_EMAIL__', config_attr_val]
				break
	else:
		for env in envs_defaults.keys():
			app_config[f'{env}:data_server'] = [f'__{env.upper()}_DATA_SERVER__', envs_defaults[env]]
		app_config.update({
			'env': ['__ENV__', '$__env.ENV'],
			'data_name': ['__DATA_NAME__', 'limp_data'],
			'locales': ['__LOCALES__', '\', \''.join(['ar_AE', 'en_AE'])],
			'locale': ['__LOCALE__', 'ar_AE'],
			'admin_doc:email': ['__ADMIN_DOC_EMAIL__', 'admin@app.limp.localhost'],
		})
	
	logger.info('This will create an app with the following config:')
	for config_attr, config_set in app_config.items():
		logger.info(f'- {config_attr}: \'{config_set[1]}\'')

	api_level = '.'.join(__version__.split('.')[:2])
	template_url = 'https://github.com/masaar/limp_app_template/archive/APIv0.0.tar.gz'
	template_url = template_url.replace('0.0', api_level)
	logger.info(f'Attempting to download LIMP app template from: {template_url}')

	# [REF] https://stackoverflow.com/a/7244263/2393762
	file_name, _ = urllib.request.urlretrieve(template_url)
	logger.info('File downloaded successfully!')

	def template_members(*, archive):
		l = len(f'limp_app_template-APIv{api_level}/')
		for member in archive.getmembers():
			if member.path.startswith(f'limp_app_template-APIv{api_level}'):
				member.path = member.path[l:]
				yield member

	app_path = os.path.realpath(os.path.join(args.app_path, args.app_name))
	logger.info(f'Attempting to extract template archive to: {app_path}')
	# [REF]: https://stackoverflow.com/a/43094365/2393762
	with tarfile.open(name=file_name, mode='r:gz') as archive:
		archive.extract
		archive.extractall(
			path=app_path, members=template_members(archive=archive),
		)
	logger.info('Archive extracted successfully!')

	logger.info('Attempting to initialise empty Git repo for new LIMP app.')
	init_call = subprocess.call(
		['git', 'init'],
		cwd=os.path.realpath(os.path.join(args.app_path, args.app_name)),
	)
	if init_call != 0:
		logger.error(
			'Git init call failed. Check console for details, then create Git repo yourself.'
		)
	logger.info('Git repo initialised successfully!')

	logger.info('Attempting to config app template for new LIMP app.')
	with open(
		os.path.realpath(os.path.join(args.app_path, args.app_name, 'limp_app.py')), 'r'
	) as f:
		limp_app_file = f.read()
	with open(
		os.path.realpath(os.path.join(args.app_path, args.app_name, 'limp_app.py')), 'w'
	) as f:
		limp_app_file = limp_app_file.replace('__PROJECT_NAME__', args.app_name, 1)
		for config_set in app_config.values():
			limp_app_file = limp_app_file.replace(config_set[0], config_set[1], 1)
		f.write(limp_app_file)

	with open(
		os.path.realpath(os.path.join(args.app_path, args.app_name, '.gitignore')), 'r'
	) as f:
		gitignore_file = f.read()
	with open(
		os.path.realpath(os.path.join(args.app_path, args.app_name, '.gitignore')), 'w'
	) as f:
		f.write(gitignore_file.replace('PROJECT_NAME', args.app_name, 1))

	os.rename(
		os.path.realpath(
			os.path.join(args.app_path, args.app_name, 'packages', 'PROJECT_NAME')
		),
		os.path.realpath(
			os.path.join(args.app_path, args.app_name, 'packages', args.app_name)
		),
	)

	logger.info(f'Congrats! Your LIMP app {args.app_name} is successfully created!')


def install_deps(args: argparse.Namespace):
	global sys, os, subprocess
	# [DOC] Change logging level to debug
	logger.setLevel(logging.DEBUG)
	logger.debug('Beginning to install dependencies')
	# [DOC] Create standard call command list
	pip_command = [sys.executable, '-m', 'pip', 'install']
	# [DOC] Check for install_user flag to install dependencies with --user option
	if args.install_user:
		logger.debug('Detected install_user flag')
		pip_command.append('--user')
	# [DOC] Add -r option to use requirements.txt files.
	pip_command.append('-r')

	dirs = [
		d
		for d in os.listdir(os.path.join(args.app_path, 'packages'))
		if os.path.isdir(os.path.join(args.app_path, 'packages', d))
	]
	# [DOC] Iterate over packages to find requirements.txt files
	for package in dirs:
		logger.debug(f'Checking package \'{package}\' for \'requirements.txt\' file.')
		if os.path.exists(
			os.path.join(args.app_path, 'packages', package, 'requirements.txt')
		):
			logger.debug(
				'File \'requirements.txt\' found! Attempting to install package dependencies.'
			)
			pip_call = subprocess.call(
				pip_command
				+ [os.path.join(args.app_path, 'packages', package, 'requirements.txt')]
			)
			if pip_call != 0:
				logger.error(
					'Last \'pip\' call failed. Check console for more details. Exiting.'
				)
				exit(1)


def launch(
	args: argparse.Namespace,
	custom_launch: Literal['test', 'generate_ref', 'generate_models'] = None,
):
	global os, asyncio
	global handler

	# [DOC] Update Config with LIMP CLI args
	from limp.config import Config, process_config

	Config._limp_version = __version__
	if custom_launch != 'generate_ref':
		Config.env = args.env
	if not custom_launch:
		Config.test_collections = args.test_collections
		Config.force_admin_check = args.force_admin_check

	# [DOC] Check for port CLI Arg
	if not custom_launch and args.port:
		try:
			Config.port = int(args.port)
		except:
			logger.error(f'Port should be in integer format. Exiting.')
			exit()
	else:
		Config.port = 8081
	# [DOC] Check for debug CLI Arg
	if args.debug:
		Config.debug = True
		logger.setLevel(logging.DEBUG)
	# [DOC] Check for log CLI Arg
	if not custom_launch and args.log:
		logger.removeHandler(handler)
		if not os.path.exists(os.path.join(args.app_path, 'logs')):
			os.makedirs(os.path.join(args.app_path, 'logs'))
		handler = logging.FileHandler(
			filename=os.path.join(
				args.app_path,
				'logs',
				f'{datetime.datetime.utcnow().strftime("%d-%b-%Y")}.log',
			)
		)
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		logger.setLevel(logging.DEBUG)

	from limp.app import run_app

	try:
		try:
			sys.path.append(args.app_path)
			limp_app = __import__('limp_app')
			app_config = limp_app.config
		except ModuleNotFoundError:
			logger.error(
				f'No \'limp_app.py\' file found in specified path: \'{args.app_path}\'. Exiting.'
			)
			exit()
		except AttributeError:
			logger.error(
				f'File \'limp_app.py\' was found but it doesn\'t have \'config\' method. Exiting.'
			)
			exit()
		logger.info(
			f'Found app \'{app_config.name} (v{app_config.version})\'. Attempting to load App Config.'
		)
		Config._app_name = app_config.name
		Config._app_version = app_config.version
		Config._app_path = os.path.realpath(args.app_path)
		# [DOC] Read app_config and update Config accordingly
		# [DOC] Check envs, env
		if custom_launch not in ['generate_ref'] and app_config.envs:
			if not args.env and not app_config.env:
				logger.error(
					'App Config Attr \'envs\' found, but no \'env\' App Config Attr, or CLI Attr were defined.'
				)
				exit()
			if args.env:
				if args.env in app_config.envs.keys():
					logger.info(
						f'Setting \'env\' Config Attr to \'env\' CLI Arg value \'{args.env}\''
					)
				else:
					logger.error(
						f'Found value \'{args.env}\' for \'env\' CLI Arg, but not defined in \'envs\' App Config Attr. Exiting.'
					)
					exit()
			else:
				if app_config.env in app_config.envs.keys():
					logger.info(
						f'Setting \'env\' Config Attr to \'env\' App Config Attr value \'{app_config.env}\''
					)
					Config.env = app_config.env
				elif app_config.env.startswith('$__env.'):
					logger.info(
						'Found Env Variable for \'env\' App Config Attr. Attempting to process it.'
					)
					env_env_var = app_config.env.replace('$__env.', '')
					env = os.getenv(env_env_var)
					if env:
						logger.info(
							f'Setting \'env\' Config Attr to Env Variable \'{env_env_var}\' value \'{env}\'.'
						)
						Config.env = env
					else:
						logger.error(
							f'No value found for Env Variable \'{env_env_var}\'. Exiting.'
						)
						exit()
				else:
					logger.error(
						f'Found value \'{args.env}\' for \'env\' CLI Arg, but not defined in \'envs\' App Config Attr. Exiting.'
					)
					exit()
			logger.info(
				f'Beginning to extract Config Attrs defined in selected \'env\', \'{Config.env}\', to App Config Attrs.'
			)
			for config_attr in dir(app_config.envs[Config.env]):
				if (
					config_attr.startswith('__')
					or getattr(app_config.envs[Config.env], config_attr) == None
				):
					continue
				logger.info(
					f'Extracting \'{config_attr}\' Config Attr to App Config Attr'
				)
				setattr(
					app_config,
					config_attr,
					getattr(app_config.envs[Config.env], config_attr),
				)
				setattr(
					Config,
					config_attr,
					getattr(app_config.envs[Config.env], config_attr),
				)
		# [DOC] Check port Config Attr
		if not custom_launch and app_config.port:
			if args.port:
				logger.info(
					f'Ignoring \'port\' App Config Attr in favour of \'port\' CLI Arg with value \'{args.port}\'.'
				)
			else:
				logger.info('Found \'port\' App Config Attr. Attempting to process it.')
				if type(app_config.port) == int:
					Config.port = app_config.port
					logger.info(f'Setting \'port\' Config Attr to \'{Config.port}\'.')
				elif type(app_config.port) == str and app_config.port.startswith(
					'$__env.'
				):
					logger.info(
						'Found Env Variable for \'port\' App Config Attr. Attempting to process it.'
					)
					port_env_var = app_config.port.replace('$__env.', '')
					port = os.getenv(port_env_var)
					if port:
						logger.info(
							f'Setting \'port\' Config Attr to Env Variable \'{port_env_var}\' value \'{port}\'.'
						)
						Config.port = port
					else:
						logger.error(
							f'No value found for Env Variable \'{port_env_var}\'. Exiting.'
						)
						exit()
				else:
					logger.error(
						f'Invalid value type for \'port\' Config Attr with value \'{app_config.port}\'. Exiting.'
					)
					exit()
		# [DOC] Check debug Config Attr
		if app_config.debug:
			if args.debug:
				logger.info(
					f'Ignoring \'debug\' App Config Attr in favour of \'debug\' CLI Arg with value \'{args.debug}\'.'
				)
			else:
				logger.info(
					'Found \'debug\' App Config Attr. Attempting to process it.'
				)
				if type(app_config.debug) == bool:
					Config.debug = app_config.debug
					logger.info(f'Setting \'debug\' Config Attr to \'{Config.debug}\'.')
				elif type(app_config.debug) == str and app_config.debug.startswith(
					'$__env.'
				):
					logger.info(
						'Found Env Variable for \'debug\' App Config Attr. Attempting to process it.'
					)
					debug_env_var = app_config.debug.replace('$__env.', '')
					debug = os.getenv(debug_env_var)
					if debug:
						logger.info(
							f'Setting \'debug\' Config Attr to Env Variable \'{debug_env_var}\' as \'True\'.'
						)
						Config.debug = True
					else:
						logger.info(
							f'No value found for Env Variable \'{debug_env_var}\'. Setting \'debug\' to \'False\'.'
						)
						Config.debug = False
				else:
					logger.error(
						f'Invalid value type for \'debug\' Config Attr with value \'{app_config.debug}\'. Exiting.'
					)
					exit()
				if Config.debug:
					logger.setLevel(logging.DEBUG)
		# [DOC] Check force_admin_check Config Attr
		if not custom_launch and app_config.force_admin_check:
			if args.force_admin_check:
				logger.info(
					f'Ignoring \'force_admin_check\' App Config Attr in favour of \'force_admin_check\' CLI Arg with value \'{args.force_admin_check}\'.'
				)
				Config.force_admin_check = True
			else:
				logger.info(
					'Found \'force_admin_check\' App Config Attr. Attempting to process it.'
				)
				if type(app_config.force_admin_check) == bool:
					Config.force_admin_check = app_config.force_admin_check
					logger.info(
						f'Setting \'force_admin_check\' Config Attr to \'{Config.force_admin_check}\'.'
					)
				elif type(
					app_config.force_admin_check
				) == str and app_config.force_admin_check.startswith('$__env.'):
					logger.info(
						'Found Env Variable for \'force_admin_check\' App Config Attr. Attempting to process it.'
					)
					check_env_var = app_config.force_admin_check.replace('$__env.', '')
					check = os.getenv(check_env_var)
					if check:
						logger.info(
							f'Setting \'force_admin_check\' Config Attr to Env Variable \'{check_env_var}\' as \'True\'.'
						)
						Config.force_admin_check = True
					else:
						logger.info(
							f'No value found for Env Variable \'{check_env_var}\'. Setting \'force_admin_check\' to \'False\'.'
						)
						Config.force_admin_check = False
				else:
					logger.error(
						f'Invalid value type for \'force_admin_check\' Config Attr with value \'{app_config.force_admin_check}\'. Exiting.'
					)
					exit()
		# [TODO] Implement realm APP Config Attr checks
		# [DOC] Process other app config attrs as PACKAGE_CONFIG
		process_config(config=app_config)
	except Exception:
		logger.error(
			'An unexpected exception happened while attempting to process LIMP app. Exception details:'
		)
		logger.error(traceback.format_exc())
		logger.error('Exiting.')
		exit()

	asyncio.run(run_app())


def test(args: argparse.Namespace):
	# [DOC] Update Config with LIMP CLI args
	from limp.config import Config

	Config.test = args.test_name
	Config.test_skip_flush = args.skip_flush
	Config.test_force = args.force
	Config.test_env = args.use_env
	Config.test_breakpoint = args.breakpoint
	launch(args=args, custom_launch='test')


def generate_ref(args: argparse.Namespace):
	# [DOC] Update Config with LIMP CLI args
	from limp.config import Config

	Config.generate_ref = True
	launch(args=args, custom_launch='generate_ref')

