from base_module import BaseModule
from event import Event
from config import Config

from bson import ObjectId

class Realm(BaseModule):
	collection = 'realms'
	attrs = {
		'user':'id',
		'name':'str',
		'default':'id',
		'create_time':'datetime'
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
			'query_args':['_id']
		},
		'delete':{
			'permissions':[['delete', {}, {}]],
			'query_args':['_id']
		}
	}

	def pre_create(self, skip_events, env, session, query, doc):
		user_results = self.modules['user'].create(skip_events=[Event.__PERM__, Event.__ARGS__, Event.__PRE__], env=env, session=session, doc={
			'username':doc['user']['username'],
			'email':doc['user']['email'],
			'name':doc['user']['name'],
			'bio':doc['user']['bio'],
			'address':doc['user']['address'],
			'postal_code':doc['user']['postal_code'],
			'phone':doc['user']['phone'],
			'website':doc['user']['website'],
			'username_hash':doc['user']['username_hash'],
			'email_hash':doc['user']['email_hash'],
			'phone_hash':doc['user']['phone_hash'],
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

		group_results = self.modules['group'].create(skip_events=[Event.__PERM__, Event.__ARGS__], env=env, session=session, doc={
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

		skip_events.append(Event.__ARGS__)
		doc['user'] = user._id
		doc['default'] = group._id
		return (skip_events, env, session, query, doc)
	
	def on_create(self, results, skip_events, env, session, query, doc):
		for doc in results['docs']:
			realm_results = self.read(skip_events=[Event.__PERM__, Event.__ARGS__], env=env, session=session, query=[{'_id':doc._id}])
			realm = realm_results.args.docs[0]
			Config._realms[realm.name] = realm
			Config._sys_docs[realm._id] = {'module':'realm'}
		return (results, skip_events, env, session, query, doc)