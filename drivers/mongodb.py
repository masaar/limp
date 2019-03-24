from config import Config
from event import Event
from utils import ClassSingleton
from base_model import BaseModel

from pymongo import MongoClient
from bson import ObjectId

import os, logging, re
logger = logging.getLogger('limp')

# metaclass=ClassSingleton
class MongoDb(metaclass=ClassSingleton):
	conn = False
	db = False

	def singleton(self):
		pass
		# self.conn = MongoClient(Config.data_server)
		# self.db = self.conn[Config.data_name]
	
	def create_conn(self):
		connection_config = {
			'ssl':Config.data_ssl
		}
		if Config.data_ca:
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			connection_config['ssl_ca_certs'] = os.path.join(__location__, '..', 'certs', Config.data_ca_name)
		self.conn = MongoClient(Config.data_server, **connection_config)
		self.db = self.conn[Config.data_name]
	
	def read(self, collection, attrs, extns, modules, query):
		if not self.conn:
			self.create_conn()
		#logger.debug('mongodb.read')
		aggregate_query = [{'$match':{'$or':[{'__deleted':{'$exists':False}}, {'__deleted':False}]}}]
		or_query = []
		access_query = {}

		# return_count = True
		skip = False
		limit = False
		sort = False
		group = False
		if '$skip' in query.keys():
			skip = query['$skip']
			del query['$skip']
		if '$limit' in query.keys():
			limit = query['$limit']
			del query['$limit']
		if '$sort' in query.keys():
			sort = query['$sort']
			del query['$sort']
		else:
			sort = {'_id':-1}
		if '$search' in query.keys():
			aggregate_query = [{'$match':{'$text':{'$search':query['$search']}}}] + aggregate_query
			# aggregate_query[0]['$match']['$text'] = {'$search':query['$search']}
			project_query = {attr:'$'+attr for attr in attrs.keys()}
			project_query['_id'] = '$_id'
			project_query['__score'] = {'$meta': 'textScore'}
			aggregate_query.append({'$project':project_query})
			aggregate_query.append({'$match':{'__score':{'$gt':0.5}}})
			del query['$search']
		if '$geo_near' in query.keys():
			aggregate_query = [{'$geoNear':{
				'near':{'type':'Point','coordinates':query['$geo_near']['val']},
				'distanceField':query['$geo_near']['attr'] + '.__distance',
				'maxDistance':query['$geo_near']['dist'],
				# 'includeLocs':'dist.location',
				'spherical':True
			}}] + aggregate_query
			# project_query = {attr:'$'+attr for attr in attrs.keys()}
			# project_query['_id'] = '$_id'
			# project_query['__score'] = {'$meta': 'textScore'}
			# aggregate_query.append({'$project':project_query})
			# aggregate_query.append({'$match':{'__score':{'$gt':0.5}}})
			del query['$geo_near']
		if '$group' in query.keys():
			group = query['$group']
			del query['$group']

		for arg in query.keys():
			query_arg = arg
			if arg.find('.') == -1 and arg.startswith('__OR:'): oper = 'or'
			else: oper = 'and'
			arg = arg.replace('__OR:', '')

			if arg.find('.') != -1 and arg.split('.')[0] in extns.keys():
				extn, arg = arg.split('.')
				if extn not in attrs.keys() or 'val' not in query[query_arg].keys() or not query[query_arg]['val']: continue
				arg_collection = modules[extns[extn][0]].collection
				arg_attrs = modules[extns[extn][0]].attrs
				aggregate_query.append({'$lookup':{'from':arg_collection, 'localField':extn, 'foreignField':'_id', 'as':extn}})
				aggregate_query.append({'$unwind':'$'+extn})
				extn = extn + '.'
				child_arg = ''
			
			elif arg.find('.') != -1 and (attrs[arg.split('.')[0]] == 'attrs' or (type(attrs[arg.split('.')[0]]) == dict and arg.split('.')[1] in attrs[arg.split('.')[0]].keys())):
				arg, child_arg = arg.split('.')
				arg_collection = collection
				arg_attrs = attrs
				extn = ''
				child_arg = '.' + child_arg

			else:
				if type(query[query_arg]) != dict or (arg != '_id' and arg not in attrs.keys()) or 'val' not in query[query_arg].keys() or not query[query_arg]['val']: continue
				arg_collection = collection
				arg_attrs = attrs
				extn = ''
				child_arg = ''

			#logger.debug('testing arg: %s, against: %s.', arg, arg_attrs[arg] if arg in arg_attrs.keys() else query[query_arg])

			if 'strict' in query[query_arg].keys() and not query[query_arg]['strict']:
				query[query_arg]['val'] = re.compile(re.escape(query[query_arg]['val']), re.IGNORECASE)

			# [TODO] Global handle of list val as $in oper
			if arg == '_id' or arg_attrs[arg] == 'id' or (type(arg_attrs[arg]) == list and arg_attrs[arg][0] == 'id'):
				#logger.debug('converting (%s) to ObjectId.', query[query_arg]['val'])
				if type(query[query_arg]['val']) == list:
					if 'oper' in query[query_arg].keys() and query[query_arg]['oper'] == '$all':
						query[query_arg]['val'] = {'$all':[ObjectId(_id) for _id in query[query_arg]['val']]}
					else:
						query[query_arg]['val'] = {'$in':[ObjectId(_id) for _id in query[query_arg]['val']]}
				else:
					if not isinstance(query[query_arg]['val'], ObjectId):
						query[query_arg]['val'] = ObjectId(query[query_arg]['val'])
				if oper == 'or': or_query.append({extn+arg+child_arg:query[query_arg]['val']})
				else: aggregate_query.append({'$match':{extn+arg+child_arg:query[query_arg]['val']}})
			# elif arg_attrs[arg] == 'id':
			# 	# [TODO] Add $in oper for list val
			# 	if oper == 'or': or_query.append({extn+arg+child_arg:ObjectId(query[query_arg]['val'])})
			# 	else: aggregate_query.append({'$match':{extn+arg+child_arg:ObjectId(query[query_arg]['val'])}})
			elif type(arg_attrs[arg]) == dict:
				child_aggregate_query = []
				for child_attr in [child_attr for child_attr in arg_attrs[arg].keys()]:
					child_aggregate_query.append({extn+arg+child_arg+'.'+child_attr.split(':')[0]:query[query_arg]['val']})
				if oper == 'or': or_query.append({'$or':child_aggregate_query})
				else: aggregate_query.append({'$match':{'$or':child_aggregate_query}})
			# elif type(arg_attrs[arg]) == list and arg_attrs[arg][0] == 'id':
			# 	if oper == 'or': or_query.append({extn+arg+child_arg:ObjectId(query[query_arg]['val'])})
			# 	else: aggregate_query.append({'$match':{extn+arg+child_arg:ObjectId(query[query_arg]['val'])}})
			elif arg_attrs[arg] == 'access':
				# [DOC] Check if passed arg is $__access query or sample val
				# [TODO] Work on sample val resolve
				# if query[query_arg]['val'] == '$__access':
				access_query = [
					{'$project':{
						'__user':'$user',
						'__access.anon':'${}.anon'.format(query_arg),
						'__access.users':{'$in':[ObjectId(query[query_arg]['val']['$__user']), '${}.users'.format(query_arg)]},
						'__access.groups':{'$or':[{'$in':[group, '${}.groups'.format(query_arg)]} for group in query[query_arg]['val']['$__groups']]}
						# 'access.groups':{'$in':[query[query_arg]['val']['$__groups'], '$access.groups']}
					}},
					{'$match':{'$or':[{'__user':ObjectId(query[query_arg]['val']['$__user'])}, {'__access.anon':True}, {'__access.users':True}, {'__access.groups':True}]}}
				]
				access_query[0]['$project'].update({attr:'$'+attr for attr in attrs.keys()})
				if oper == 'or': or_query += access_query
				else: aggregate_query += access_query
				# aggregate_query.append(access_query)
			else:
				if 'oper' not in query[query_arg].keys() or query[query_arg]['oper'] not in ['$gt', '$lt', '$bet', '$not', '$regex', '$all']:
					query[query_arg]['oper'] = '$eq'
				# if 'oper' in query[query_arg].keys(): 
					# [TODO] ignore invalid opers
					# if query[query_arg]['oper'] not in ['$gt', '$lt', '$bet', '$not', '$regex', '$all']:
					# 	query[query_arg]['oper'] = '$eq'
				if oper == 'or':
					if query[query_arg]['oper'] == '$bet':
						or_query.append({extn+arg+child_arg:{'$gte':query[query_arg]['val'], '$lte':query[query_arg]['val2']}})
					else:
						or_query.append({extn+arg+child_arg:{query[query_arg]['oper']:query[query_arg]['val']}})
				else:
					if query[query_arg]['oper'] == '$bet':
						aggregate_query.append({'$match':{extn+arg+child_arg:{'$gte':query[query_arg]['val'], '$lte':query[query_arg]['val2']}}})
					elif query[query_arg]['oper'] == '$not':
						aggregate_query.append({'$match':{extn+arg+child_arg:{'$ne':query[query_arg]['val']}}})
					else:
						aggregate_query.append({'$match':{extn+arg+child_arg:{query[query_arg]['oper']:query[query_arg]['val']}}})
				# else:
				# 	if oper == 'or': or_query.append({extn+arg+child_arg:query[query_arg]['val']})
				# 	else: aggregate_query.append({'$match':{extn+arg+child_arg:query[query_arg]['val']}})
			
			if extn.find('.') != -1:
				group_query = {attr:{'$first':'$'+attr} for attr in attrs.keys()}
				group_query['_id'] = '$_id'
				group_query[extn[:-1]] = {'$first':'$'+extn[:-1]+'._id'}
				aggregate_query.append({'$group':group_query})

		group_query = {attr:{'$first':'$'+attr} for attr in attrs.keys()}
		group_query['_id'] = '$_id'
		aggregate_query.append({'$group':group_query})
		if or_query: aggregate_query.append({'$match':{'$or':or_query}})
		# if access_query:
		# 	access_query['$project'].update({attr:'$'+attr for attr in attrs.keys() if attr != 'access'})
		# 	# del access_query['$project']['access']
		# 	aggregate_query.append({'$project':access_query['$project']})
		# 	aggregate_query.append({'$match':access_query['$match']})

		# logger.debug('final query: %s, %s.', collection, aggregate_query)

		collection = self.db[collection]
		docs_total = collection.aggregate(aggregate_query + [{'$count':'__docs_total'}])
		try:
			docs_total = docs_total.next()['__docs_total']
		except StopIteration:
			return {
				'total':0,
				'count':0,
				'docs':[],
				'groups': []
			}

		groups = {}
		if group:
			for group_condition in group:
				group_query = aggregate_query + [{'$bucketAuto':{
					'groupBy': '$' + group_condition['by'],
					'buckets': group_condition['count']
				}}]
				check_group = False
				for i in range(0, group_query.__len__()):
					if list(group_query[i].keys())[0] == '$match' and list(group_query[i]['$match'].keys())[0] == group_condition['by']:
						check_group = True
						break
				if check_group:
					del group_query[i]
				group_query = collection.aggregate(group_query)
				groups[group_condition['by']] = [{'min':group['_id']['min'], 'max':group['_id']['max'], 'count':group['count']} for group in group_query]

		# if sort:
		aggregate_query.append({'$sort':sort})
		if skip:
			aggregate_query.append({'$skip':skip})
		if limit:
			aggregate_query.append({'$limit':limit})
		
		logger.debug('final query: %s, %s.', collection, aggregate_query)

		docs_count = collection.aggregate(aggregate_query + [{'$count':'__docs_count'}])
		try:
			docs_count = docs_count.next()['__docs_count']
		except StopIteration:
			return {
				'total':docs_total,
				'count':0,
				'docs':[],
				'groups': {} if not group else groups
			}
		docs = collection.aggregate(aggregate_query)
		models = []
		for doc in docs:
			# #logger.debug('found: %s.', doc)
			for extn in extns.keys():
				# [DOC] Check if extn module is dynamic value
				if extns[extn][0].startswith('$__doc.'):
					extn_module = modules[doc[extns[extn][0].replace('$__doc.', '')]]
				else:
					extn_module = modules[extns[extn][0]]
				# [DOC] Check if extn attr set to fetch all or specific attrs
				if extns[extn][1][0] == '*':
					extn_attrs = {attr:extn_module.attrs[attr] for attr in extn_module.attrs.keys()}
				else:
					extn_attrs = {attr:extn_module.attrs[attr] for attr in extns[extn][1]}
				# [DOC] Implicitly add _id key to extn attrs so that we don't delete it in process
				extn_attrs['_id'] = 'id'
				#logger.debug('extn_attrs: %s.', extn_attrs)
				if attrs[extn] == 'id':
					# [DOC] In case value is null, do not attempt to extend doc
					if not doc or not doc[extn]: continue
					# [DOC] Stage skip events
					skip_events = [Event.__PERM__]
					# [DOC] Call read method on extn module, without second-step extn
					# [DOC] Check if extn rule is explicitly requires second-dimension extn.
					if not (extns[extn].__len__() == 3 and extns[extn][2] == True):
						skip_events.append(Event.__EXTN__)
					extn_results = extn_module.methods['read'](skip_events=skip_events, query={'_id':{'val':doc[extn]}, '$limit':1})
					# [TODO] Consider a fallback for extn no-match cases
					if extn_results['args']['count']:
						doc[extn] = extn_results['args']['docs'][0]
						# [DOC] delete all unneeded keys from the resulted doc
						del_attrs = []
						for attr in doc[extn]._attrs().keys():
							if attr not in extn_attrs.keys():
								del_attrs.append(attr)
						#logger.debug('extn del_attrs: %s.', del_attrs)
						for attr in del_attrs:
							del doc[extn][attr]
					else:
						doc[extn] = None
				elif attrs[extn] == ['id']:
					# [DOC] In case value is null, do not attempt to extend doc
					if not doc[extn]: continue
					# [DOC] Loop over every _id in the extn array
					for i in range(0, doc[extn].__len__()):
						# [DOC] In case value is null, do not attempt to extend doc
						if not doc[extn][i]: continue
						extn_results = extn_module.methods['read'](skip_events=[Event.__PERM__, Event.__EXTN__], query={'_id':{'val':doc[extn][i]}, '$limit':1})
						if extn_results['args']['count']:
							#logger.debug('extedning doc with attrs: %s:', {attr:extn_results['args']['docs'][0][attr] for attr in extn_attrs.keys()})
							# [TODO] Add condition for limited keys import
							doc[extn][i] = {attr:extn_results['args']['docs'][0][attr] for attr in extn_attrs.keys()}
						else:
							doc[extn][i] = None
			if doc:
				models.append(BaseModel(doc))
		return {
			'total':docs_total,
			'count':docs_count,
			'docs':models,
			'groups': {} if not group else groups
		}

	def create(self, collection, attrs, extns, modules, doc):
		if not self.conn:
			self.create_conn()
		collection = self.db[collection]
		# #logger.debug('Inserting doc: %s.', doc)
		_id = collection.insert_one(doc).inserted_id
		return {
			'count':1,
			'docs':[BaseModel({'_id':_id})]
		}
	
	def update(self, collection, attrs, extns, modules, query, doc):
		if not self.conn:
			self.create_conn()
		# [DOC] Perform a read query to get all matching documents
		read_results = self.read(collection=collection, attrs=attrs, extns={}, modules=modules, query=query)
		# print('read_results', read_results)
		docs = [doc._id for doc in read_results['docs']]
		# [DOC] Perform update query on matching docs
		collection = self.db[collection]
		results = None
		if 'diff' not in doc.keys():
			# #logger.debug('attempting to update docs:%s with values:%s', docs, doc)
			results = collection.update_many({'_id':{'$in':docs}}, {'$set':doc})
			update_count = results.modified_count
		else:
			update_count = 0
			diff = doc['diff']
			del doc['diff']
			diff['vars']
			# update_results = []
			for update_doc in read_results['docs']:
				# #logger.debug('final update object: %s.', {'$set':doc, '$push':{'diff':diff}})
				shadow_doc = {attr:doc[attr] for attr in doc.keys() if doc[attr] != update_doc[attr] and attr != 'diff'}
				# print(update_doc, shadow_doc)
				# [DOC] Some mass update queries end up with no docs, skip them.
				if shadow_doc.keys().__len__() == 0:
					continue
				diff['vars'] = {attr:update_doc[attr] for attr in shadow_doc.keys()}
				# #logger.debug('shadow_doc: %s.', shadow_doc)
				#logger.debug('attempting to update doc:%s with values:%s', update_doc._id, shadow_doc)
				# update_results.append(
				results = collection.update_one({'_id':update_doc._id}, {'$set':shadow_doc, '$push':{'diff':diff}})
				update_count += results.modified_count
				# )
		# 1/0
			# results = update_results[0]
		#logger.debug('update results: %s', results)
		# update_count = 0
		# update_id = []
		# if type(_id) == str or isinstance(_id, ObjectId): _id = [_id]
		# #logger.debug('updating _id: %s.', _id)
		# for id in _id:
		# 	results = collection.update_one({'_id':ObjectId(id)}, {'$set':doc})
		# update_count += results.modified_count
		# if results.modified_count:
		# 	update_id.append(ObjectId(id))
		return {
			'count':update_count,
			'docs':[{'_id':doc} for doc in docs]
		}
	
	def delete(self, collection, attrs, extns, modules, query, force_delete):
		if not self.conn:
			self.create_conn()
		if not force_delete:
			return self.update(collection=collection, attrs=attrs, extns=extns, modules=modules, query=query, doc={'__deleted':True})
		else:
			# [DOC] Perform a read query to get all matching documents
			results = self.read(collection=collection, attrs=attrs, extns=extns, modules=modules, query=query)
			docs = [doc._id for doc in results['docs']]
			#logger.debug('attempting to delete docs:%s', docs)
			# [DOC] Perform update query on matching docs
			collection = self.db[collection]
			results = collection.delete_many({'_id':{'$in':docs}})
			#logger.debug('delete results: %s', results)
			return {
				'count':results.deleted_count,
				'docs':docs
			}

		# collection = self.db[collection]
		# delete_count = 0
		# delete_id = []
		# if type(_id) == str or isinstance(_id, ObjectId): _id = [_id]
		# if force_delete:
		# 	for id in _id:
		# 		results = collection.delete_one({'_id':ObjectId(id)})
		# 	# delete_count += results.delete_count
		# 	delete_count += 1
		# else:
		# 	for id in _id:
		# 		results = collection.update_one({'_id':ObjectId(id)}, {'$set':{'__deleted':True}})
		# 	delete_count += results.modified_count
		# 	if results.modified_count:
		# 		delete_id.append(ObjectId(id))
		# return {
		# 	'count':delete_count,
		# 	'docs':delete_id
		# }