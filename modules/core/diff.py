from base_module import BaseModule
from event import Event

from bson import ObjectId

import datetime, time

class Diff(BaseModule):
	collection = 'diff'
	attrs = {
		'user':'id',
		'module':'str',
		'doc':'id',
		'vars':'attrs',
		'remarks':'str',
		'create_time':'time'
	}
	optional_attrs = ['doc', 'remarks']
	methods = {
		'read':{
			'permissions':[['admin', {}, {}]]
		},
		'create':{
			'permissions':[['admin', {}, {'user':'$__user'}]]
		},
		'delete':{
			'permissions':[['admin', {}, {}]],
			'query_args':['!_id']
		}
	}

	def pre_create(self, env, session, query, doc):
		# [DOC] Detect non-_id update query:
		if '_id' not in query.keys():
			results = self.modules[doc['module']].methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=query)
			if results.args.count > 1:
				query['_id'] = {'val':[doc._id for doc in results.args.docs]}
			elif results.args.count == 1:
				query['_id'] = results.args.docs[0]._id
			else:
				return {
					'status':400,
					'msg':'No update docs matched.',
					'args':{'code':'CORE_DIFF_NO_MATCH'}
				}
		if '_id' in query.keys() and type(query['_id']['val']) == list:
			for i in range(0, query['_id']['val'].__len__() - 1):
				self.methods['create'](skip_events=[Event.__PERM__], env=env, session=session, query={'_id':{'val':query['_id']['val'][i]}}, doc=doc)
			query['_id'] = {'val':query['_id']['val'][query['_id']['val'].__len__() - 1]}
		doc['doc'] = ObjectId(query['_id']['val'])
		return (env, session, query, doc)