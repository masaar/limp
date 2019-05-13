from base_module import BaseModule

class Realm(BaseModule):
	collection = 'realms'
	attrs = {
		'user':'id',
		'name':'str',
		'admin':'id',
		'create_time':'time'
	}
	methods = {
		'read':{
			'permissions':[['read', {}, {}]]
		},
		'create':{
			'permissions':[['create', {}, {}]]
		},
		'update':{
			'permissions':[['update', {}, {'user':None, 'create_time':None}]],
			'query_args':['!_id']
		},
		'delete':{
			'permissions':[['delete', {}, {}]],
			'query_args':['!_id']
		}
	}