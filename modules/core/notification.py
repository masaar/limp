from base_module import BaseModule
from config import Config

import datetime, time

class Notification(BaseModule):
	collection = 'notifications'
	attrs = {
		'user':'id',
		'create_time':'time',
		'notify_time':'time',
		'title':'str',
		'content':'id',
		'status':('new', 'snooze', 'done')
	}
	methods = {
		'read':{
			'permissions':[['*', {'user':'$__user'}, {}]]
		},
		'create':{
			'permissions':[['create', {}, {'user':'$__user'}]]
		},
		'update':{
			'permissions':[['update', {'user':'$__user'}, {'user':None, 'create_time':None, 'title':None, 'content':None}]],
			# 'query_args':['!_id']
		},
		'delete':{
			'permissions':[['delete', {'user':'$__user'}, {}]],
			'query_args':['!_id']
		}
	}

	def pre_create(self, session, query, doc):
		if 'notify_time'not in doc.keys():
			doc['notify_time'] = datetime.datetime.fromtimestamp(time.time())
		return (session, query, doc)