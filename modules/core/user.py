from base_module import BaseModule
from event import Event
from config import Config

from bson import ObjectId
import datetime, time

class User(BaseModule):
	collection = 'users'
	attrs = {
		'username':'str',
		'email':'email',
		'phone':'phone',
		'name':'locale',
		'bio':'locale',
		'address':'locale',
		'postal_code':'str',
		'website':'uri:web',
		'locale':'locales',
		'create_time':'time',
		'login_time':'time',
		'groups':['id'],
		'privileges':'privileges',
		'username_hash':'str',
		'email_hash':'str',
		'phone_hash':'str',
		'status':('active', 'banned', 'deleted', 'disabled_password'),
		'attrs':'attrs'
	}
	optional_attrs = ['website', 'locale', 'login_time', 'status', 'attrs']
	extns = {
		# 'groups': ['group', ['*']]
	}
	methods = {
		'read':{
			'permissions':[['admin', {}, {}], ['read', {'_id':'$__user'}, {}]]
		},
		'create':{
			'permissions':[['admin', {}, {}]]
		},
		'update':{
			'permissions':[['admin', {}, {'groups':None}], ['update', {'_id':'$__user'}, {'groups':None, 'privileges':None}]],
			'query_args':['_id']
		},
		'delete':{
			'permissions':[['admin', {}, {}], ['delete', {'_id':'$__user'}, {}]],
			'query_args':['_id']
		},
		'read_privileges':{
			'permissions':[['admin', {}, {}], ['read', {'_id':'$__user'}, {}]],
			'query_args':['_id']
		},
		'add_group':{
			'permissions':[['admin', {}, {}]],
			'query_args':['_id'],
			'doc_args':['group']
		},
		'delete_group':{
			'permissions':[['admin', {}, {}]],
			'query_args':['_id'],
			'doc_args':['group']
		}
	}

	def on_read(self, results, skip_events, env, session, query, doc):
		for i in range(0, results['docs'].__len__()):
			user = results['docs'][i]
			del user['username_hash']
			del user['email_hash']
			del user['phone_hash']
		return (results, skip_events, env, session, query, doc)
	
	def pre_create(self, skip_events, env, session, query, doc):
		results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query={'__OR:username':{'val':doc['username']}, '__OR:email':{'val':doc['email']}, '__OR:phone':{'val':doc['phone']}, '$limit':1})
		if results['args']['count']:
			return {
				'status':400,
				'msg':'A user with the same username, email or phone already exists.',
				'args':{'code':'CORE_USER_DUPLICATE_USER'}
			}
		if Config.realm:
			realm_results = self.modules['realm'].methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query={'realm':{'val':env['realm']}})
			realm = realm_results.args.docs[0]
			doc['groups'] = [realm.default]
		else:
			doc['groups'] = [ObjectId('f00000000000000000000013')]
		doc['privileges'] = {}
		if 'locale' not in doc.keys():
			doc['locale'] = Config.locale
		if 'status' not in doc.keys():
			doc['status'] = 'active'
		if 'attrs' not in doc.keys():
			doc['attrs'] = {}
		# print('(skip_events, env, session, query, doc)', (skip_events, env, session, query, doc))
		return (skip_events, env, session, query, doc)
	
	def pre_update(self, skip_events, env, session, query, doc):
		# [DOC] Make sure no attrs overwriting would happen
		if 'attrs' in doc.keys():
			results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=query)
			if not results['args']['count']:
				return {
					'status':400,
					'msg':'User is invalid.',
					'args':{'code':'CORE_USER_INVALID_USER'}
				}
			if results['args']['count'] > 1:
				return {
					'status':400,
					'msg':'Updating user attrs can be done only to individual users.',
					'args':{'code':'CORE_USER_MULTI_ATTRS_UPDATE'}
				}
			results['args']['docs'][0]['attrs'].update(
				{attr:doc['attrs'][attr] for attr in doc['attrs'].keys() if doc['attrs'][attr] != None and doc['attrs'][attr] != ''}
			)
			doc['attrs'] = results['args']['docs'][0]['attrs']
		return (skip_events, env, session, query, doc)
	
	# [TODO] Add pre_update method to check for duplications at time of updating

	def read_privileges(self, skip_events=[], env={}, session=None, query=[], doc={}):
		# [DOC] Confirm _id is valid
		results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':query['_id'][0]}])
		if not results['args']['count']:
			return {
				'status':400,
				'msg':'User is invalid.',
				'args':{'code':'CORE_USER_INVALID_USER'}
			}
		user = results['args']['docs'][0]
		for group in user.groups:
			group_results = self.modules['group'].methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':group}])
			group = group_results['args']['docs'][0]
			for privilege in group.privileges.keys():
				if privilege not in user.privileges.keys(): user.privileges[privilege] = []
				for i in range(0, group.privileges[privilege].__len__()):
					if group.privileges[privilege][i] not in user.privileges[privilege]:
						user.privileges[privilege].append(group.privileges[privilege][i])
		return results
	
	def add_group(self, skip_events=[], env={}, session=None, query=[], doc={}):
		# [DOC] Check group privileges
		# if ('*' in session.user.privileges.keys() and session.user.privileges['*'] == '*') \
		# or ('__group_*' in session.user.privileges.keys() and session.user.privileges['__group_'])
		# [DOC] Confirm all basic args are provided
		doc['group'] = ObjectId(doc['group'])
		# [DOC] Confirm group is valid
		results = self.modules['group'].methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query={'_id':{'val':doc['group']}, '$limit':1})
		if not results['args']['count']:
			return {
				'status':400,
				'msg':'Group is invalid.',
				'args':{'code':'CORE_USER_INVALID_GROUP'}
			}
		# [DOC] Get user details
		results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query={**query, '$limit':1})
		if not results['args']['count']:
			return {
				'status':400,
				'msg':'User is invalid.',
				'args':{'code':'CORE_USER_INVALID_USER'}
			}
		user = results['args']['docs'][0]
		# [DOC] Confirm group was not added before
		if doc['group'] in user.groups:
			return {
				'status':400,
				'msg':'User is already a member of the group.',
				'args':{'code':'CORE_USER_GROUP_ADDED'}
			}
		user.groups.append(doc['group'])
		# [DOC] Update the user
		results = self.methods['update'](skip_events=[Event.__PERM__], env=env, session=session, query=query, doc={'groups':user.groups})
		return results
	
	def delete_group(self, skip_events=[], env={}, session=None, query=[], doc={}):
		# [DOC] Confirm all basic args are provided
		doc['group'] = ObjectId(doc['group'])
		# [DOC] Confirm group is valid
		results = self.modules['group'].methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query={'_id':{'val':doc['group']}, '$limit':1})
		if not results['args']['count']:
			return {
				'status':400,
				'msg':'Group is invalid.',
				'args':{'code':'CORE_USER_INVALID_GROUP'}
			}
		# [DOC] Get user details
		results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query={**query, '$limit':1})
		if not results['args']['count']:
			return {
				'status':400,
				'msg':'User is invalid.',
				'args':{'code':'CORE_USER_INVALID_USER'}
			}
		user = results['args']['docs'][0]
		# [DOC] Confirm group was not added before
		if doc['group'] not in user.groups:
			return {
				'status':400,
				'msg':'User is not a member of the group.',
				'args':{'code':'CORE_USER_GROUP_NOT_ADDED'}
			}
		user.groups = [group for group in user.groups if str(group) != str(doc['group'])]
		# [DOC] Update the user
		results = self.methods['update'](skip_events=[Event.__PERM__], env=env, session=session, query=query, doc={'groups':user.groups})
		return results

