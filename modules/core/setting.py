from base_module import BaseModule
from event import Event

class Setting(BaseModule):
	collection = 'settings'
	attrs = {
		'user':'id',
		'var':'str',
		'val':'any',
		'type':{'global', 'user'}
	}
	extns = {
		'user':['user', ['name', 'email']]
	}
	methods = {
		'read':{
			'permissions':[['admin', {'$limit':1}, {}], ['read', {'user':'$__user', '$limit':1}, {}]],
			'query_args':[{'_id':'id'}, {'var':'str'}]
		},
		'create':{
			'permissions':[['admin', {}, {}], ['create', {}, {'type':'user'}]]
		},
		'update':{
			'permissions':[['admin', {'$limit':1}, {}], ['update', {'type':'user', 'user':'$__user', '$limit':1}, {'type':None, 'user':None}]],
			'query_args':{'var':'str'},
			'doc_args':{'val':'any'}
		},
		'delete':{
			'permissions':[['admin', {'$limit':1}, {}]],
			'query_args':{'var':'str'}
		},
		'retrieve_file':{
			'permissions':[['*', {'type':'global'}, {}]],
			'get_method':True
		}
	}

	def pre_create(self, skip_events, env, query, doc):
		if type(doc['val']) == list and doc['val'].__len__() == 1 and type(doc['val'][0]) == dict and 'content' in doc['val'][0].keys():
			doc['val'] = doc['val'][0]
		return (skip_events, env, query, doc)
	
	def pre_update(self, skip_events, env, query, doc):
		if type(doc['val']) == list and doc['val'].__len__() == 1 and type(doc['val'][0]) == dict and 'content' in doc['val'][0].keys():
			doc['val'] = doc['val'][0]
		return (skip_events, env, query, doc)