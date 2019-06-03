from base_module import BaseModule
from event import Event
from config import Config

from bson import ObjectId

class Realm(BaseModule):
	collection = 'realms'
	attrs = {
		'user':'id',
		'name':'str',
		'admin':'id',
		'default':'id',
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

	def pre_create(self, skip_events, env, session, query, doc):
		user_results = self.modules['user'].methods['create'](skip_events=[Event.__PERM__, Event.__ARGS__, Event.__PRE__], env=env, session=session, doc={
			'username':doc['admin']['email'],
			'email':doc['admin']['email'],
			'name':doc['admin']['name'],
			'bio':doc['admin']['bio'],
			'address':doc['admin']['address'],
			'postal_code':doc['admin']['postal_code'],
			'phone':doc['admin']['phone'],
			'website':doc['admin']['website'],
			'username_hash':doc['admin']['username_hash'],
			'email_hash':doc['admin']['email_hash'],
			'phone_hash':doc['admin']['phone_hash'],
			'locale':Config.locale,
			'groups':[],
			'privileges':{'*':'*'},
			'status':'active',
			'attrs':{},
			'realm':doc['name']
		})
		if user_results.status != 200:
			return user_results
		user = user_results.args.docs[0]

		group_results = self.modules['group'].methods['create'](skip_events=[Event.__PERM__], env=env, session=session, doc={
			'_id':ObjectId('f00000000000000000000013'),
			'user':user._id,
			'name':{
				locale:'__DEFAULT' for locale in Config.locales
			},
			'bio':{
				locale:'__DEFAULT' for locale in Config.locales
			},
			'privileges':Config.default_privileges,
			'attrs':{},
			'realm':doc['name']
		})
		if group_results.status != 200:
			return group_results
		group = group_results.args.docs[0]

		doc['admin'] = user._id
		doc['default'] = group._id
		return (skip_events, env, session, query, doc)