class Group(BaseModule):
	collection = 'groups'
	attrs = {
		'user':'id',
		'name':'locale',
		'bio':'locale',
		'privileges':'privileges',
		'attrs':'attrs'
	}
	optional_attrs = ['attrs']
	methods = {
		'read':{
			'permissions':[['admin', {}, {}]]
		},
		'create':{
			'permissions':[['admin', {}, {}]]
		},
		'update':{
			'permissions':[['admin', {}, {}], ['update', {'user':'$__user', 'privileges':None}]],
			'query_args':['_id']
		},
		'delete':{
			'permissions':[['admin', {}, {}], ['delete', {'user':'$__user'}]],
			'query_args':['_id']
		}
	}

	def pre_create(self, skip_events, env, session, query, doc):
		if 'attrs' not in doc.keys():
			doc['attrs'] = {}
		return (skip_events, env, session, query, doc)

	def pre_update(self, skip_events, env, session, query, doc):
		# [DOC] Make sure no attrs overwriting would happen
		if 'attrs' in doc.keys():
			results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=query)
			if not results['args']['count']:
				return {
					'status':400,
					'msg':'Group is invalid.',
					'args':{'code':'CORE_GROUP_INVALID_GROUP'}
				}
			if results['args']['count'] > 1:
				return {
					'status':400,
					'msg':'Updating group attrs can be done only to individual groups.',
					'args':{'code':'CORE_GROUP_MULTI_ATTRS_UPDATE'}
				}
			results['args']['docs'][0]['attrs'].update(
				{attr:doc['attrs'][attr] for attr in doc['attrs'].keys() if doc['attrs'][attr] != None and doc['attrs'][attr] != ''}
			)
			doc['attrs'] = results['args']['docs'][0]['attrs']
		return (skip_events, env, session, query, doc)