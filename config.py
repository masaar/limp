from event import Event
from test import Test

from typing import List, Dict, Callable, Any

from croniter import croniter
from pymongo import database
from bson import ObjectId

import os, jwt, logging, datetime, time

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

	_limp_version: float = None
	version: float = None

	test: str = False
	test_flush: bool = False
	test_force: bool = False
	test_env: bool = False
	test_breakpoint: bool = False
	tests: Dict[str, List[Dict[str, Any]]] = {}

	emulate_test: bool = False

	realm: bool = False

	data_driver: str = 'mongodb'
	data_server: str = 'mongodb://localhost'
	data_name: str = 'limp_data'
	data_ssl: bool = False
	data_ca_name: str = None
	data_ca: str = None

	data_azure_mongo: bool = False

	sms_auth: Dict[str, str] = {}

	email_auth: Dict[str, str] = {}

	locales: List[str] = ['ar_AE', 'en_AE']
	locale: str = 'ar_AE'

	admin_username: str = '__ADMIN'
	admin_email: str = 'ADMIN@LIMP.MASAAR.COM'
	admin_phone: str = '+971500000000'
	admin_password: str = '__ADMIN'

	anon_token: str = '__ANON_TOKEN_f00000000000000000000012'
	anon_privileges: Dict[str, List[str]] = {}

	groups: List[Dict[str, Any]] = []
	default_privileges: Dict[str, List[str]] = {}

	data_indexes: List[Dict[str, Any]] = []

	docs: List[Dict[str, Any]] = []

	l10n: Dict[str, Dict[str, Any]] = {}

	types: Dict[str, Callable] = {}

	jobs: List[Dict[str, Any]] = []

	@classmethod
	def config_data(self, modules):

		# [DOC] Check API version
		if not self.version:
			logger.warning('No version sepecified for the app. LIMPd would continue to run the app, but the developer should consider adding version to eliminate specs mismatch.')
		else:
			if self._limp_version != self.version:
				logger.error('LIMPd is on version \'%s\', but the app requires version \'%s\'. Exiting.', self._limp_version, self.version)
				exit()
		
		# [DOC] Check for jobs
		if self.jobs:
			from utils import DictObj
			# [DOC] Create _jobs_env
			self._jobs_session = DictObj({**Config.compile_anon_session(), 'user':DictObj(Config.compile_anon_user())})
			# [DOC] Check jobs schedule validity
			self._jobs_base = datetime.datetime.utcnow()
			for job in self.jobs:
				if not croniter.is_valid(job['schedule']):
					logger.error('Job with schedule \'%s\' is invalid. Exiting.', job['schedule'])
					exit()
				else:
					job['schedule'] = croniter(job['schedule'], self._jobs_base)
					job['next_time'] = datetime.datetime.fromtimestamp(job['schedule'].get_next(), datetime.timezone.utc).isoformat()[:16]
			

		# [DOC] Check default values
		security_warning = '[SECURITY WARNING] %s is not explicitly set. It has been defaulted to \'%s\' but in production environment you should consider setting it to your own to protect your app from breaches.'
		if self.admin_username == '__ADMIN':
			logger.warning(security_warning, 'Admin username', '__ADMIN')
		if self.admin_email == 'ADMIN@LIMP.MASAAR.COM':
			logger.warning(security_warning, 'Admin email', 'ADMIN@LIMP.MASAAR.COM')
		if self.admin_phone == '+971500000000':
			logger.warning(security_warning, 'Admin phone', '+971500000000')
		if self.admin_password == '__ADMIN':
			logger.warning(security_warning, 'Admin password', '__ADMIN')
		if self.anon_token == '__ANON_TOKEN_f00000000000000000000012':
			logger.warning(security_warning, 'Anon token', '__ANON_TOKEN_f00000000000000000000012')

		# [DOC] Check for env data variables
		data_attrs = {'server':'mongodb://localhost', 'name':'limp_data', 'ssl':False, 'ca_name':False, 'ca':False}
		for data_attr_name in data_attrs.keys():
			data_attr = getattr(self, 'data_{}'.format(data_attr_name))
			if type(data_attr) == str and data_attr.startswith('$__env.'):
				logger.debug('Detected env variable for config attr \'data_%s\'', data_attr_name)
				if not os.getenv(data_attr[7:]):
					logger.warning('Couldn\'t read env variable for config attr \'data_%s\'. Defaulting to \'%s\'', data_attr_name, data_attrs[data_attr_name])
					setattr(self, 'data_{}'.format(data_attr_name), data_attrs[data_attr_name])
				else:
					# [DOC] Set data_ssl to True rather than string env variable value
					if data_attr_name == 'ssl':
						data_attr = True
					else:
						data_attr = os.getenv(data_attr[7:])
					logger.warning('Setting env variable for config attr \'data_%s\' to \'%s\'', data_attr_name, data_attr)
					setattr(self, 'data_{}'.format(data_attr_name), data_attr)


		# [DOC] Check SSL settings
		if self.data_ca:
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			if not os.path.exists(os.path.join(__location__, 'certs')):
				os.makedirs(os.path.join(__location__, 'certs'))
			with open(os.path.join(__location__, 'certs', self.data_ca_name), 'w') as f:
				f.write(self.data_ca)
		
		from data import Data

		if self.data_driver == 'mongodb':
			from drivers.mongodb import MongoDb
			Data.driver = MongoDb

		# [DOC] Create default env dict
		self._sys_conn = Data.create_conn()
		self._sys_env = {
			'conn':self._sys_conn,
			'REMOTE_ADDR':'127.0.0.1',
			'HTTP_USER_AGENT':'LIMPd'
		}

		if self.data_azure_mongo:
			for module in modules:
				try:
					if modules[module].collection:
						logger.debug('Attempting to create shard collection: %s.', modules[module].collection)
						self._sys_conn.command('shardCollection', '{}.{}'.format(Config.data_name, modules[module].collection), key={'_id':'hashed'})
					else:
						logger.debug('Skipping service module: %s.', module)
				except Exception as err:
					logger.error(err)
		
		logger.debug('Testing realm mode.')
		if Config.realm:
			# [DOC] Append realm to env dict
			self._sys_env['realm'] = '__global'
			# [DOC] Append realm attrs to all modules attrs and set at as required in query_args and doc_args
			for module in modules.keys():
				if module != 'realm':
					logger.debug('Updated module \'%s\' for realm mode.', module)
					modules[module].attrs['realm'] = 'str'
					for method in modules[module].methods.keys():
						modules[module].methods[method].query_args.append('realm')
						modules[module].methods[method].doc_args.append('realm')
			# [DOC] Query all realms to provide access to available realms and to add realm docs to _sys_docs
			realm_results = modules['realm'].read(skip_events=[Event.__PERM__, Event.__ARGS__], env=self._sys_env)
			logger.debug('Found %s realms. Namely; %s', realm_results.args.count, ', '.join([doc.name for doc in realm_results.args.docs]))
			for doc in realm_results.args.docs:
				self._realms[doc.name] = doc
				self._sys_docs[doc._id] = {'module':'realm'}
			# [DOC] Create __global realm
			if '__global' not in self._realms:
				logger.debug('GLOBAL realm not found, creating it.')
				realm_results = modules['realm'].create(skip_events=[Event.__PERM__, Event.__PRE__], env=self._sys_env, doc={
					'_id':ObjectId('f00000000000000000000014'),
					'user':ObjectId('f00000000000000000000010'),
					'name':'__global',
					'default':'f00000000000000000000013'
				})
				logger.debug('GLOBAL realm creation results: %s', realm_results)
				if realm_results.status != 200:
					logger.error('Config step failed. Exiting.')
					exit()

		# [DOC] Check test mode
		if self.test:
			logger.debug('Test mode detected.')
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			if not os.path.exists(os.path.join(__location__, 'tests')):
				os.makedirs(os.path.join(__location__, 'tests'))
			if not self.test_env:
				for module in modules.keys():
					if modules[module].collection:
						logger.debug('Updating collection name \'%s\' of module %s', modules[module].collection, module)
						modules[module].collection = 'test_{}'.format(modules[module].collection)
						if self.test_flush:
							logger.debug('Flushing test collection \'%s\'', modules[module].collection)
							Data.drop(env=self._sys_env, session=None, collection=modules[module].collection)
					else:
						logger.debug('Skipping service module %s', module)
			else:
				logger.warning('Testing on \'%s\' env. LIMPd would be sleeping for 5secs to give you chance to abort test workflow if this was a mistake.', self.env)
				time.sleep(5)
				

		# [DOC] Checking users collection
		logger.debug('Testing users collection.')
		user_results = modules['user'].read(skip_events=[Event.__PERM__, Event.__ON__], env=self._sys_env, query=[{'_id':'f00000000000000000000010'}])
		if not user_results.args.count:
			logger.debug('ADMIN user not found, creating it.')
			admin_doc = {
				'_id': ObjectId('f00000000000000000000010'),
				'username': self.admin_username,
				'email': self.admin_email,
				'name': {
					locale: '__ADMIN' for locale in self.locales
				},
				'bio': {
					locale: '__ADMIN' for locale in self.locales
				},
				'address': {
					locale: '__ADMIN' for locale in self.locales
				},
				'postal_code': '__ADMIN',
				'phone': self.admin_phone,
				'website': 'https://ADMIN.limp.masaar.com',
				'groups': [],
				'privileges': {'*': '*'},
				'email_hash': jwt.encode({'hash':['email', self.admin_email, self.admin_password, self.anon_token]}, self.admin_password).decode('utf-8').split('.')[1],
				'phone_hash': jwt.encode({'hash':['phone', self.admin_phone, self.admin_password, self.anon_token]}, self.admin_password).decode('utf-8').split('.')[1],
				'username_hash': jwt.encode({'hash':['username', self.admin_username, self.admin_password, self.anon_token]}, self.admin_password).decode('utf-8').split('.')[1],
				'locale': self.locale,
				'attrs':{}
			}
			if Config.realm:
				admin_doc['realm'] = '__global'
			admin_results = modules['user'].create(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=self._sys_env, doc=admin_doc)
			logger.debug('ADMIN user creation results: %s', admin_results)
			if admin_results.status != 200:
				logger.error('Config step failed. Exiting.')
				exit()
		self._sys_docs[ObjectId('f00000000000000000000010')] = {
			'module':'user'
		}

		# [DOC] Test if ANON user exists
		user_results = modules['user'].read(skip_events=[Event.__PERM__, Event.__ON__], env=self._sys_env, query=[{'_id':'f00000000000000000000011'}])
		if not user_results.args.count:
			logger.debug('ANON user not found, creating it.')
			anon_results = modules['user'].create(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=self._sys_env, doc=self.compile_anon_user())
			logger.debug('ANON user creation results: %s', anon_results)
			if anon_results.status != 200:
				logger.error('Config step failed. Exiting.')
				exit()
		self._sys_docs[ObjectId('f00000000000000000000011')] = {
			'module':'user'
		}

		logger.debug('Testing sessions collection.')
		# [DOC] Test if ANON session exists
		session_results = modules['session'].read(skip_events=[Event.__PERM__, Event.__ON__], env=self._sys_env, query=[{'_id':'f00000000000000000000012'}])
		if not session_results.args.count:
			logger.debug('ANON session not found, creating it.')
			anon_results = modules['session'].create(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=self._sys_env, doc=self.compile_anon_session())
			logger.debug('ANON session creation results: %s', anon_results)
			if anon_results.status != 200:
				logger.error('Config step failed. Exiting.')
				exit()
		self._sys_docs[ObjectId('f00000000000000000000012')] = {
			'module':'session'
		}

		logger.debug('Testing groups collection.')
		# [DOC] Test if DEFAULT group exists
		group_results = modules['group'].read(skip_events=[Event.__PERM__, Event.__ON__], env=self._sys_env, query=[{'_id':'f00000000000000000000013'}])
		if not group_results.args.count:
			logger.debug('DEFAULT group not found, creating it.')
			group_doc = {
				'_id': ObjectId('f00000000000000000000013'),
				'user': ObjectId('f00000000000000000000010'),
				'name': {
					locale: '__DEFAULT' for locale in self.locales
				},
				'bio': {
					locale: '__DEFAULT' for locale in self.locales
				},
				'privileges': self.default_privileges,
				'attrs':{}
			}
			if self.realm:
				group_doc['realm'] = '__global'
			group_results = modules['group'].create(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=self._sys_env, doc=group_doc)
			logger.debug('DEFAULT group creation results: %s', group_results)
			if group_results.status != 200:
				logger.error('Config step failed. Exiting.')
				exit()
		self._sys_docs[ObjectId('f00000000000000000000013')] = {
			'module':'group'
		}
		
		# [DOC] Test app-specific groups
		logger.debug('Testing app-specific groups collection.')
		for group in self.groups:
			group_results = modules['group'].read(skip_events=[Event.__PERM__, Event.__ON__], env=self._sys_env, query=[{'_id':group['_id']}])
			if not group_results.args.count:
				logger.debug('App-specific group with name %s not found, creating it.', group['name'])
				if self.realm:
					group['realm'] = '__global'
				group_results = modules['group'].create(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=self._sys_env, doc=group)
				logger.debug('App-specific group with name %s creation results: %s', group['name'], group_results)
				if group_results.status != 200:
					logger.error('Config step failed. Exiting.')
					exit()
			self._sys_docs[ObjectId(group['_id'])] = {
				'module':'group'
			}
		
		# [DOC] Test app-specific data indexes
		logger.debug('Testing data indexes')
		for index in self.data_indexes:
			logger.debug('Attempting to create data index: %s', index)
			self._sys_conn[index['collection']].create_index(index['index'])
		logger.debug('Creating \'__deleted\' data indexes for all collections.')
		for module in modules:
			if modules[module].collection:
				logger.debug('Attempting to create \'__deleted\' data index for collection: %s', modules[module].collection)
				self._sys_conn[modules[module].collection].create_index([('__deleted', 1)])
		if self.realm:
			logger.debug('Creating \'realm\' data indexes for all collections.')
			for module in modules:
				if module != 'realm' and modules[module].collection:
					logger.debug('Attempting to create \'realm\' data index for collection: %s', modules[module].collection)
					self._sys_conn[modules[module].collection].create_index([('realm', 'text')])

		# [DOC] Test app-specific docs
		logger.debug('Testing docs.')
		for doc in self.docs:
			doc_results = modules[doc['module']].read(skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=self._sys_env, query=[{'_id':doc['doc']['_id']}])
			if not doc_results.args.count:
				if self.realm:
					doc['doc']['realm'] = '__global'
				skip_events = [Event.__PERM__]
				if 'skip_args' in doc.keys() and doc['skip_args'] == True:
					skip_events.append(Event.__ARGS__)
				doc_results = modules[doc['module']].create(skip_events=skip_events, env=self._sys_env, doc=doc['doc'])
				logger.debug('App-specific doc with _id \'%s\' of module \'%s\' creation results: %s', doc['doc']['_id'], doc['module'], doc_results)
				if doc_results.status != 200:
					logger.error('Config step failed. Exiting.')
					exit()
			self._sys_docs[ObjectId(doc['doc']['_id'])] = {
				'module':doc['module']
			}
		
		# [DOC] Check for test mode
		if self.test:
			logger.debug('Running tests')
			from utils import DictObj
			anon_session = self.compile_anon_session()
			anon_session['user'] = DictObj(self.compile_anon_user())
			Test.run_test(test_name=self.test, steps=False, modules=modules, env=self._sys_env, session=DictObj(anon_session))
			exit()
		
		# [DOC] Check for emulate_test mode
		if self.emulate_test:
			self.test = True
	
	@classmethod
	def compile_anon_user(self):
		anon_doc = {
			'_id': ObjectId('f00000000000000000000011'),
			'username': self.anon_token,
			'email': 'ANON@LIMP.MASAAR.COM',
			'name': {
				locale: '__ANON' for locale in self.locales
			},
			'bio': {
				locale: '__ANON' for locale in self.locales
			},
			'address': {
				locale: '__ANON' for locale in self.locales
			},
			'postal_code': '__ANON',
			'phone': '+0',
			'website': 'https://ANON.limp.masaar.com',
			'groups': [],
			'privileges': self.anon_privileges,
			'email_hash': self.anon_token,
			'phone_hash': self.anon_token,
			'username_hash': self.anon_token,
			'locale': self.locale,
			'attrs':{}
		}
		if self.realm:
			anon_doc['realm'] = '__global'
		return anon_doc

	@classmethod
	def compile_anon_session(self):
		session_doc = {
			'_id': ObjectId('f00000000000000000000012'),
			'user': ObjectId('f00000000000000000000011'),
			'host_add': '127.0.0.1',
			'user_agent': self.anon_token,
			'timestamp': '1970-01-01T00:00:00',
			'expiry': '1970-01-01T00:00:00',
			'token': self.anon_token
		}
		if self.realm:
			session_doc['realm'] = '__global'
		return session_doc