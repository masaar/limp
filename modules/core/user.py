from base_module import BaseModule
from enums import Event
from classes import ATTR, PERM, EXTN, ATTR_MOD
from config import Config

from bson import ObjectId


class User(BaseModule):
	'''`User` module provides data type and controller for users in LIMP eco-system. This module is supposed to be used for internal calls only, however it has wide-access permissions in order to allow admins, proxy modules to easily expose the methods.'''
	collection = 'users'
	attrs = {
		'name': ATTR.LOCALE(desc='Name of the user as `LOCALE`.'),
		'locale': ATTR.LOCALES(desc='Default locale of the user.'),
		'create_time': ATTR.DATETIME(desc='Python `datetime` ISO format of the doc creation.'),
		'login_time': ATTR.DATETIME(desc='Python `datetime` ISO format of the last login.'),
		'groups': ATTR.LIST(
			desc='List of `_id` for every group the user is member of.',
			list=[ATTR.ID(desc='`_id` of Group doc the user is member of.')]
		),
		'privileges': ATTR.DICT(
			desc='Privileges of the user. These privileges are always available to the user regardless of whether groups user is part of have them or not.',
			dict={'__key': ATTR.STR(), '__val': ATTR.LIST(list=[ATTR.STR()])}
		),
		'status': ATTR.LITERAL(
			desc='Status of the user to determine whether user has access to the app or not.',
			literal=['active', 'banned', 'deleted', 'disabled_password']
		),
	}
	defaults = {'login_time': None, 'status': 'active', 'groups': [], 'privileges': {}}
	unique_attrs = []
	methods = {
		'read': {
			'permissions': [
				PERM(privilege='admin'),
				PERM(privilege='read', query_mod={'_id': '$__user'}),
			]
		},
		'create': {'permissions': [PERM(privilege='admin')]},
		'update': {
			'permissions': [
				PERM(privilege='admin', doc_mod={'groups': None}),
				PERM(
					privilege='update',
					query_mod={'_id': '$__user'},
					doc_mod={'groups': None, 'privileges': None},
				),
			],
			'query_args': {'_id': ATTR.ID()},
		},
		'delete': {
			'permissions': [
				PERM(privilege='admin'),
				PERM(privilege='delete', query_mod={'_id': '$__user'}),
			],
			'query_args': {'_id': ATTR.ID()},
		},
		'read_privileges': {
			'permissions': [
				PERM(privilege='admin'),
				PERM(privilege='read', query_mod={'_id': '$__user'}),
			],
			'query_args': {'_id': ATTR.ID()},
		},
		'add_group': {
			'permissions': [PERM(privilege='admin')],
			'query_args': {'_id': ATTR.ID()},
			'doc_args': [{'group': ATTR.ID()}, {'group': ATTR.LIST(list=[ATTR.ID()])}],
		},
		'delete_group': {
			'permissions': [PERM(privilege='admin')],
			'query_args': {'_id': ATTR.ID(), 'group': ATTR.ID()},
		},
		'retrieve_file': {'permissions': [PERM(privilege='__sys')], 'get_method': True},
		'create_file': {'permissions': [PERM(privilege='__sys')]},
		'delete_file': {'permissions': [PERM(privilege='__sys')]},
	}

	async def on_read(self, results, skip_events, env, query, doc, payload):
		for i in range(len(results['docs'])):
			user = results['docs'][i]
			user['settings'] = {}
			for auth_attr in Config.user_auth_attrs:
				del user[f'{auth_attr}_hash']
			if len(Config.user_doc_settings):
				setting_results = await Config.modules['setting'].read(
					skip_events=[Event.PERM, Event.ARGS],
					env=env,
					query=[
						{'user': user._id, 'var': {'$in': Config.user_doc_settings}}
					],
				)
				if setting_results.args.count:
					user['settings'] = {
						setting_doc['var']: setting_doc['val']
						for setting_doc in setting_results.args.docs
					}
		return (results, skip_events, env, query, doc, payload)

	async def pre_create(self, skip_events, env, query, doc, payload):
		if Event.ARGS not in skip_events:
			if Config.realm:
				realm_results = await Config.modules['realm'].read(
					skip_events=[Event.PERM], env=env
				)
				realm = realm_results.args.docs[0]
				doc['groups'] = [realm.default]
			else:
				doc['groups'] = [ObjectId('f00000000000000000000013')]
		if 'settings' in doc.keys():
			payload['settings'] = doc['settings']
		return (skip_events, env, query, doc, payload)

	async def on_create(self, results, skip_events, env, query, doc, payload):
		if 'settings' in payload.keys():
			for setting in payload['settings'].keys():
				if callable(payload['settings'][setting]['val']):
					setting_val = payload['settings'][setting]['val'](
						skip_events=skip_events, env=env, query=query, doc=doc
					)
				else:
					setting_val = payload['settings'][setting]['val']
				setting_results = await Config.modules['setting'].create(
					skip_events=[Event.PERM, Event.ARGS],
					env=env,
					doc={
						'user': results['docs'][0]._id,
						'var': setting,
						'val': setting_val,
						'type': payload['settings'][setting]['type'],
					},
				)
				if setting_results.status != 200:
					return setting_results
		return (results, skip_events, env, query, doc, payload)

	async def read_privileges(self, skip_events=[], env={}, query=[], doc={}):
		# [DOC] Confirm _id is valid
		results = await self.read(
			skip_events=[Event.PERM], env=env, query=[{'_id': query['_id'][0]}]
		)
		if not results.args.count:
			return self.status(
				status=400, msg='User is invalid.', args={'code': 'INVALID_USER'}
			)
		user = results.args.docs[0]
		for group in user.groups:
			group_results = await Config.modules['group'].read(
				skip_events=[Event.PERM], env=env, query=[{'_id': group}]
			)
			group = group_results.args.docs[0]
			for privilege in group.privileges.keys():
				if privilege not in user.privileges.keys():
					user.privileges[privilege] = []
				for i in range(len(group.privileges[privilege])):
					if group.privileges[privilege][i] not in user.privileges[privilege]:
						user.privileges[privilege].append(
							group.privileges[privilege][i]
						)
		return results

	async def add_group(self, skip_events=[], env={}, query=[], doc={}):
		# [DOC] Check for list group attr
		if type(doc['group']) == list:
			for i in range(0, len(doc['group']) - 1):
				await self.add_group(
					skip_events=skip_events,
					env=env,
					query=query,
					doc={'group': doc['group'][i]},
				)
			doc['group'] = doc['group'][-1]
		# [DOC] Confirm all basic args are provided
		doc['group'] = ObjectId(doc['group'])
		# [DOC] Confirm group is valid
		results = await Config.modules['group'].read(
			skip_events=[Event.PERM], env=env, query=[{'_id': doc['group']}]
		)
		if not results.args.count:
			return self.status(
				status=400, msg='Group is invalid.', args={'code': 'INVALID_GROUP'}
			)
		# [DOC] Get user details
		results = await self.read(skip_events=[Event.PERM], env=env, query=query)
		if not results.args.count:
			return self.status(
				status=400, msg='User is invalid.', args={'code': 'INVALID_USER'}
			)
		user = results.args.docs[0]
		# [DOC] Confirm group was not added before
		if doc['group'] in user.groups:
			return self.status(
				status=400,
				msg='User is already a member of the group.',
				args={'code': 'GROUP_ADDED'},
			)
		user.groups.append(doc['group'])
		# [DOC] Update the user
		results = await self.update(
			skip_events=[Event.PERM], env=env, query=query, doc={'groups': user.groups}
		)
		return results

	async def delete_group(self, skip_events=[], env={}, query=[], doc={}):
		# [DOC] Confirm group is valid
		results = await Config.modules['group'].read(
			skip_events=[Event.PERM], env=env, query=[{'_id': query['group'][0]}]
		)
		if not results.args.count:
			return self.status(
				status=400, msg='Group is invalid.', args={'code': 'INVALID_GROUP'}
			)
		# [DOC] Get user details
		results = await self.read(
			skip_events=[Event.PERM], env=env, query=[{'_id': query['_id'][0]}]
		)
		if not results.args.count:
			return self.status(
				status=400, msg='User is invalid.', args={'code': 'INVALID_USER'}
			)
		user = results.args.docs[0]
		# [DOC] Confirm group was not added before
		if query['group'][0] not in user.groups:
			return self.status(
				status=400,
				msg='User is not a member of the group.',
				args={'code': 'GROUP_NOT_ADDED'},
			)
		# [DOC] Update the user
		results = await self.update(
			skip_events=[Event.PERM],
			env=env,
			query=[{'_id': query['_id'][0]}],
			doc={'groups': {'$remove': [query['group'][0]]}},
		)
		return results
