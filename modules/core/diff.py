from base_module import BaseModule
from enums import Event
from classes import ATTR, PERM
from config import Config

from bson import ObjectId


class Diff(BaseModule):
	collection = 'diff'
	attrs = {
		'user': ATTR.ID(),
		'module': ATTR.STR(),
		'doc': ATTR.ID(),
		'vars': ATTR.DICT(dict={'__key': ATTR.STR(), '__val': ATTR.ANY()}),
		'remarks': ATTR.STR(),
		'create_time': ATTR.DATETIME(),
	}
	defaults = {'doc': None, 'remarks': ''}
	methods = {
		'read': {'permissions': [PERM(privilege='admin')]},
		'create': {
			'permissions': [PERM(privilege='admin', doc_mod={'user': '$__user'})]
		},
		'delete': {
			'permissions': [PERM(privilege='admin')],
			'query_args': {'_id': ATTR.ID()},
		},
	}

	async def pre_create(self, skip_events, env, query, doc, payload):
		# [DOC] Detect non-_id update query:
		if '_id' not in query:
			results = await Config.modules[doc['module']].read(
				skip_events=[Event.PERM], env=env, query=query
			)
			if results.args.count > 1:
				query.append({'_id': {'$in': [doc._id for doc in results.args.docs]}})
			elif results.args.count == 1:
				query.append({'_id': results.args.docs[0]._id})
			else:
				return self.status(
					status=400, msg='No update docs matched.', args={'code': 'NO_MATCH'}
				)
		if '_id' in query and type(query['_id'][0]) == list:
			for i in range(0, len(query['_id'][0]) - 1):
				self.create(
					skip_events=[Event.PERM],
					env=env,
					query=[{'_id': query['_id'][0][i]}],
					doc=doc,
				)
			query['_id'][0] = query['_id'][0][-1]
		doc['doc'] = ObjectId(query['_id'][0])
		return (skip_events, env, query, doc, payload)
