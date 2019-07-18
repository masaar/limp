from base_module import BaseModule, BaseModel
from event import Event
# from utils import NONE_VALUE

from bson import ObjectId

import logging, jwt, secrets, copy, datetime
logger = logging.getLogger('limp')

class Session(BaseModule):
	collection = 'sessions'
	attrs = {
		'user':'id',
		'host_add':'ip',
		'user_agent':'str',
		'timestamp':'datetime',
		'expiry':'datetime',
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
		user_results = self.modules['user'].read(skip_events=[Event.__PERM__, Event.__ON__], env=env, session=session, query=[{key:doc[key], '{}_hash'.format(key):doc['hash'], '$limit':1}])
		if not user_results.args.count:
			return {
				'status':403,
				'msg':'Wrong auth credentials.',
				'args':{'code':'CORE_SESSION_INVALID_CREDS'}
			}
		user = user_results.args.docs[0]

		token = secrets.token_urlsafe(32)
		session = {
			'user':user._id,
			'host_add':env['REMOTE_ADDR'],
			'user_agent':env['HTTP_USER_AGENT'],
			'timestamp':datetime.datetime.utcnow().isoformat(),
			'expiry':(datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat(),
			'token':token
		}
		# logger.debug('creating session:%s', session)
		results = self.create(skip_events=[Event.__PERM__], env=env, session=session, doc=session)
		if results.status != 200:
			return results

		session['_id'] = results.args.docs[0]._id
		session['user'] = user
		results.args.docs[0] = BaseModel(session)
		
		# [DOC] read user privileges and return them
		user_results = self.modules['user'].read_privileges(skip_events=[Event.__PERM__], env=env, session=results.args.docs[0], query=[{'_id':user._id}])
		if user_results.status != 200:
			return user_results
		results.args.docs[0]['user'] = user_results.args.docs[0]

		return {
			'status':200,
			'msg':'You were succefully authed.',
			'args':results.args
		}
	
	def reauth(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if str(query['_id'][0]) == 'f00000000000000000000012':
			return {
				'status':400,
				'msg':'Reauth is not required for \'__ANON\' user.',
				'args':{'code':'CORE_SESSION_ANON_REAUTH'}
			}
		results = self.read(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':query['_id'][0]}])
		if not results.args.count:
			return {
				'status':403,
				'msg':'Session is invalid.',
				'args':{'code':'CORE_SESSION_INVALID_SESSION'}
			}
		
		if jwt.encode({'token':results.args.docs[0].token}, results.args.docs[0].token).decode('utf-8').split('.')[1] != query['hash'][0]:
			return {
				'status':403,
				'msg':'Reauth token hash invalid.',
				'args':{'code':'CORE_SESSION_INVALID_REAUTH_HASH'}
			}
		if results.args.docs[0].expiry < datetime.datetime.utcnow().isoformat():
			results = self.delete(skip_events=[Event.__PERM__, Event.__SOFT__], env=env, session=session, query=[{'_id':session._id}])
			return {
				'status':403,
				'msg':'Session had expired.',
				'args':{'code':'CORE_SESSION_SESSION_EXPIRED'}
			}
		# [DOC] update user's last_login timestamp
		self.modules['user'].update(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':results.args.docs[0].user}], doc={'login_time':datetime.datetime.utcnow().isoformat()})
		self.update(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':results.args.docs[0]._id}], doc={'expiry':(datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat()})
		# [DOC] read user privileges and return them
		user_results = self.modules['user'].read_privileges(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':results.args.docs[0].user._id}])
		results.args.docs[0]['user'] = user_results.args.docs[0]
		return {
			'status':200,
			'msg':'You were succefully reauthed.',
			'args':results.args
		}

	def signout(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if str(query['_id'][0]) == 'f00000000000000000000012':
			return {
				'status':400,
				'msg':'Singout is not allowed for \'__ANON\' user.',
				'args':{'code':'CORE_SESSION_ANON_SIGNOUT'}
			}
		results = self.read(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':query['_id'][0]}])

		if not results.args.count:
			return {
				'status':403,
				'msg':'Session is invalid.',
				'args':{'code':'CORE_SESSION_INVALID_SESSION'}
			}
		results = self.delete(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':session._id}])

		return {
			'status':200,
			'msg':'You are succefully signed-out.',
			'args':results.args #pylint: disable=no-member
		}
	
	def check_permissions(self, session, module, permissions):
		module = module.module_name
		user = session.user

		permissions = copy.deepcopy(permissions)

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
				query = self.parse_permission_args(permission_args=permission[1], user=user)
				doc = self.parse_permission_args(permission_args=permission[2], user=user)
				return {
					'query': query,
					'doc': doc
				}
		# [DOC] If all permission checks fail
		return False

	def parse_permission_args(self, permission_args, user):
		if type(permission_args) == list:
			args_iter = range(0, permission_args.__len__())
		elif type(permission_args) == dict:
			args_iter = list(permission_args.keys())
		
		for j in args_iter:
			if type(permission_args[j]) == dict:
				# [DOC] Check for optional attrs
				if '__optional' in permission_args[j].keys():
					# [TODO] Implement conditions
					# [DOC] Convert None values to NONE_VALUE
					# if permission_args[j]['__optional'] == None:
					# 	permission_args[j]['__optional'] = NONE_VALUE
					permission_args[j] = self.parse_permission_args(permission_args=[permission_args[j]['__optional']], user=user)[0]
				else:
					# [DOC] Check opers
					for oper in ['$gt', '$lt', '$gte', '$lte', '$bet', '$not', '$regex', '$all', '$in']:
						if oper in permission_args[j].keys():
							if oper == '$bet':
								permission_args[j]['$bet'] = self.parse_permission_args(permission_args=permission_args[j]['$bet'], user=user)
							else:
								permission_args[j][oper] = self.parse_permission_args(permission_args=[permission_args[j][oper]], user=user)[0]
							# [DOC] Continue the iteration
							continue
					# [DOC] Child args, parse
					permission_args[j] = self.parse_permission_args(permission_args=permission_args[j], user=user)
			elif type(permission_args[j]) == list:
				permission_args[j] = self.parse_permission_args(permission_args=permission_args[j], user=user)
			elif type(permission_args[j]) == str:
				# [DOC] Check for variables
				if permission_args[j] == '$__user':
					permission_args[j] = user._id
				elif permission_args[j] == '$__access':
					permission_args[j] = {
						'$__user':user._id,
						'$__groups':user.groups
					}
				elif permission_args[j] == '$__datetime':
					permission_args[j] = datetime.datetime.utcnow().isoformat()
				elif permission_args[j] == '$__date':
					permission_args[j] = datetime.date.today().isoformat()
				elif permission_args[j] == '$__time':
					permission_args[j] = datetime.datetime.now().time().isoformat()
		
		return permission_args