from base_module import BaseModule
from event import Event

class Setting(BaseModule):
	collection = 'settings'
	attrs = {
		'var':'str',
		'val':'any',
		'type':('global', 'user'),
		'user':'id'
	}
	optional_attrs = ['user']
	extns = {
		'user':['user', ['name', 'email']]
	}
	methods = {
		'read':{
			'permissions':[['admin', {'$limit':1}, {}], ['read', {'user':'$__user', '$limit':1}, {}]],
			'query_args':['^_id', '^var']
		},
		'get_setting':{
			'permissions':[['admin', {'$limit':1}, {}], ['read', {'user':'$__user', '$limit':1}, {}]],
			'query_args':['!var']
		},
		'create':{
			'permissions':[['admin', {'$limit':1}, {}], ['create', {}, {'type':'user', 'user':'$__user', '$limit':1}]]
		},
		'update':{
			'permissions':[['admin', {'$limit':1}, {}], ['update', {'type':'user', 'user':'$__user', '$limit':1}, {'type':None, 'user':None}]],
			'query_args':['!var'],
			'doc_args':['!val']
		},
		'delete':{
			'permissions':[['admin', {'$limit':1}, {}]],
			'query_args':['!var']
		},
		'retrieve_file':{
			'permissions':[['*', {'type':'global'}, {}]],
			'query_args':['!_id', '!var'],
			'get_method':True
		}
	}

	def pre_create(self, env, session, query, doc):
		if type(doc['val']) == list and doc['val'].__len__() == 1 and 'content' in doc['val'][0].keys():
			doc['val'] = doc['val'][0]
		return (env, session, query, doc)
	
	def pre_update(self, env, session, query, doc):
		if type(doc['val']) == list and doc['val'].__len__() == 1 and 'content' in doc['val'][0].keys():
			doc['val'] = doc['val'][0]
		return (env, session, query, doc)

	def get_setting(self, skip_events=[], env={}, session=None, query={}, doc={}, files={}):
		results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=query)
		if not results.args.count:
			return False
		else:
			return results.args.docs[0].val