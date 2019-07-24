from base_module import BaseModule
from event import Event
from config import Config

from bson import ObjectId

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
		'create_time':'datetime',
		'login_time':'datetime',
		'groups':['id'],
		'privileges':'privileges',
		'username_hash':'str',
		'email_hash':'str',
		'phone_hash':'str',
		'status':('active', 'banned', 'deleted', 'disabled_password'),
		'attrs':'attrs'
	}
	defaults = {'bio':{locale:'' for locale in Config.locales}, 'website':None, 'locale':Config.locale, 'login_time':None, 'status':'active', 'attrs':{}, 'groups':[], 'privileges':{}}
	unique_attrs = ['username', 'email', 'phone']
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
			# [DOC] Attempt to extend attrs values if __EXTN__ event is not skipped
			if Event.__EXTN__ not in skip_events:
				for attr in user.attrs.keys():
					if type(user.attrs[attr]) == dict and '__extn' in user.attrs[attr].keys():
						extn = user.attrs[attr]['__extn']
						if type(extn[1]) == list:
							if not extn[1].__len__():
								# [DOC] This is placeholder __extn attr with no value. Skip.
								continue
							extn_query = [{'_id':{'$in':extn[1]}}]
						else:
							if not extn[1]:
								# [DOC] This is placeholder __extn attr with no value. Skip.
								continue
							extn_query = [{'_id':extn[1]}]
						if extn[2] != ['*']:
							extn_query.append({'$attrs':extn[2]})
						extn_results = self.modules[extn[0]].read(skip_events=[Event.__PERM__, Event.__EXTN__], env=env, session=session, query=extn_query)
						if not extn_results.args.count:
							user.attrs[attr] = None
						else:
							user.attrs[attr] = extn_results.args.docs[0]
		return (results, skip_events, env, session, query, doc)
	
	def pre_create(self, skip_events, env, session, query, doc):
		if Event.__ARGS__ not in skip_events:
			if Config.realm:
				realm_results = self.modules['realm'].read(skip_events=[Event.__PERM__], env=env, session=session)
				realm = realm_results.args.docs[0]
				doc['groups'] = [realm.default]
			else:
				doc['groups'] = [ObjectId('f00000000000000000000013')]
		return (skip_events, env, session, query, doc)
	
	def pre_update(self, skip_events, env, session, query, doc):
		# [DOC] Make sure no attrs overwriting would happen
		if 'attrs' in doc.keys():
			attrs = {}
			for attr in doc['attrs'].keys():
				if attr in ['$add', '$push', '$push_unique', '$pull']:
					attrs[attr] = doc['attrs'][attr]
				else:
					attrs[f'attrs.{attr}'] = doc['attrs'][attr]
		return (skip_events, env, session, query, doc)

	def read_privileges(self, skip_events=[], env={}, session=None, query=[], doc={}):
		# [DOC] Confirm _id is valid
		results = self.read(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':query['_id'][0]}])
		if not results.args.count:
			return {
				'status':400,
				'msg':'User is invalid.',
				'args':{'code':'CORE_USER_INVALID_USER'}
			}
		user = results.args.docs[0]
		for group in user.groups:
			group_results = self.modules['group'].read(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':group}])
			group = group_results.args.docs[0]
			for privilege in group.privileges.keys():
				if privilege not in user.privileges.keys(): user.privileges[privilege] = []
				for i in range(0, group.privileges[privilege].__len__()):
					if group.privileges[privilege][i] not in user.privileges[privilege]:
						user.privileges[privilege].append(group.privileges[privilege][i])
		return results
	
	def add_group(self, skip_events=[], env={}, session=None, query=[], doc={}):
		# [DOC] Check for list group attr
		if type(doc['group']) == list:
			for i in range(0, doc['group'].__len__()-1):
				self.add_group(skip_events=skip_events, env=env, session=session, query=query, doc={'group':doc['group'][i]})
			doc['group'] = doc['group'][-1]
		# [DOC] Confirm all basic args are provided
		doc['group'] = ObjectId(doc['group'])
		# [DOC] Confirm group is valid
		results = self.modules['group'].read(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':doc['group']}])
		if not results.args.count:
			return {
				'status':400,
				'msg':'Group is invalid.',
				'args':{'code':'CORE_USER_INVALID_GROUP'}
			}
		# [DOC] Get user details
		results = self.read(skip_events=[Event.__PERM__], env=env, session=session, query=query)
		if not results.args.count:
			return {
				'status':400,
				'msg':'User is invalid.',
				'args':{'code':'CORE_USER_INVALID_USER'}
			}
		user = results.args.docs[0]
		# [DOC] Confirm group was not added before
		if doc['group'] in user.groups:
			return {
				'status':400,
				'msg':'User is already a member of the group.',
				'args':{'code':'CORE_USER_GROUP_ADDED'}
			}
		user.groups.append(doc['group'])
		# [DOC] Update the user
		results = self.update(skip_events=[Event.__PERM__], env=env, session=session, query=query, doc={'groups':user.groups})
		return results
	
	def delete_group(self, skip_events=[], env={}, session=None, query=[], doc={}):
		# [DOC] Confirm all basic args are provided
		doc['group'] = ObjectId(doc['group'])
		# [DOC] Confirm group is valid
		results = self.modules['group'].read(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':doc['group']}])
		if not results.args.count:
			return {
				'status':400,
				'msg':'Group is invalid.',
				'args':{'code':'CORE_USER_INVALID_GROUP'}
			}
		# [DOC] Get user details
		results = self.read(skip_events=[Event.__PERM__], env=env, session=session, query=query)
		if not results.args.count:
			return {
				'status':400,
				'msg':'User is invalid.',
				'args':{'code':'CORE_USER_INVALID_USER'}
			}
		user = results.args.docs[0]
		# [DOC] Confirm group was not added before
		if doc['group'] not in user.groups:
			return {
				'status':400,
				'msg':'User is not a member of the group.',
				'args':{'code':'CORE_USER_GROUP_NOT_ADDED'}
			}
		user.groups = [group for group in user.groups if str(group) != str(doc['group'])]
		# [DOC] Update the user
		results = self.update(skip_events=[Event.__PERM__], env=env, session=session, query=query, doc={'groups':user.groups})
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
	defaults = {'bio':{locale:'' for locale in Config.locales}, 'privileges':{}, 'attrs':{}}
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
		return (skip_events, env, session, query, doc)

	def pre_update(self, skip_events, env, session, query, doc):
		# [DOC] Make sure no attrs overwriting would happen
		if 'attrs' in doc.keys():
			results = self.read(skip_events=[Event.__PERM__], env=env, session=session, query=query)
			if not results.args.count:
				return {
					'status':400,
					'msg':'Group is invalid.',
					'args':{'code':'CORE_GROUP_INVALID_GROUP'}
				}
			if results.args.count > 1:
				return {
					'status':400,
					'msg':'Updating group attrs can be done only to individual groups.',
					'args':{'code':'CORE_GROUP_MULTI_ATTRS_UPDATE'}
				}
			results.args.docs[0]['attrs'].update(
				{attr:doc['attrs'][attr] for attr in doc['attrs'].keys() if doc['attrs'][attr] != None and doc['attrs'][attr] != ''}
			)
			doc['attrs'] = results.args.docs[0]['attrs']
		return (skip_events, env, session, query, doc)