from config import Config
from event import Event
from utils import ClassSingleton, DictObj
from base_model import BaseModel

from pymongo import MongoClient
from bson import ObjectId

import os, logging, re
logger = logging.getLogger('limp')

class MongoDb(metaclass=ClassSingleton):

	def singleton(self):
		# [DOC] Deprecated.
		pass
	
	def create_conn(self):
		connection_config = {
			'ssl':Config.data_ssl
		}
		if Config.data_ca:
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			connection_config['ssl_ca_certs'] = os.path.join(__location__, '..', 'certs', Config.data_ca_name)
		# [DOC] Check for multiple servers
		if type(Config.data_server) == list:
			for data_server in Config.data_server:
				conn = MongoClient(data_server, **connection_config, connect=True)
				try:
					logger.debug('Check if data_server: %s isMaster.', data_server)
					results = conn.admin.command('ismaster')
					logger.debug('-Check results: %s', results)
					if results['ismaster']:
						conn = conn[Config.data_name]
						break
				except Exception as err:
					logger.debug('Not master. Error: %s', err)
					pass
		elif type(Config.data_server) == str:
			# [DOC] If it's single server just connect directly
			conn = MongoClient(Config.data_server, **connection_config, connect=True)[Config.data_name]
		return conn
	
	# [DEPRECATED] query dict
	def _compile_query_deprecated(self, collection, attrs, extns, modules, query):
		aggregate_query = [{'$match':{'$or':[{'__deleted':{'$exists':False}}, {'__deleted':False}]}}]
		or_query = []
		access_query = {}

		logger.debug('attempting to parse query: %s', query)

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
				'spherical':True
			}}] + aggregate_query
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
				if extn not in attrs.keys() or 'val' not in query[query_arg].keys() or (query[query_arg]['val'] == None or query[query_arg]['val'] == ''): continue
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
				if type(query[query_arg]) != dict or (arg != '_id' and arg not in attrs.keys()) or 'val' not in query[query_arg].keys() or (query[query_arg]['val'] == None or query[query_arg]['val'] == ''): continue
				arg_collection = collection
				arg_attrs = attrs
				extn = ''
				child_arg = ''

			if 'strict' in query[query_arg].keys() and not query[query_arg]['strict']:
				query[query_arg]['val'] = re.compile(re.escape(query[query_arg]['val']), re.IGNORECASE)

			# [TODO] Global handle of list val as $in oper
			if arg == '_id' or arg_attrs[arg] == 'id' or (type(arg_attrs[arg]) == list and arg_attrs[arg][0] == 'id'):
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
			elif type(arg_attrs[arg]) == dict:
				child_aggregate_query = []
				for child_attr in [child_attr for child_attr in arg_attrs[arg].keys()]:
					child_aggregate_query.append({extn+arg+child_arg+'.'+child_attr.split(':')[0]:query[query_arg]['val']})
				if oper == 'or': or_query.append({'$or':child_aggregate_query})
				else: aggregate_query.append({'$match':{'$or':child_aggregate_query}})
			elif arg_attrs[arg] == 'access':
				# [DOC] Check if passed arg is $__access query or sample val
				# [TODO] Work on sample val resolve
				access_query = [
					{'$project':{
						'__user':'$user',
						'__access.anon':'${}.anon'.format(query_arg),
						'__access.users':{'$in':[ObjectId(query[query_arg]['val']['$__user']), '${}.users'.format(query_arg)]},
						'__access.groups':{'$or':[{'$in':[group, '${}.groups'.format(query_arg)]} for group in query[query_arg]['val']['$__groups']]}
					}},
					{'$match':{'$or':[{'__user':ObjectId(query[query_arg]['val']['$__user'])}, {'__access.anon':True}, {'__access.users':True}, {'__access.groups':True}]}}
				]
				access_query[0]['$project'].update({attr:'$'+attr for attr in attrs.keys()})
				if oper == 'or': or_query += access_query
				else: aggregate_query += access_query
			else:
				if 'oper' not in query[query_arg].keys() or query[query_arg]['oper'] not in ['$gt', '$lt', '$gte', '$lte', '$bet', '$not', '$regex', '$all', '$in']:
					query[query_arg]['oper'] = '$eq'
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
			
			if extn.find('.') != -1:
				group_query = {attr:{'$first':'$'+attr} for attr in attrs.keys()}
				group_query['_id'] = '$_id'
				group_query[extn[:-1]] = {'$first':'$'+extn[:-1]+'._id'}
				aggregate_query.append({'$group':group_query})

		group_query = {attr:{'$first':'$'+attr} for attr in attrs.keys()}
		group_query['_id'] = '$_id'
		aggregate_query.append({'$group':group_query})
		if or_query: aggregate_query.append({'$match':{'$or':or_query}})

		logger.debug('Final query: %s', aggregate_query)

		return (skip, limit, sort, group, aggregate_query)
	
	def _compile_query(self, collection, attrs, extns, modules, query):
		aggregate_query = []
		logger.debug('attempting to parse query: %s', query)

		skip = False
		limit = False
		sort = False
		group = False

		for step in query:
			# [DOC] Check if step type is list or dict
			if type(step) == list:
				self._compile_query_step(aggregate_query=aggregate_query, collection=collection, attrs=attrs, extns=extns, modules=modules, step=step)
			elif type(step) == dict:
				if '$skip' in step.keys():
					skip = step['$skip']
					del step['$skip']
				if '$limit' in step.keys():
					limit = step['$limit']
					del step['$limit']
				if '$sort' in step.keys():
					sort = step['$sort']
					del step['$sort']
				else:
					sort = {'_id':-1}
				if '$search' in step.keys():
					aggregate_query = [{'$match':{'$text':{'$search':step['$search']}}}] + aggregate_query
					project_query = {attr:'$'+attr for attr in attrs.keys()}
					project_query['_id'] = '$_id'
					project_query['__score'] = {'$meta': 'textScore'}
					aggregate_query.append({'$project':project_query})
					aggregate_query.append({'$match':{'__score':{'$gt':0.5}}})
					del step['$search']
				if '$geo_near' in step.keys():
					aggregate_query = [{'$geoNear':{
						'near':{'type':'Point','coordinates':step['$geo_near']['val']},
						'distanceField':step['$geo_near']['attr'] + '.__distance',
						'maxDistance':step['$geo_near']['dist'],
						'spherical':True
					}}] + aggregate_query
					del step['$geo_near']
				if '$group' in step.keys():
					group = step['$group']
					del step['$group']

		aggregate_query = [{'$match':{'$or':[{'__deleted':{'$exists':False}}, {'__deleted':False}]}}, *aggregate_query]
		return (skip, limit, sort, group, aggregate_query)
		
	def _compile_query_step(self, aggregate_query, collection, attrs, extns, modules, step, top_level=True):
		if top_level:
			step_query = [{'$match':{'$or':[]}}]
			step_query_match = step_query[0]['$match']['$or']
		else:
			step_query = [{'$or':[]}]
			step_query_match = step_query[0]['$or']

		for child_step in step:
			if type(child_step) == dict:
				child_step_query = {'$and':[]}
				for attr in child_step.keys():
					# [DOC] Add extn query when required
					if attr.find('.') != -1 and attr.split('.')[0] in extns.keys():
						extn_collection = modules[extns[attr.split('.')[0]][0]].collection
						if modules[extns[attr.split('.')[0]][0]].attrs[attr.split('.')[1]] == 'id':
							child_step[attr] = ObjectId(child_step[attr])
						step_query.insert(0, {'$unwind':'${}'.format(attr.split('.')[0])})
						step_query.insert(0, {'$lookup':{'from':extn_collection, 'localField':attr.split('.')[0], 'foreignField':'_id', 'as':attr.split('.')[0]}})
						group_query = {attr:{'$first':'${}'.format(attr)} for attr in attrs.keys()}
						group_query[attr.split('.')[0]] = {'$first':'${}._id'.format(attr.split('.')[0])}
						group_query['_id'] = '$_id'
						step_query.append({'$group':group_query})
					# [DOC] Convert strings and lists of strings to ObjectId when required
					elif attr in attrs.keys() and attrs[attr] == 'id':
						child_step[attr] = ObjectId(child_step[attr])
					elif attr in attrs.keys() and attrs[attr] == ['id']:
						if type(child_step[attr]):
							child_step[attr] = [ObjectId(child_attr) for child_attr in child_step[attr]]
						elif type(child_step[attr]) == str:
							child_step[attr] = ObjectId(child_step[attr])
					child_step_query['$and'].append({attr: child_step[attr]})
				if child_step_query['$and'].__len__():
					step_query_match.append(child_step_query)
			elif type(child_step) == list:
				step_query_match.append(self._compile_query_step(aggregate_query=aggregate_query, collection=collection, attrs=attrs, extns=extns, modules=modules, step=child_step, top_level=False))

		if not step_query_match.__len__():
			return []

		if top_level:
			aggregate_query += step_query
		else:
			return step_query
	
	def read(self, env, session, collection, attrs, extns, modules, query):
		conn = env['conn']
		# [DEPRECATED] query dict
		if type(query) == dict:
			skip, limit, sort, group, aggregate_query = self._compile_query_deprecated(collection=collection, attrs=attrs, extns=extns, modules=modules, query=query)
		elif type(query) == list:
			skip, limit, sort, group, aggregate_query = self._compile_query(collection=collection, attrs=attrs, extns=extns, modules=modules, query=query)
		
		logger.debug('aggregate_query: %s', aggregate_query)

		collection = conn[collection]
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
				if attrs[extn] == 'id':
					# [DOC] In case value is null, do not attempt to extend doc
					if not doc or not doc[extn]: continue
					# [DOC] Stage skip events
					skip_events = [Event.__PERM__]
					# [DOC] Call read method on extn module, without second-step extn
					# [DOC] Check if extn rule is explicitly requires second-dimension extn.
					if not (extns[extn].__len__() == 3 and extns[extn][2] == True):
						skip_events.append(Event.__EXTN__)
					extn_results = extn_module.methods['read'](skip_events=skip_events, env=env, session=session, query=[
						[{'_id':doc[extn]}],
						{'$limit':1}
					])
					# [TODO] Consider a fallback for extn no-match cases
					if extn_results['args']['count']:
						doc[extn] = extn_results['args']['docs'][0]
						# [DOC] delete all unneeded keys from the resulted doc
						del_attrs = []
						for attr in doc[extn]._attrs().keys():
							if attr not in extn_attrs.keys():
								del_attrs.append(attr)
						# logger.debug('extn del_attrs: %s against: %s.', del_attrs, extn_attrs)
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
						extn_results = extn_module.methods['read'](skip_events=[Event.__PERM__, Event.__EXTN__], env=env, session=session, query=[
							[{'_id':doc[extn][i]}],
							{'$limit':1}
						])
						if extn_results['args']['count']:
							doc[extn][i] = extn_results['args']['docs'][0]
							# [DOC] delete all unneeded keys from the resulted doc
							del_attrs = []
							for attr in doc[extn][i]._attrs().keys():
								if attr not in extn_attrs.keys():
									del_attrs.append(attr)
							# logger.debug('extn del_attrs: %s against: %s.', del_attrs, extn_attrs)
							for attr in del_attrs:
								del doc[extn][i][attr]
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

	def create(self, env, session, collection, attrs, extns, modules, doc):
		conn = env['conn']
		collection = conn[collection]
		_id = collection.insert_one(doc).inserted_id
		return {
			'count':1,
			'docs':[BaseModel({'_id':_id})]
		}
	
	def update(self, env, session, collection, attrs, extns, modules, query, doc):
		conn = env['conn']
		# [DOC] Perform a read query to get all matching documents
		read_results = self.read(env=env, session=session, collection=collection, attrs=attrs, extns={}, modules=modules, query=query)
		docs = [doc._id for doc in read_results['docs']]
		# [DOC] Perform update query on matching docs
		collection = conn[collection]
		results = None
		update_doc = {'$set':doc}
		# [DOC] Check for increament oper
		del_attrs = []
		for attr in doc.keys():
			if type(doc[attr]) == dict and '$inc' in doc[attr].keys():
				if '$inc' not in update_doc.keys():
					update_doc['$inc'] = {}
				update_doc['$inc'][attr] = doc[attr]['$inc']
				del_attrs.append(attr)
		for del_attr in del_attrs:
			del doc[del_attr]
		# [DOC] If using Azure Mongo service update docs one by one
		if Config.data_azure_mongo:
			update_count = 0
			for _id in docs:
				results = collection.update_one({'_id':_id}, update_doc)
				update_count += results.modified_count
		else:
			results = collection.update_many({'_id':{'$in':docs}}, update_doc)
			update_count = results.modified_count
		return {
			'count':update_count,
			'docs':[{'_id':doc} for doc in docs]
		}
	
	def delete(self, env, session, collection, attrs, extns, modules, query, force_delete):
		conn = env['conn']
		if not force_delete:
			return self.update(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query, doc={'__deleted':True})
		else:
			# [DOC] Perform a read query to get all matching documents
			results = self.read(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query)
			docs = [doc._id for doc in results['docs']]
			# [DOC] Perform update query on matching docs
			collection = conn[collection]
			if Config.data_azure_mongo:
				delete_count = 0
				for _id in docs:
					results = collection.delete_one({'_id':_id})
					delete_count += results.deleted_count
			else:
				results = collection.delete_many({'_id':{'$in':docs}})
				delete_count = results.deleted_count
			return {
				'count':delete_count,
				'docs':docs
			}
	
	def drop(self, env, session, collection):
		conn = env['conn']
		collection = conn[collection]
		drop_results = collection.drop()
		return True