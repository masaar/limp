from base_module import BaseModule
from enums import Event
from classes import ATTR, PERM, EXTN, ATTR_MOD
from utils import InvalidAttrException
from config import Config


class Setting(BaseModule):
	'''`Setting` module module provides data type and controller for settings in LIMP eco-system. This is used by `User` module tp provide additional user-wise settings. It also allows for global-typed settings.'''
	collection = 'settings'
	attrs = {
		'user': ATTR.ID(desc='`_id` of `User` doc the doc belongs to.'),
		'var': ATTR.STR(desc='Name of the setting. This is unique for every `user` in the module.'),
		'val': ATTR.ANY(desc='Value of the setting.'),
		'type': ATTR.LITERAL(
			desc='Type of the setting. This sets whether setting is global, or belong to user, and whether use can update it or not.',
			literal=['global', 'user', 'user_sys']
		),
	}
	diff = True
	unique_attrs = [('user', 'var', 'type')]
	extns = {
		'val': ATTR_MOD(
			condition=lambda skip_events, env, query, doc, scope: type(scope) == dict
			and '__extn' in scope.keys(),
			default=lambda skip_events, env, query, doc, scope: {
				'__extn': EXTN(
					module=scope['__extn']['__module'],
					attrs=scope['__extn']['__attrs'],
					force=scope['__extn']['__force'],
				),
				'__val': scope['__extn']['__val'],
			},
		)
	}
	methods = {
		'read': {
			'permissions': [
				PERM(privilege='admin', query_mod={'$limit': 1}),
				PERM(
					privilege='read',
					query_mod={
						'user': '$__user',
						'type': ATTR_MOD(
							condition=lambda skip_events, env, query, doc: 'type'
							in doc.keys()
							and doc['type'] == 'user_sys',
							default=lambda skip_events, env, query, doc: InvalidAttrException(
								attr_name='type',
								attr_type=ATTR.LITERAL(literal=['global', 'user']),
								val_type=str,
							),
						),
						'$limit': 1,
					},
				),
			],
			'query_args': [
				{
					'_id': ATTR.ID(),
					'type': ATTR.LITERAL(literal=['global', 'user', 'user_sys']),
				},
				{
					'var': ATTR.STR(),
					'type': ATTR.LITERAL(literal=['global']),
				},
				{
					'var': ATTR.STR(),
					'user': ATTR.ID(),
					'type': ATTR.LITERAL(literal=['user', 'user_sys']),
				},
			],
		},
		'create': {
			'permissions': [
				PERM(privilege='admin'),
				PERM(privilege='create', doc_mod={'type': 'user'}),
			]
		},
		'update': {
			'permissions': [
				PERM(privilege='admin', query_mod={'$limit': 1}),
				PERM(
					privilege='update',
					query_mod={'type': 'user', 'user': '$__user', '$limit': 1},
					doc_mod={'type': None},
				),
			],
			'query_args': [
				{
					'_id': ATTR.ID(),
					'type': ATTR.LITERAL(literal=['global', 'user', 'user_sys']),
				},
				{
					'var': ATTR.STR(),
					'type': ATTR.LITERAL(literal=['global']),
				},
				{
					'var': ATTR.STR(),
					'user': ATTR.ID(),
					'type': ATTR.LITERAL(literal=['user', 'user_sys']),
				},
			],
			'doc_args': {'val': ATTR.ANY()},
		},
		'delete': {
			'permissions': [PERM(privilege='admin', query_mod={'$limit': 1})],
			'query_args': [{'_id': ATTR.ID()}, {'var': ATTR.STR()}],
		},
		'retrieve_file': {
			'permissions': [PERM(privilege='*', query_mod={'type': 'global'})],
			'get_method': True,
		},
	}

	async def pre_create(self, skip_events, env, query, doc, payload):
		if (
			type(doc['val']) == list
			and len(doc['val']) == 1
			and type(doc['val'][0]) == dict
			and 'content' in doc['val'][0].keys()
		):
			doc['val'] = doc['val'][0]
		return (skip_events, env, query, doc, payload)
	
	async def on_create(self, results, skip_events, env, query, doc, payload):
		if doc['type'] in ['user', 'user_sys']:
			if doc['user'] == env['session'].user._id:
				env['session'].user.settings[doc['var']] = doc['val']
		return (results, skip_events, env, query, doc, payload)

	async def pre_update(self, skip_events, env, query, doc, payload):
		if (
			type(doc['val']) == list
			and len(doc['val']) == 1
			and type(doc['val'][0]) == dict
			and 'content' in doc['val'][0].keys()
		):
			doc['val'] = doc['val'][0]
		return (skip_events, env, query, doc, payload)
	
	async def on_update(self, results, skip_events, env, query, doc, payload):
		if query['type'][0] in ['user', 'user_sys']:
			if query['user'][0] == env['session'].user._id:
				if type(doc['val']) == dict and '$add' in doc['val'].keys():
					env['session'].user.settings[query['var'][0]] += doc['val']['$add']
				elif type(doc['val']) == dict and '$multiply' in doc['val'].keys():
					env['session'].user.settings[query['var'][0]] *= doc['val']['$multiply']
				elif type(doc['val']) == dict and '$append' in doc['val'].keys():
					env['session'].user.settings[query['var'][0]].append(doc['val']['$append'])
				elif type(doc['val']) == dict and '$remove' in doc['val'].keys():
					env['session'].user.settings[query['var'][0]].remove(doc['val']['$remove'])
				else:
					env['session'].user.settings[query['var'][0]] = doc['val']
		return (results, skip_events, env, query, doc, payload)