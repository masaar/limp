from base_module import BaseModule
from enums import Event

from bson import ObjectId

class Diff(BaseModule):
	collection = 'diff'
	attrs = {
		'user':'id',
		'module':'str',
		'doc':'id',
		'vars':'attrs',
		'remarks':'str',
		'create_time':'datetime'
	}
	defaults = {'doc':None, 'remarks':''}
	methods = {
		'read':{
			'permissions':[['admin', {}, {}]]
		},
		'create':{
			'permissions':[['admin', {}, {'user':'$__user'}]]
		},
		'delete':{
			'permissions':[['admin', {}, {}]],
			'query_args':{'_id':'id'}
		}
	}

	async def pre_create(self, skip_events, env, query, doc):
		# [DOC] Detect non-_id update query:
		if '_id' not in query:
			results = await self.modules[doc['module']].read(skip_events=[Event.__PERM__], env=env, query=query)
			if results.args.count > 1:
				query.append({'_id':{'$in':[doc._id for doc in results.args.docs]}})
			elif results.args.count == 1:
				query.append({'_id':results.args.docs[0]._id})
			else:
				return {
					'status':400,
					'msg':'No update docs matched.',
					'args':{'code':'CORE_DIFF_NO_MATCH'}
				}
		if '_id' in query and type(query['_id'][0]) == list:
			for i in range(0, len(query['_id'][0]) - 1):
				self.create(skip_events=[Event.__PERM__], env=env, query=[{'_id':query['_id'][0][i]}], doc=doc)
			query['_id'][0] = query['_id'][0][-1]
		doc['doc'] = ObjectId(query['_id'][0])
		return (skip_events, env, query, doc)