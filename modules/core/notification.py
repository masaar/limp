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
			'permissions':[['create', {}, {}]]
		},
		'update':{
			'permissions':[['update', {'user':'$__user'}, {'user':None, 'create_time':None, 'title':None, 'content':None}]]
		},
		'delete':{
			'permissions':[['delete', {'user':'$__user'}, {}]],
			'query_args':['_id']
		}
	}

	def pre_create(self, skip_events, env, session, query, doc):
		if 'notify_time'not in doc.keys():
			doc['notify_time'] = datetime.datetime.fromtimestamp(time.time())
		return (skip_events, env, session, query, doc)