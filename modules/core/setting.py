from base_module import BaseModule
from event import Event

class Setting(BaseModule):
	collection = 'settings'
	attrs = {
		'var':'str',
		'val':'any',
		'type':('global', 'user'),
		'user':'id',
		# 'diff':'diff'
	}
	optional_attrs = ['user']
	extns = {
		'user':['user', ['name', 'email']]
	}
	methods = {
		'read':{
			'permissions':[['admin', {}, {}], ['read', {'user':'$__user'}, {}]]
		},
		'create':{
			'permissions':[['admin', {}, {}], ['create', {}, {'type':'user', 'user':'$__user'}]]
		},
		'update':{
			'permissions':[['admin', {}, {}], ['update', {'type':'user', 'user':'$__user'}, {'type':None, 'user':None}]],
			'query_args':['!var']
		},
		'delete':{
			'permissions':[['admin', {}, {}]],
			'query_args':['!var']
		}
	}