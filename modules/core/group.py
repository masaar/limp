from base_module import BaseModule
from classes import ATTR, PERM
from config import Config
from enums import Event


class Group(BaseModule):
	collection = 'groups'
	attrs = {
		'user': ATTR.ID(),
		'name': ATTR.LOCALE(),
		'desc': ATTR.LOCALE(),
		'privileges': ATTR.DICT(
			dict={'__key': ATTR.STR(), '__val': ATTR.LIST(list=[ATTR.STR()])}
		),
		'settings': ATTR.DICT(dict={'__key': ATTR.STR(), '__val': ATTR.ANY()}),
	}
	defaults = {
		'desc': {locale: '' for locale in Config.locales},
		'privileges': {},
		'settings': {},
	}
	methods = {
		'read': {'permissions': [PERM(privilege='admin')]},
		'create': {'permissions': [PERM(privilege='admin')]},
		'update': {
			'permissions': [
				PERM(privilege='admin'),
				PERM(
					privilege='update',
					query_mod={'user': '$__user'},
					doc_mod={'privileges': None},
				),
			],
			'query_args': {'_id': ATTR.ID()},
		},
		'delete': {
			'permissions': [
				PERM(privilege='admin'),
				PERM(privilege='delete', query_mod={'user': '$__user'}),
			],
			'query_args': {'_id': ATTR.ID()},
		},
	}

	async def pre_create(self, skip_events, env, query, doc, payload):
		return (skip_events, env, query, doc, payload)

	async def pre_update(self, skip_events, env, query, doc, payload):
		# [DOC] Make sure no attrs overwriting would happen
		if 'attrs' in doc.keys():
			results = await self.read(skip_events=[Event.PERM], env=env, query=query)
			if not results.args.count:
				return self.status(
					status=400, msg='Group is invalid.', args={'code': 'INVALID_GROUP'}
				)
			if results.args.count > 1:
				return self.status(
					status=400,
					msg='Updating group attrs can be done only to individual groups.',
					args={'code': 'MULTI_ATTRS_UPDATE'},
				)
			results.args.docs[0]['attrs'].update(
				{
					attr: doc['attrs'][attr]
					for attr in doc['attrs'].keys()
					if doc['attrs'][attr] != None and doc['attrs'][attr] != ''
				}
			)
			doc['attrs'] = results.args.docs[0]['attrs']
		return (skip_events, env, query, doc, payload)
