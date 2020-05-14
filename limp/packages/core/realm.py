from limp.base_module import BaseModule
from limp.enums import Event
from limp.classes import ATTR, PERM, EXTN
from limp.config import Config

from bson import ObjectId


class Realm(BaseModule):
	'''`Realm` module module provides data type and controller for Realm Mode in LIMP eco-system.'''

	collection = 'realms'
	attrs = {
		'user': ATTR.ID(
			desc='`_id` of `User` doc the doc belongs to. This is also the ADMIN of the realm.'
		),
		'name': ATTR.STR(
			desc='Name of the realm. This is both readable as well as unique name.'
		),
		'default': ATTR.ID(
			desc='`_id` of `Group` doc that serves as `DEFAULT` group of the realm.'
		),
		'create_time': ATTR.DATETIME(
			desc='Python `datetime` ISO format of the doc creation.'
		),
	}
	methods = {
		'read': {'permissions': [PERM(privilege='read')]},
		'create': {'permissions': [PERM(privilege='create')]},
		'update': {
			'permissions': [
				PERM(privilege='update', doc_mod={'user': None, 'create_time': None})
			],
			'query_args': {'_id': ATTR.ID()},
		},
		'delete': {
			'permissions': [PERM(privilege='delete')],
			'query_args': {'_id': ATTR.ID()},
		},
	}

	async def pre_create(self, skip_events, env, query, doc, payload):
		user_doc = {attr: doc['user'][attr] for attr in Config.user_attrs}
		user_doc.update(
			{
				'locale': Config.locale,
				'groups': [],
				'privileges': {'*': '*'},
				'status': 'active',
				'attrs': {},
				'realm': doc['name'],
			}
		)
		user_results = await Config.modules['user'].create(
			skip_events=[Event.PERM, Event.ARGS, Event.PRE], env=env, doc=user_doc
		)
		if user_results.status != 200:
			return user_results
		user = user_results.args.docs[0]

		group_results = await Config.modules['group'].create(
			skip_events=[Event.PERM, Event.ARGS],
			env=env,
			doc={
				'user': user._id,
				'name': {locale: '__DEFAULT' for locale in Config.locales},
				'bio': {locale: '__DEFAULT' for locale in Config.locales},
				'privileges': Config.default_privileges,
				'attrs': {},
				'realm': doc['name'],
			},
		)
		if group_results.status != 200:
			return group_results
		group = group_results.args.docs[0]

		skip_events.append(Event.ARGS)
		doc['user'] = user._id
		doc['default'] = group._id
		return (skip_events, env, query, doc, payload)

	async def on_create(self, results, skip_events, env, query, doc, payload):
		for doc in results['docs']:
			realm_results = await self.read(
				skip_events=[Event.PERM, Event.ARGS], env=env, query=[{'_id': doc._id}]
			)
			realm = realm_results.args.docs[0]
			Config._realms[realm.name] = realm
			Config._sys_docs[realm._id] = {'module': 'realm'}
		return (results, skip_events, env, query, doc, payload)
