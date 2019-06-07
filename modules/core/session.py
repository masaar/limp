from base_module import BaseModule, BaseModel
from event import Event

from bson import ObjectId

import logging, datetime, time, json, jwt, secrets
logger = logging.getLogger('limp')

class Session(BaseModule):
	collection = 'sessions'
	attrs = {
		'user':'id',
		'host_add':'ip',
		'user_agent':'str',
		'timestamp':'time',
		'expiry':'time',
		'token':'str'
	}
	extns = {
		'user':['user', ['*'], True]
	}
	methods = {
		'read':{
			'permissions':[['read', {'user':'$__user'}, {}]]
		},
		'create':{
			'permissions':[['create', {}, {}]]
		},
		'update':{
			'permissions':[['update', {'user':'$__user'}, {'user':None}]],
			'query_args':['_id']
		},
		'delete':{
			'permissions':[['delete', {'user':'$__user'}, {}]],
			'query_args':['_id']
		},
		'auth':{
			'permissions':[['*', {}, {}]],
			'doc_args':['hash', ('username', 'phone', 'email')]
		},
		'reauth':{
			'permissions':[['*', {}, {}]],
			'query_args':['_id', 'hash']
		},
		'signout':{
			'permissions':[['*', {}, {}]],
			'query_args':['_id']
		}
	}

	def auth(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if 'username' in doc.keys(): key = 'username'
		elif 'phone' in doc.keys(): key = 'phone'
		elif 'email' in doc.keys(): key = 'email'
		user_results = self.modules['user'].methods['read'](skip_events=[Event.__PERM__, Event.__ON__], env=env, session=session, query={key:{'val':doc[key]}, '{}_hash'.format(key):{'val':doc['hash']}, '$limit':1})
		if not user_results['args']['count']:
			return {
				'status':403,
				'msg':'Wrong auth credentials.',
				'args':{'code':'CORE_SESSION_INVALID_CREDS'}
			}
		user = user_results['args']['docs'][0]
		# results = self.modules['user'].methods['read_privileges'](skip_events=[Event.__PERM__], env=env, session=session, query=[[{'_id':results['args']['docs'][0]}]])
		#logger.debug('auth success')
		token = secrets.token_urlsafe(32)
		session = {
			'user':user._id,
			'host_add':env['REMOTE_ADDR'],
			'user_agent':env['HTTP_USER_AGENT'],
			'timestamp':datetime.datetime.fromtimestamp(time.time()),
			'expiry':datetime.datetime.fromtimestamp(time.time() + 2592000),
			'token':token
		}
		# logger.debug('creating session:%s', session)
		results = self.methods['create'](skip_events=[Event.__PERM__], env=env, session=session, doc=session)
		if results['status'] != 200:
			return results
		# results['args']['docs'][0]._attrs().update(session)
		# logger.debug('session_results: %s', results)

		session['_id'] = results.args.docs[0]._id
		session['user'] = user
		results['args']['docs'][0] = BaseModel(session)
		
		# [DOC] read user privileges and return them
		user_results = self.modules['user'].methods['read_privileges'](skip_events=[Event.__PERM__], env=env, session=results['args']['docs'][0], query=[{'_id':user._id}])
		if user_results['status'] != 200:
			return user_results
		results['args']['docs'][0]['user'] = user_results['args']['docs'][0]

		return {
			'status':200,
			'msg':'You were succefully authed.',
			'args':results['args']
		}
	
	def reauth(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if str(query['_id']):
			return {
				'status':400,
				'msg':'Reauth is not required for \'__ANON\' user.',
				'args':{'code':'CORE_SESSION_ANON_REAUTH'}
			}
		results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':query['_id']['val']}])
		if not results['args']['count']:
			return {
				'status':403,
				'msg':'Session is invalid.',
				'args':{'code':'CORE_SESSION_INVALID_SESSION'}
			}
		
		if jwt.encode({'token':results['args']['docs'][0].token}, results['args']['docs'][0].token).decode('utf-8').split('.')[1] != query['hash']['val']:
			return {
				'status':403,
				'msg':'Reauth token hash invalid.',
				'args':{'code':'CORE_SESSION_INVALID_REAUTH_HASH'}
			}
		if results['args']['docs'][0].expiry < datetime.datetime.fromtimestamp(time.time()):
			results = self.methods['delete'](skip_events=[Event.__PERM__, Event.__SOFT__], env=env, session=session, query=[{'_id':session._id}])
			return {
				'status':403,
				'msg':'Session had expired.',
				'args':{'code':'CORE_SESSION_SESSION_EXPIRED'}
			}
		# [DOC] update user's last_login timestamp
		self.modules['user'].methods['update'](skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':results['args']['docs'][0].user}], doc={'login_time':datetime.datetime.fromtimestamp(time.time())})
		self.methods['update'](skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':results['args']['docs'][0]._id}], doc={'expiry':datetime.datetime.fromtimestamp(time.time() + 2592000)})
		# [DOC] read user privileges and return them
		user_results = self.modules['user'].methods['read_privileges'](skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':results['args']['docs'][0].user._id}])
		results['args']['docs'][0]['user'] = user_results['args']['docs'][0]
		return {
			'status':200,
			'msg':'You were succefully reauthed.',
			'args':results['args']
		}

	def signout(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if query['_id']['val'] == 'f00000000000000000000012' or query['_id']['val'] == ObjectId('f00000000000000000000012'):
			return {
				'status':400,
				'msg':'Singout is not allowed for \'__ANON\' user.',
				'args':{'code':'CORE_SESSION_ANON_SIGNOUT'}
			}
		results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':query['_id']['val']}])
		#logger.debug('session find results: %s.', results)
		if not results['args']['count']:
			return {
				'status':403,
				'msg':'Session is invalid.',
				'args':{'code':'CORE_SESSION_INVALID_SESSION'}
			}
		results = self.methods['delete'](skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':session._id}])
		print('session/signout:', results)
		return {
			'status':200,
			'msg':'You are succefully signed-out.',
			'args':results['args']
		}
	
	def check_permissions(self, session, module, permissions):
		module = module.module_name
		user = session.user
		print('user', user)

		for permission in permissions:
			logger.debug('checking permission: %s against: %s', permission, user.privileges)
			permission_pass = False
			if permission[0] == '*':
				permission_pass = True
			
			if not permission_pass:
				if permission[0].find('.') == -1:
					permission_module = module
					permission_attr = permission[0]
				elif permission[0].find('.') != -1:
					permission_module = permission[0].split('.')[0]
					permission_attr = permission[0].split('.')[1]
				
				if '*' in user.privileges.keys() and permission_module not in user.privileges.keys():
					user.privileges[permission_module] = user.privileges['*']
				if permission_module in user.privileges.keys():
					if user.privileges[permission_module] == '*':
						user.privileges[permission_module] = self.privileges
					if type(user.privileges[permission_module]) == list and '*' in user.privileges[permission_module]:
						user.privileges[permission_module] += self.privileges
				if permission_module not in user.privileges.keys(): user.privileges[permission_module] = []
				
				if permission_attr in user.privileges[permission_module]:
					permission_pass = True

			if permission_pass:
				logger.debug('checking permission, query: %s', permission[1])
				query = {attr:permission[1][attr] for attr in permission[1].keys() if type(permission[1][attr]) == dict}
				query.update({attr:{'val':permission[1][attr]} for attr in permission[1].keys() if type(permission[1][attr]) == str})
				query.update({attr:permission[1][attr] for attr in permission[1].keys() if type(permission[1][attr]) == int})
				#logger.debug('checking permission, query: %s', query)
				# query = {attr:{'val':query[attr]} for attr in query.keys() if type(query[attr]) != dict}
				doc = {attr:permission[2][attr] for attr in permission[2].keys()}
				attrs_list = [query, doc]
				for attrs in attrs_list:
					for attr in attrs.keys():
						#logger.debug('examining permission arg: %s, %s', attr, attrs[attr])
						if attrs[attr] == '$__user':
							attrs[attr] = user
						elif type(attrs[attr]) == dict and 'val' in attrs[attr].keys() and attrs[attr]['val'] == '$__user':
							attrs[attr]['val'] = user
						elif attrs[attr] == '$__access':
							attrs[attr] = {
								'$__user':user,
								'$__groups':user.groups
							}
						elif type(attrs[attr]) == dict and 'val' in attrs[attr].keys() and attrs[attr]['val'] == '$__access':
							attrs[attr]['val'] = {
								'$__user':user,
								'$__groups':user.groups
							}
						elif attrs[attr] == '$__time':
							attrs[attr] = datetime.datetime.fromtimestamp(time.time())
						elif type(attrs[attr]) == dict and 'val' in attrs[attr].keys() and attrs[attr]['val'] == '$__time':
							attrs[attr]['val'] = datetime.datetime.fromtimestamp(time.time())
						#logger.debug('processed permission arg: %s, %s', attr, attrs[attr])
					#logger.debug('processed permission args: %s', attrs)
				return {
					'query': query,
					'doc': doc
				}
		# [DOC] If all permission checks fail
		return False
