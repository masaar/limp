from base_module import BaseModule
from event import Event

class Setting(BaseModule):
	collection = 'settings'
	attrs = {
		'user':'id',
		'var':'str',
		'val':'any',
		'type':('global', 'user')
	}
	optional_attrs = ['user']
	extns = {
		'user':['user', ['name', 'email']]
	}
	methods = {
		'read':{
			'permissions':[['admin', {'$limit':1}, {}], ['read', {'user':'$__user', '$limit':1}, {}]],
			'query_args':[('_id', 'var')]
		},
		'get_setting':{
			'permissions':[['admin', {'$limit':1}, {}], ['read', {'user':'$__user', '$limit':1}, {}]],
			'query_args':['var']
		},
		'create':{
			'permissions':[['admin', {'$limit':1}, {}], ['create', {}, {'type':'user', 'user':'$__user', '$limit':1}]]
		},
		'update':{
			'permissions':[['admin', {'$limit':1}, {}], ['update', {'type':'user', 'user':'$__user', '$limit':1}, {'type':None, 'user':None}]],
			'query_args':['var'],
			'doc_args':['val']
		},
		'delete':{
			'permissions':[['admin', {'$limit':1}, {}]],
			'query_args':['var']
		},
		'retrieve_file':{
			'permissions':[['*', {'type':'global'}, {}]],
			'query_args':['_id', 'var'],
			'get_method':True
		}
	}

	def pre_create(self, skip_events, env, session, query, doc):
		if type(doc['val']) == list and doc['val'].__len__() == 1 and type(doc['val'][0]) == dict and 'content' in doc['val'][0].keys():
			doc['val'] = doc['val'][0]
		return (skip_events, env, session, query, doc)
	
	def pre_update(self, skip_events, env, session, query, doc):
		if type(doc['val']) == list and doc['val'].__len__() == 1 and type(doc['val'][0]) == dict and 'content' in doc['val'][0].keys():
			doc['val'] = doc['val'][0]
		return (skip_events, env, session, query, doc)

	def get_setting(self, skip_events=[], env={}, session=None, query={}, doc={}, files={}):
		results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=query)
		if not results.args.count:
			return False
		else:
			return results.args.docs[0].val