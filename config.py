from bson import ObjectId
from event import Event

import logging, datetime

logger = logging.getLogger('limp')


class Config:
	debug = False

	data_driver = 'mongodb'
	data_server = 'mongodb://localhost'
	data_port = 27017
	data_name = 'limp_data'

	sms_auth = {}

	email_auth = {}

	locales = ['ar_AE', 'en_AE']
	locale = 'ar_AE'

	events = {}
	templates = {}

	l10n = {}

	@classmethod
	def config_data(self, modules):
		# [DOC] Checking users collection
		logger.debug('Testing users collection.')
		user_results = modules['user'].methods['read'](
			skip_events=[Event.__PERM__, Event.__ON__, Event.__NOTIF__])
		# [Doc] test if ADMIN, ANON users exist
		admin_exists = False
		anon_exists = False
		for doc in user_results.args.docs:
			if str(doc._id) == 'f00000000000000000000010':
				admin_exists = True
			if str(doc._id) == 'f00000000000000000000011':
				anon_exists = True
		if not admin_exists:
			logger.debug('ADMIN user not found, creating it.')
			admin_results = modules['user'].methods['create'](skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__, Event.__NOTIF__], doc={
				'_id': ObjectId('f00000000000000000000010'),
				'username': '__ADMIN',
				'email': 'ADMIN@LIMP.MASAAR.COM',
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
				'phone': '+971550000000',
				'website': 'https://ADMIN.limp.masaar.com',
				'groups': [],
				'privileges': {
					'*': '*'
				},
				'email_hash': 'eyJwYXNzd29yZCI6Il9fQURNSU4iLCJlbWFpbCI6IkFETUlOQExJTVAuTUFTQUFSLkNPTSJ9',
				'phone_hash': '__ADMIN',
				'username_hash': '__ADMIN',
				'locale': 'en_AE'
			})
			logger.debug('ADMIN user creation results %s', admin_results)
		if not anon_exists:
			logger.debug('ANON user not found, creating it.')
			anon_results = modules['user'].methods['create'](skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__, Event.__NOTIF__], doc={
				'_id': ObjectId('f00000000000000000000011'),
				'username': '__ANON',
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
				'phone': '+971000000000',
				'website': 'https://ANON.limp.masaar.com',
				'groups': [],
				'privileges': {
					'*': '*'
				},
				'email_hash': '__ANON',
				'phone_hash': '__ANON',
				'username_hash': '__ANON',
				'locale': 'en_AE'
			})
			logger.debug('ANON user creation results %s', anon_results)

		logger.debug('Testing sessions collection.')
		session_results = modules['session'].methods['read'](
			skip_events=[Event.__PERM__, Event.__ON__, Event.__NOTIF__])
		# [Doc] test if ANON session exists
		anon_exists = False
		for doc in session_results.args.docs:
			if str(doc._id) == 'f00000000000000000000012':
				anon_exists = True
		if not anon_exists:
			logger.debug('ANON session not found, creating it.')
			admin_results = modules['session'].methods['create'](skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__, Event.__NOTIF__], doc={
				'_id': ObjectId('f00000000000000000000012'),
				'user': ObjectId('f00000000000000000000010'),
				'host_add': '127.0.0.1',
				'user_agent': '__ANON',
				'timestamp': datetime.datetime.fromtimestamp(86400) - datetime.timedelta(days=1),
				'expiry': datetime.datetime.fromtimestamp(86400) - datetime.timedelta(days=1),
				'token': '__ANON'
			})
			logger.debug('ANON session creation results %s', admin_results)

		logger.debug('Testing groups collection.')
		group_results = modules['group'].methods['read'](
			skip_events=[Event.__PERM__, Event.__ON__, Event.__NOTIF__])
		# [Doc] test if DEFAULT group exists
		default_exists = False
		for doc in group_results.args.docs:
			if str(doc._id) == 'f00000000000000000000013':
				default_exists = True
		if not default_exists:
			logger.debug('DEFAULT group not found, creating it.')
			admin_results = modules['group'].methods['create'](skip_events=[Event.__PERM__, Event.__PRE__, Event.__ON__, Event.__NOTIF__], doc={
				'_id': ObjectId('f00000000000000000000013'),
				'user': ObjectId('f00000000000000000000010'),
				'name': {
					locale: '__DEFAULT' for locale in self.locales
				},
				'bio': {
					locale: '__DEFAULT' for locale in self.locales
				},
				'privileges': {}
			})
			logger.debug('DEFAULT group creation results %s', admin_results)