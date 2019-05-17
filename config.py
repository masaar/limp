from bson import ObjectId
from event import Event
from test import Test

import os, jwt, logging, datetime

logger = logging.getLogger('limp')


class Config:
	debug = False

	test = False
	test_flush = False
	test_force = False
	tests = {}

	data_driver = 'mongodb'
	data_server = 'mongodb://localhost'
	data_name = 'limp_data'
	data_ssl = False
	data_ca_name = None
	data_ca = None

	data_azure_mongo = False

	sms_auth = {}

	email_auth = {}

	locales = ['ar_AE', 'en_AE']
	locale = 'ar_AE'

	events = {}
	templates = {}
	l10n = {}

	admin_username = '__ADMIN'
	admin_email = 'ADMIN@LIMP.MASAAR.COM'
	admin_phone = '+971500000000'
	admin_password = '__ADMIN'

	anon_token = '__ANON_TOKEN_f00000000000000000000012'
	anon_privileges = {}

	groups = []
	default_privileges = {}

	data_indexes = []

	docs = []

	realm = False


	@classmethod
	def config_data(self, modules):
		# [DOC] Check SSL settings
		if self.data_ca:
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			if not os.path.exists(os.path.join(__location__, 'certs')):
				os.makedirs(os.path.join(__location__, 'certs'))
			with open(os.path.join(__location__, 'certs', self.data_ca_name), 'w') as f:
				f.write(self.data_ca)
		
		from data import Data
		conn = Data.create_conn() #pylint: disable=no-value-for-parameter
		env = {'conn':conn}
		if self.realm:
			env['realm'] = '__global'

		if self.data_azure_mongo:
			for module in modules:
				try:
					logger.debug('Attempting to create shard collection: %s.', modules[module].collection)
					conn.command('shardCollection', '{}.{}'.format(Config.data_name, modules[module].collection), key={'_id':'hashed'})
				except Exception as err:
					logger.error(err)
		
		logger.debug('Testing realm mode.')
		if Config.realm:
			for module in modules.keys():
				modules[module].attrs['realm'] = 'str'
				for method in modules[module].methods.keys():
					modules[module].methods[method].query_args.append('!realm')
					modules[module].methods[method].doc_args.append('!realm')
		
		# [DOC] Check test mode
		if self.test:
			logger.debug('Test mode detected.')
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			if not os.path.exists(os.path.join(__location__, 'tests')):
				os.makedirs(os.path.join(__location__, 'tests'))
			for module in modules.keys():
				logger.debug('Updating collection name \'%s\' of module %s', modules[module].collection, module)
				modules[module].collection = 'test_{}'.format(modules[module].collection)
				if self.test_flush:
					Data.drop(env=env, session=None, collection=modules[module].collection) #pylint: disable=no-value-for-parameter

		# [DOC] Checking users collection
		logger.debug('Testing users collection.')
		user_results = modules['user'].methods['read'](skip_events=[Event.__PERM__, Event.__ON__, Event.__NOTIF__], env=env, query={'_id':{'val':'f00000000000000000000010'}})
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
				'email_hash': jwt.encode({'hash':['email', self.admin_email, self.admin_password]}, self.admin_password).decode('utf-8').split('.')[1],
				'phone_hash': jwt.encode({'hash':['phone', self.admin_phone, self.admin_password]}, self.admin_password).decode('utf-8').split('.')[1],
				'username_hash': jwt.encode({'hash':['username', self.admin_username, self.admin_password]}, self.admin_password).decode('utf-8').split('.')[1],
				'locale': self.locale,
				'attrs':{}
			}
			if Config.realm:
				admin_doc['realm'] = '__global'
			admin_results = modules['user'].methods['create'](skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__, Event.__NOTIF__], env=env, doc=admin_doc)
			logger.debug('ADMIN user creation results: %s', admin_results)

		user_results = modules['user'].methods['read'](skip_events=[Event.__PERM__, Event.__ON__, Event.__NOTIF__], env=env, query={'_id':{'val':'f00000000000000000000011'}})
		if not user_results.args.count:
			logger.debug('ANON user not found, creating it.')
			anon_results = modules['user'].methods['create'](skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__, Event.__NOTIF__], env=env, doc=self.compile_anon_user())
			logger.debug('ANON user creation results: %s', anon_results)

		logger.debug('Testing sessions collection.')
		# [Doc] test if ANON session exists
		session_results = modules['session'].methods['read'](skip_events=[Event.__PERM__, Event.__ON__, Event.__NOTIF__], env=env, query={'_id':{'val':'f00000000000000000000012'}})
		if not session_results.args.count:
			logger.debug('ANON session not found, creating it.')
			anon_results = modules['session'].methods['create'](skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__, Event.__NOTIF__], env=env, doc=self.compile_anon_session())
			logger.debug('ANON session creation results: %s', anon_results)

		logger.debug('Testing groups collection.')
		# [Doc] test if DEFAULT group exists
		group_results = modules['group'].methods['read'](skip_events=[Event.__PERM__, Event.__ON__, Event.__NOTIF__], env=env, query={'_id':{'val':'f00000000000000000000013'}})
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
			group_results = modules['group'].methods['create'](skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__, Event.__NOTIF__], env=env, doc=group_doc)
			logger.debug('DEFAULT group creation results: %s', group_results)
		
		logger.debug('Testing app-specific groups collection.')
		# [DOC] test app-specific groups
		for group in self.groups:
			group_results = modules['group'].methods['read'](skip_events=[Event.__PERM__, Event.__ON__, Event.__NOTIF__], env=env, query={'_id':{'val':group['_id']}})
			if not group_results.args.count:
				logger.debug('App-specific group with name %s not found, creating it.', group['name'])
				if self.realm:
					group['realm'] = '__global'
				group_results = modules['group'].methods['create'](skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__, Event.__NOTIF__], env=env, doc=group)
				logger.debug('App-specific group with name %s creation results: %s', group['name'], group_results)
		
		logger.debug('Testing data indexes')
		for index in self.data_indexes:
			logger.debug('Attempting to create data index: %s', index)
			conn[index['collection']].create_index(index['index'])

		logger.debug('Testing docs.')
		for doc in self.docs:
			doc_results = modules[doc['module']].methods['read'](skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__], env=env, query={'_id':{'val':doc['doc']['_id']}})
			if not doc_results.args.count:
				if self.realm:
					doc['doc']['realm'] = '__global'
				modules[doc['module']].methods['create'](skip_events=[Event.__PERM__], env=env, doc=doc['doc'])
		
		if self.test:
			logger.debug('Running tests')
			from utils import DictObj
			Test.run_test(test_name=self.test, modules=modules, env=env, session=DictObj({
				'user':DictObj(self.compile_anon_user())
			}))
			exit()
	
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
			'timestamp': datetime.datetime.fromtimestamp(86400) - datetime.timedelta(days=1),
			'expiry': datetime.datetime.fromtimestamp(86400) - datetime.timedelta(days=1),
			'token': self.anon_token
		}
		if self.realm:
			session_doc['realm'] = '__global'
		return session_doc