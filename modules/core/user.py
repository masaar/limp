from base_module import BaseModule
from enums import Event
from config import Config

from bson import ObjectId

class User(BaseModule):
	collection = 'users'
	attrs = {
		'name':'locale',
		'locale':'locales',
		'create_time':'datetime',
		'login_time':'datetime',
		'groups':['id'],
		'privileges':'privileges',
		'status':{'active', 'banned', 'deleted', 'disabled_password'},
		'attrs':'attrs'
	}
	defaults = {'login_time':None, 'status':'active', 'attrs':{}, 'groups':[], 'privileges':{}}
	unique_attrs = []
	methods = {
		'read':{
			'permissions':[['admin', {}, {}], ['read', {'_id':'$__user'}, {}]]
		},
		'create':{
			'permissions':[['admin', {}, {}]]
		},
		'update':{
			'permissions':[['admin', {}, {'groups':None}], ['update', {'_id':'$__user'}, {'groups':None, 'privileges':None}]],
			'query_args':{'_id':'id'}
		},
		'delete':{
			'permissions':[['admin', {}, {}], ['delete', {'_id':'$__user'}, {}]],
			'query_args':{'_id':'id'}
		},
		'read_privileges':{
			'permissions':[['admin', {}, {}], ['read', {'_id':'$__user'}, {}]],
			'query_args':{'_id':'id'}
		},
		'add_group':{
			'permissions':[['admin', {}, {}]],
			'query_args':{'_id':'id'},
			'doc_args':[{'group':('id', ['id'])}]
		},
		'delete_group':{
			'permissions':[['admin', {}, {}]],
			'query_args':{'_id':'id', 'group':'id'}
		},
		'retrieve_file':{
			'permissions':[['__sys', {}, {}]],
			'get_method':True
		},
		'create_file':{
			'permissions':[['__sys', {}, {}]]
		},
		'delete_file':{
			'permissions':[['__sys', {}, {}]]
		}
	}

	async def on_read(self, results, skip_events, env, query, doc):
		for i in range(0, len(results['docs'])):
			user = results['docs'][i]
			for attr in self.unique_attrs:
				del user[f'{attr}_hash']
			# [DOC] Attempt to extend attrs values if __EXTN__ event is not skipped
			if Event.__EXTN__ not in skip_events:
				for attr in user.attrs.keys():
					if type(user.attrs[attr]) == dict and '__extn' in user.attrs[attr].keys():
						extn = user.attrs[attr]['__extn']
						if type(extn[1]) == list:
							if not len(extn[1]):
								# [DOC] This is placeholder __extn attr with no value. Set as empty array
								user.attrs[attr] = []
								continue
							extn_query = [{'_id':{'$in':extn[1]}}]
						else:
							if not extn[1]:
								# [DOC] This is placeholder __extn attr with no value. Set as None
								user.attrs[attr] = None
								continue
							extn_query = [{'_id':extn[1]}]
						if extn[2] != ['*']:
							extn_query.append({'$attrs':extn[2]})
						extn_results = await self.modules[extn[0]].read(skip_events=[Event.__PERM__, Event.__EXTN__], env=env, query=extn_query)
						if not extn_results.args.count:
							user.attrs[attr] = None
						else:
							if type(extn[1]) == list:
								user.attrs[attr] = extn_results.args.docs
							else:
								user.attrs[attr] = extn_results.args.docs[0]
		return (results, skip_events, env, query, doc)
	
	async def pre_create(self, skip_events, env, query, doc):
		if Event.__ARGS__ not in skip_events:
			if Config.realm:
				realm_results = await self.modules['realm'].read(skip_events=[Event.__PERM__], env=env)
				realm = realm_results.args.docs[0]
				doc['groups'] = [realm.default]
			else:
				doc['groups'] = [ObjectId('f00000000000000000000013')]
		return (skip_events, env, query, doc)
	
	async def pre_update(self, skip_events, env, query, doc):
		# [DOC] Make sure no attrs overwriting would happen
		if 'attrs' in doc.keys():
			attrs = {}
			for attr in doc['attrs'].keys():
				if attr in ['$add', '$push', '$push_unique', '$pull']:
					attrs[attr] = doc['attrs'][attr]
				else:
					attrs[f'attrs.{attr}'] = doc['attrs'][attr]
		return (skip_events, env, query, doc)

	async def read_privileges(self, skip_events=[], env={}, query=[], doc={}):
		# [DOC] Confirm _id is valid
		results = await self.read(skip_events=[Event.__PERM__], env=env, query=[{'_id':query['_id'][0]}])
		if not results.args.count:
			return {
				'status':400,
				'msg':'User is invalid.',
				'args':{'code':'CORE_USER_INVALID_USER'}
			}
		user = results.args.docs[0]
		for group in user.groups:
			group_results = await self.modules['group'].read(skip_events=[Event.__PERM__], env=env, query=[{'_id':group}])
			group = group_results.args.docs[0]
			for privilege in group.privileges.keys():
				if privilege not in user.privileges.keys(): user.privileges[privilege] = []
				for i in range(0, len(group.privileges[privilege])):
					if group.privileges[privilege][i] not in user.privileges[privilege]:
						user.privileges[privilege].append(group.privileges[privilege][i])
		return results
	
	async def add_group(self, skip_events=[], env={}, query=[], doc={}):
		# [DOC] Check for list group attr
		if type(doc['group']) == list:
			for i in range(0, len(doc['group'])-1):
				await self.add_group(skip_events=skip_events, env=env, query=query, doc={'group':doc['group'][i]})
			doc['group'] = doc['group'][-1]
		# [DOC] Confirm all basic args are provided
		doc['group'] = ObjectId(doc['group'])
		# [DOC] Confirm group is valid
		results = await self.modules['group'].read(skip_events=[Event.__PERM__], env=env, query=[{'_id':doc['group']}])
		if not results.args.count:
			return {
				'status':400,
				'msg':'Group is invalid.',
				'args':{'code':'CORE_USER_INVALID_GROUP'}
			}
		# [DOC] Get user details
		results = await self.read(skip_events=[Event.__PERM__], env=env, query=query)
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
		results = await self.update(skip_events=[Event.__PERM__], env=env, query=query, doc={'groups':user.groups})
		return results
	
	async def delete_group(self, skip_events=[], env={}, query=[], doc={}):
		# [DOC] Confirm group is valid
		results = await self.modules['group'].read(skip_events=[Event.__PERM__], env=env, query=[{'_id':query['group'][0]}])
		if not results.args.count:
			return {
				'status':400,
				'msg':'Group is invalid.',
				'args':{'code':'CORE_USER_INVALID_GROUP'}
			}
		# [DOC] Get user details
		results = await self.read(skip_events=[Event.__PERM__], env=env, query=[{
			'_id':query['_id'][0]
		}])
		if not results.args.count:
			return {
				'status':400,
				'msg':'User is invalid.',
				'args':{'code':'CORE_USER_INVALID_USER'}
			}
		user = results.args.docs[0]
		# [DOC] Confirm group was not added before
		if query['group'][0] not in user.groups:
			return {
				'status':400,
				'msg':'User is not a member of the group.',
				'args':{'code':'CORE_USER_GROUP_NOT_ADDED'}
			}
		# [DOC] Update the user
		results = await self.update(skip_events=[Event.__PERM__], env=env, query=[{
			'_id':query['_id'][0]
		}], doc={
			'groups':{'$pull':[query['group'][0]]}
		})
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
			'permissions':[['admin', {}, {}], ['update', {'user':'$__user'}, {'privileges':None}]],
			'query_args':{'_id':'id'}
		},
		'delete':{
			'permissions':[['admin', {}, {}], ['delete', {'user':'$__user'}, {}]],
			'query_args':{'_id':'id'}
		}
	}

	async def pre_create(self, skip_events, env, query, doc):
		return (skip_events, env, query, doc)

	async def pre_update(self, skip_events, env, query, doc):
		# [DOC] Make sure no attrs overwriting would happen
		if 'attrs' in doc.keys():
			results = await self.read(skip_events=[Event.__PERM__], env=env, query=query)
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
		return (skip_events, env, query, doc)