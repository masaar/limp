from base_module import BaseModule
from enums import Event
from classes import ATTR, PERM, EXTN, ATTR_MOD
from utils import InvalidAttrException
from config import Config


class Setting(BaseModule):
	collection = 'settings'
	attrs = {
		'user': ATTR.ID(),
		'var': ATTR.STR(),
		'val': ATTR.ANY(),
		'type': ATTR.LITERAL(literal=['global', 'user', 'user_sys']),
	}
	diff = True
	unique_attrs = [('user', 'var')]
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
							default=InvalidAttrException(
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
					'type': ATTR.LITERAL(literal=['global', 'user', 'user_sys']),
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
			'query_args': {'var': ATTR.STR()},
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

	async def pre_update(self, skip_events, env, query, doc, payload):
		if (
			type(doc['val']) == list
			and len(doc['val']) == 1
			and type(doc['val'][0]) == dict
			and 'content' in doc['val'][0].keys()
		):
			doc['val'] = doc['val'][0]
		return (skip_events, env, query, doc, payload)
