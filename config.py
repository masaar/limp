from enums import Event
from test import Test
from base_model import BaseModel
from utils import LIMP_ATTRS, DictObj

from typing import List, Dict, Callable, Any, Union, Set, Tuple

from croniter import croniter
from pymongo import database
from bson import ObjectId

import os, jwt, logging, datetime, time, requests

logger = logging.getLogger('limp')


class Config:
	debug: bool = False
	env: str = None
	
	_sys_conn: database
	_sys_env: Dict[str, Any]
	_sys_docs: Dict[str, Dict[str, str]] = {}
	_realms: Dict[str, 'BaseModel'] = {}
	_jobs_session: 'BaseModel'
	_jobs_base: datetime

	_limp_version: str = None
	version: float = None

	test: str = False
	test_flush: bool = False
	test_force: bool = False
	test_env: bool = False
	test_breakpoint: bool = False
	test_collections: bool = False
	tests: Dict[str, List[Dict[str, Any]]] = {}

	emulate_test: bool = False

	realm: bool = False

	vars: Dict[str, Any] = {}

	conn_timeout: int = 120
	quota_anon_min: int = 40
	quota_auth_min: int = 100
	quota_ip_min: int = 500

	data_server: str = 'mongodb://localhost'
	data_name: str = 'limp_data'
	data_ssl: bool = False
	data_ca_name: str = None
	data_ca: str = None

	data_azure_mongo: bool = False

	email_auth: Dict[str, str] = {}

	locales: List[str] = ['ar_AE', 'en_AE']
	locale: str = 'ar_AE'

	admin_doc: Dict[str, Any] = {}
	admin_password: str = '__ADMIN'

	anon_token: str = '__ANON_TOKEN_f00000000000000000000012'
	anon_privileges: Dict[str, List[str]] = {}

	user_attrs: LIMP_ATTRS = {}
	user_auth_attrs: List[str] = []
	user_attrs_defaults: Dict[str, Any] = {}

	groups: List[Dict[str, Any]] = []
	default_privileges: Dict[str, List[str]] = {}

	data_indexes: List[Dict[str, Any]] = []

	docs: List[Dict[str, Any]] = []

	l10n: Dict[str, Dict[str, Any]] = {}

	jobs: List[Dict[str, Any]] = []

	gateways: Dict[str, Callable] = {}

	types: Dict[str, Callable] = {}

	@classmethod
	async def config_data(cls, modules: Dict[str, 'BaseModule']) -> None:
		# [DOC] Check API version
		if not cls.version:
			logger.warning('No version sepecified for the app. LIMPd would continue to run the app, but the developer should consider adding version to eliminate specs mismatch.')
		else:
			limp_version = float('.'.join(cls._limp_version.split('.')[0:2]))
			if limp_version != cls.version:
				logger.error('LIMPd is on version \'%s\', but the app requires version \'%s\'. Exiting.', cls._limp_version, cls.version)
				exit()
			try:
				version_detected = False
				versions = (requests.get('https://raw.githubusercontent.com/masaar/limp-versions/master/versions.txt').content).decode('utf-8').split('\n')
				for version in versions:
					if float('.'.join(version.split('.')[0:2])) == limp_version:
						version_detected = version
					elif float('.'.join(version.split('.')[0:2])) > 5.4:
						break
					else:
						if version_detected != False:
							if '5.4.9' != version_detected:
								break
				if version_detected and version_detected != cls._limp_version:
					logger.warning('Your app is using LIMPs version \'%s\' while newer version \'%s\' of the same API is available. Please, update.', cls._limp_version, version_detected)
			except:
				logger.warning('An error occured while attempting to check for latest update to LIMPs. Please, check for updates on your own.')
		
		# [DOC] Check for jobs
		if cls.jobs:
			# [DOC] Create _jobs_env
			cls._jobs_session = DictObj({**Config.compile_anon_session(), 'user':DictObj(Config.compile_anon_user())})
			# [DOC] Check jobs schedule validity
			cls._jobs_base = datetime.datetime.utcnow()
			for job in cls.jobs:
				if not croniter.is_valid(job['schedule']):
					logger.error('Job with schedule \'%s\' is invalid. Exiting.', job['schedule'])
					exit()
				else:
					job['schedule'] = croniter(job['schedule'], cls._jobs_base)
					job['next_time'] = datetime.datetime.fromtimestamp(job['schedule'].get_next(), datetime.timezone.utc).isoformat()[:16]
			

		# [DOC] Check for presence of user_auth_attrs
		if len(cls.user_auth_attrs) < 1 or \
			sum([1 for attr in cls.user_auth_attrs if attr in cls.user_attrs.keys()]) != len(cls.user_auth_attrs):
			logger.error('Either no \'user_auth_attrs\' are provided, or one of \'user_auth_attrs\' not present in \'user_attrs\'. Exiting.')
			exit()


		# [DOC] Check default values
		security_warning = '[SECURITY WARNING] %s is not explicitly set. It has been defaulted to \'%s\' but in production environment you should consider setting it to your own to protect your app from breaches.'
		if cls.admin_password == '__ADMIN':
			logger.warning(security_warning, 'Admin password', '__ADMIN')
		if cls.anon_token == '__ANON_TOKEN_f00000000000000000000012':
			logger.warning(security_warning, 'Anon token', '__ANON_TOKEN_f00000000000000000000012')

		# [DOC] Check for env data variables
		data_attrs = {'server':'mongodb://localhost', 'name':'limp_data', 'ssl':False, 'ca_name':False, 'ca':False}
		for data_attr_name in data_attrs.keys():
			data_attr = getattr(cls, 'data_{}'.format(data_attr_name))
			if type(data_attr) == str and data_attr.startswith('$__env.'):
				logger.debug('Detected env variable for config attr \'data_%s\'', data_attr_name)
				if not os.getenv(data_attr[7:]):
					logger.warning('Couldn\'t read env variable for config attr \'data_%s\'. Defaulting to \'%s\'', data_attr_name, data_attrs[data_attr_name])
					setattr(cls, 'data_{}'.format(data_attr_name), data_attrs[data_attr_name])
				else:
					# [DOC] Set data_ssl to True rather than string env variable value
					if data_attr_name == 'ssl':
						data_attr = True
					else:
						data_attr = os.getenv(data_attr[7:])
					logger.warning('Setting env variable for config attr \'data_%s\' to \'%s\'', data_attr_name, data_attr)
					setattr(cls, 'data_{}'.format(data_attr_name), data_attr)


		# [DOC] Check SSL settings
		if cls.data_ca:
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			if not os.path.exists(os.path.join(__location__, 'certs')):
				os.makedirs(os.path.join(__location__, 'certs'))
			with open(os.path.join(__location__, 'certs', cls.data_ca_name), 'w') as f:
				f.write(cls.data_ca)
		
		from data import Data

		# [DOC] Create default env dict
		anon_user = cls.compile_anon_user()
		anon_session = cls.compile_anon_session()
		anon_session['user'] = DictObj(anon_user)
		cls._sys_conn = Data.create_conn()
		cls._sys_env = {
			'conn':cls._sys_conn,
			'REMOTE_ADDR':'127.0.0.1',
			'HTTP_USER_AGENT':'LIMPd',
			'session':DictObj(anon_session),
			'ws':None,
			'watch_tasks':{}
		}

		if cls.data_azure_mongo:
			for module in modules:
				try:
					if modules[module].collection:
						logger.debug('Attempting to create shard collection: %s.', modules[module].collection)
						cls._sys_conn[cls.data_name].command('shardCollection', '{}.{}'.format(Config.data_name, modules[module].collection), key={'_id':'hashed'})
					else:
						logger.debug('Skipping service module: %s.', module)
				except Exception as err:
					logger.error(err)

		# [DOC] Check test mode
		if cls.test or cls.test_collections:
			logger.debug('Test mode or Test Collections Mode detected.')
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			if not os.path.exists(os.path.join(__location__, 'tests')):
				os.makedirs(os.path.join(__location__, 'tests'))
			if not cls.test_env:
				for module in modules.keys():
					if modules[module].collection:
						logger.debug('Updating collection name \'%s\' of module %s', modules[module].collection, module)
						modules[module].collection = 'test_{}'.format(modules[module].collection)
						if cls.test_flush:
							logger.debug('Flushing test collection \'%s\'', modules[module].collection)
							await Data.drop(env=cls._sys_env, collection=modules[module].collection)
					else:
						logger.debug('Skipping service module %s', module)
			else:
				logger.warning('Testing on \'%s\' env. LIMPd would be sleeping for 5secs to give you chance to abort test workflow if this was a mistake.', cls.env)
				time.sleep(5)
				
		logger.debug('Testing realm mode.')
		if Config.realm:
			# [DOC] Append realm to env dict
			cls._sys_env['realm'] = '__global'
			# [DOC] Append realm attrs to all modules attrs and set at as required in query_args and doc_args
			for module in modules.keys():
				if module != 'realm':
					logger.debug('Updating module \'%s\' for realm mode.', module)
					modules[module].attrs['realm'] = 'str'
					for method in modules[module].methods.keys():
						# [DOC] Attempt required changes to query_args to add realm query_arg
						if not modules[module].methods[method].query_args:
							modules[module].methods[method].query_args = [{}]
						elif type(modules[module].methods[method].query_args) == dict:
							modules[module].methods[method].query_args = [modules[module].methods[method].query_args]
						for query_args_set in modules[module].methods[method].query_args:
							query_args_set['realm'] = 'str'
						# [DOC] Attempt required changes to doc_args to add realm doc_arg
						if not modules[module].methods[method].doc_args:
							modules[module].methods[method].doc_args = [{}]
						elif type(modules[module].methods[method].doc_args) == dict:
							modules[module].methods[method].doc_args = [modules[module].methods[method].doc_args]
						for doc_args_set in modules[module].methods[method].doc_args:
							doc_args_set['realm'] = 'str'
			# [DOC] Query all realms to provide access to available realms and to add realm docs to _sys_docs
			realm_results = await modules['realm'].read(skip_events=[Event.__PERM__, Event.__ARGS__], env=cls._sys_env)
			logger.debug('Found %s realms. Namely; %s', realm_results.args.count, ', '.join([doc.name for doc in realm_results.args.docs]))
			for doc in realm_results.args.docs:
				cls._realms[doc.name] = doc
				cls._sys_docs[doc._id] = {'module':'realm'}
			# [DOC] Create __global realm
			if '__global' not in cls._realms:
				logger.debug('GLOBAL realm not found, creating it.')
				realm_results = await modules['realm'].create(skip_events=[Event.__PERM__, Event.__PRE__], env=cls._sys_env, doc={
					'_id':ObjectId('f00000000000000000000014'),
					'user':ObjectId('f00000000000000000000010'),
					'name':'__global',
					'default':'f00000000000000000000013'
				})
				logger.debug('GLOBAL realm creation results: %s', realm_results)
				if realm_results.status != 200:
					logger.error('Config step failed. Exiting.')
					exit()

		# [DOC] Checking users collection
		logger.debug('Testing users collection.')
		user_results = await modules['user'].read(skip_events=[Event.__PERM__, Event.__ON__], env=cls._sys_env, query=[{'_id':'f00000000000000000000010'}])
		if not user_results.args.count:
			logger.debug('ADMIN user not found, creating it.')
			# [DOC] Prepare base ADMIN user doc
			admin_doc = {
				'_id': ObjectId('f00000000000000000000010'),
				'name': {
					cls.locale: '__ADMIN'
				},
				'groups': [],
				'privileges': {'*': '*'},
				'locale': cls.locale,
				'attrs':{}
			}
			# [DOC] Update ADMIN user doc with admin_doc Config Attr
			admin_doc.update(cls.admin_doc)

			for auth_attr in cls.user_auth_attrs:
				admin_doc[f'{auth_attr}_hash'] = jwt.encode({'hash':[auth_attr, admin_doc[auth_attr], cls.admin_password, cls.anon_token]}, cls.admin_password).decode('utf-8').split('.')[1]
			if Config.realm:
				admin_doc['realm'] = '__global'
			admin_results = await modules['user'].create(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=cls._sys_env, doc=admin_doc)
			logger.debug('ADMIN user creation results: %s', admin_results)
			if admin_results.status != 200:
				logger.error('Config step failed. Exiting.')
				exit()
		cls._sys_docs[ObjectId('f00000000000000000000010')] = {
			'module':'user'
		}

		# [DOC] Test if ANON user exists
		user_results = await modules['user'].read(skip_events=[Event.__PERM__, Event.__ON__], env=cls._sys_env, query=[{'_id':'f00000000000000000000011'}])
		if not user_results.args.count:
			logger.debug('ANON user not found, creating it.')
			anon_results = await modules['user'].create(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=cls._sys_env, doc=cls.compile_anon_user())
			logger.debug('ANON user creation results: %s', anon_results)
			if anon_results.status != 200:
				logger.error('Config step failed. Exiting.')
				exit()
		cls._sys_docs[ObjectId('f00000000000000000000011')] = {
			'module':'user'
		}

		logger.debug('Testing sessions collection.')
		# [DOC] Test if ANON session exists
		session_results = await modules['session'].read(skip_events=[Event.__PERM__, Event.__ON__], env=cls._sys_env, query=[{'_id':'f00000000000000000000012'}])
		if not session_results.args.count:
			logger.debug('ANON session not found, creating it.')
			anon_results = await modules['session'].create(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=cls._sys_env, doc=cls.compile_anon_session())
			logger.debug('ANON session creation results: %s', anon_results)
			if anon_results.status != 200:
				logger.error('Config step failed. Exiting.')
				exit()
		cls._sys_docs[ObjectId('f00000000000000000000012')] = {
			'module':'session'
		}

		logger.debug('Testing groups collection.')
		# [DOC] Test if DEFAULT group exists
		group_results = await modules['group'].read(skip_events=[Event.__PERM__, Event.__ON__], env=cls._sys_env, query=[{'_id':'f00000000000000000000013'}])
		if not group_results.args.count:
			logger.debug('DEFAULT group not found, creating it.')
			group_doc = {
				'_id': ObjectId('f00000000000000000000013'),
				'user': ObjectId('f00000000000000000000010'),
				'name': {
					locale: '__DEFAULT' for locale in cls.locales
				},
				'bio': {
					locale: '__DEFAULT' for locale in cls.locales
				},
				'privileges': cls.default_privileges,
				'attrs':{}
			}
			if cls.realm:
				group_doc['realm'] = '__global'
			group_results = await modules['group'].create(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=cls._sys_env, doc=group_doc)
			logger.debug('DEFAULT group creation results: %s', group_results)
			if group_results.status != 200:
				logger.error('Config step failed. Exiting.')
				exit()
		cls._sys_docs[ObjectId('f00000000000000000000013')] = {
			'module':'group'
		}
		
		# [DOC] Test app-specific groups
		logger.debug('Testing app-specific groups collection.')
		for group in cls.groups:
			group_results = await modules['group'].read(skip_events=[Event.__PERM__, Event.__ON__], env=cls._sys_env, query=[{'_id':group['_id']}])
			if not group_results.args.count:
				logger.debug('App-specific group with name %s not found, creating it.', group['name'])
				if cls.realm:
					group['realm'] = '__global'
				group_results = await modules['group'].create(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=cls._sys_env, doc=group)
				logger.debug('App-specific group with name %s creation results: %s', group['name'], group_results)
				if group_results.status != 200:
					logger.error('Config step failed. Exiting.')
					exit()
			cls._sys_docs[ObjectId(group['_id'])] = {
				'module':'group'
			}
		
		# [DOC] Test app-specific data indexes
		logger.debug('Testing data indexes')
		for index in cls.data_indexes:
			logger.debug('Attempting to create data index: %s', index)
			cls._sys_conn[cls.data_name][index['collection']].create_index(index['index'])
		logger.debug('Creating \'__deleted\' data indexes for all collections.')
		for module in modules:
			if modules[module].collection:
				logger.debug('Attempting to create \'__deleted\' data index for collection: %s', modules[module].collection)
				cls._sys_conn[cls.data_name][modules[module].collection].create_index([('__deleted', 1)])
		if cls.realm:
			logger.debug('Creating \'realm\' data indexes for all collections.')
			for module in modules:
				if module != 'realm' and modules[module].collection:
					logger.debug('Attempting to create \'realm\' data index for collection: %s', modules[module].collection)
					cls._sys_conn[cls.data_name][modules[module].collection].create_index([('realm', 'text')])

		# [DOC] Test app-specific docs
		logger.debug('Testing docs.')
		for doc in cls.docs:
			doc_results = await modules[doc['module']].read(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=cls._sys_env, query=[{'_id':doc['doc']['_id']}])
			if not doc_results.args.count:
				if cls.realm:
					doc['doc']['realm'] = '__global'
				skip_events = [Event.__PERM__]
				if 'skip_args' in doc.keys() and doc['skip_args'] == True:
					skip_events.append(Event.__ARGS__)
				doc_results = await modules[doc['module']].create(skip_events=skip_events, env=cls._sys_env, doc=doc['doc'])
				logger.debug('App-specific doc with _id \'%s\' of module \'%s\' creation results: %s', doc['doc']['_id'], doc['module'], doc_results)
				if doc_results.status != 200:
					logger.error('Config step failed. Exiting.')
					exit()
			cls._sys_docs[ObjectId(doc['doc']['_id'])] = {
				'module':doc['module']
			}
		
		# [DOC] Check for test mode
		if cls.test:
			logger.debug('Running tests')
			anon_session = cls.compile_anon_session()
			anon_session['user'] = DictObj(cls.compile_anon_user())
			Test.session = DictObj(anon_session)
			await Test.run_test(test_name=cls.test, steps=False, modules=modules, env=cls._sys_env)
			exit()
		
		# [DOC] Check for emulate_test mode
		if cls.emulate_test:
			cls.test = True
	
	@classmethod
	def compile_anon_user(cls):
		anon_doc = {
			'_id': ObjectId('f00000000000000000000011'),
			'name': {
				cls.locale: '__ANON'
			},
			'groups': [],
			'privileges': cls.anon_privileges,
			'locale': cls.locale,
			'attrs':{}
		}
		for attr in cls.user_attrs.keys():
			anon_doc[attr] = Test.generate_attr(cls.user_attrs[attr])
		for auth_attr in cls.user_auth_attrs:
			anon_doc[f'{auth_attr}_hash'] = cls.anon_token
		if cls.realm:
			anon_doc['realm'] = '__global'
		return anon_doc

	@classmethod
	def compile_anon_session(cls):
		session_doc = {
			'_id': ObjectId('f00000000000000000000012'),
			'user': ObjectId('f00000000000000000000011'),
			'host_add': '127.0.0.1',
			'user_agent': cls.anon_token,
			'timestamp': '1970-01-01T00:00:00',
			'expiry': '1970-01-01T00:00:00',
			'token': cls.anon_token
		}
		if cls.realm:
			session_doc['realm'] = '__global'
		return session_doc