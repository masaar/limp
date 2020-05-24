from limp.base_module import BaseModule
from limp.enums import Event
from limp.classes import ATTR, PERM, EXTN, ATTR_MOD
from limp.utils import InvalidAttrException, validate_attr, generate_dynamic_attr
from limp.config import Config


class Setting(BaseModule):
	'''`Setting` module module provides data type and controller for settings in LIMP eco-system. This is used by `User` module tp provide additional user-wise settings. It also allows for global-typed settings.'''

	collection = 'settings'
	attrs = {
		'user': ATTR.ID(desc='`_id` of `User` doc the doc belongs to.'),
		'var': ATTR.STR(
			desc='Name of the setting. This is unique for every `user` in the module.'
		),
		'val': ATTR.ANY(desc='Value of the setting.'),
		'val_type': ATTR.DYNAMIC_ATTR(),
		'type': ATTR.LITERAL(
			desc='Type of the setting. This sets whether setting is global, or belong to user, and whether use can update it or not.',
			literal=['global', 'user', 'user_sys'],
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
				{'var': ATTR.STR(), 'type': ATTR.LITERAL(literal=['global']),},
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
					doc_mod={'var': None, 'val_type': None, 'type': None},
				),
			],
			'query_args': [
				{
					'_id': ATTR.ID(),
					'type': ATTR.LITERAL(literal=['global', 'user', 'user_sys']),
				},
				{'var': ATTR.STR(), 'type': ATTR.LITERAL(literal=['global']),},
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

	async def on_create(self, results, skip_events, env, query, doc, payload):
		if doc['type'] in ['user', 'user_sys']:
			if (
				doc['user'] == env['session'].user._id
				and doc['var'] in Config.user_doc_settings
			):
				env['session'].user[doc['var']] = doc['val']
		return (results, skip_events, env, query, doc, payload)

	async def pre_update(self, skip_events, env, query, doc, payload):
		setting_results = await self.read(
			skip_events=[Event.PERM], env=env, query=query
		)
		if not setting_results.args.count:
			return self.status(
				status=400, msg='Invalid Setting doc', args={'code': 'INVALID_SETTING'}
			)
		setting = setting_results.args.docs[0]
		# [DOC] Attempt to validate val against Setting val_type
		try:
			setting_val_type, _ = generate_dynamic_attr(dynamic_attr=setting.val_type)
			doc['val'] = await validate_attr(
				attr_name=setting.var, attr_type=setting_val_type, attr_val=doc['val']
			)
		except Exception as e:
			return self.status(
				status=400,
				msg=f'Invalid value for for Setting doc of type \'{type(doc["val"])}\' with required type \'{setting_val_type}\'',
				args={'code': 'INVALID_ATTR'},
			)
		return (skip_events, env, query, doc, payload)

	async def on_update(self, results, skip_events, env, query, doc, payload):
		if (
			query['type'][0] in ['user', 'user_sys']
			and query['user'][0] == env['session'].user._id
			and query['var'][0] in Config.user_doc_settings
		):
			if type(doc['val']) == dict and '$add' in doc['val'].keys():
				env['session'].user[query['var'][0]] += doc['val']['$add']
			elif type(doc['val']) == dict and '$multiply' in doc['val'].keys():
				env['session'].user[query['var'][0]] *= doc['val']['$multiply']
			elif type(doc['val']) == dict and '$append' in doc['val'].keys():
				env['session'].user[query['var'][0]].append(doc['val']['$append'])
			elif type(doc['val']) == dict and '$remove' in doc['val'].keys():
				env['session'].user[query['var'][0]].remove(doc['val']['$remove'])
			else:
				env['session'].user[query['var'][0]] = doc['val']
		return (results, skip_events, env, query, doc, payload)
