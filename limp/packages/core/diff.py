from limp.base_module import BaseModule
from limp.enums import Event
from limp.classes import ATTR, PERM, LIMP_DOC
from limp.config import Config

from bson import ObjectId


class Diff(BaseModule):
	'''`Diff` module provides data type and controller for `Diff Workflow`. It is meant for use by internal calls only. Best practice to accessing diff docs is by creating proxy modules or writing LIMP methods that expose the diff docs.'''

	collection = 'diff'
	attrs = {
		'user': ATTR.ID(desc='`_id` of `User` doc the doc belongs to.'),
		'module': ATTR.STR(desc='Name of the module the original doc is part of.'),
		'doc': ATTR.ID(desc='`_id` of the original doc.'),
		'vars': ATTR.KV_DICT(
			desc='Key-value `dict` containing all attrs that have been updated from the original doc.',
			key=ATTR.STR(),
			val=ATTR.ANY(),
		),
		'remarks': ATTR.STR(
			desc='Human-readable remarks of the doc. This is introduced to allow developers to add log messages to diff docs.'
		),
		'create_time': ATTR.DATETIME(
			desc='Python `datetime` ISO format of the doc creation.'
		),
	}
	defaults = {'doc': None, 'remarks': ''}
	methods = {
		'read': {'permissions': [PERM(privilege='read')]},
		'create': {'permissions': [PERM(privilege='__sys')]},
		'delete': {'permissions': [PERM(privilege='delete')]},
	}

	async def pre_create(self, skip_events, env, query, doc, payload):
		# [DOC] format Doc Oper with prefixed underscores to avoid data errors
		doc = self.format_doc_oper(doc=doc)
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
			for i in range(len(query['_id'][0]) - 1):
				self.create(
					skip_events=[Event.PERM],
					env=env,
					query=[{'_id': query['_id'][0][i]}],
					doc=doc,
				)
			query['_id'][0] = query['_id'][0][-1]
		doc['doc'] = ObjectId(query['_id'][0])
		return (skip_events, env, query, doc, payload)

	def format_doc_oper(self, *, doc: LIMP_DOC):
		shadow_doc: LIMP_DOC = {}
		for attr in doc.keys():
			if attr[0] == '$':
				shadow_doc[f'__{attr}'] = doc[attr]
			elif type(doc[attr]) == dict:
				shadow_doc[attr] = self.format_doc_oper(doc=doc[attr])
			else:
				shadow_doc[attr] = doc[attr]
		return shadow_doc
