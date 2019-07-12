from config import Config
from event import Event
from utils import DictObj, Query
from base_model import BaseModel
from data import DELETE_SOFT_SKIP_SYS, DELETE_SOFT_SYS, DELETE_FORCE_SKIP_SYS, DELETE_FORCE_SYS

from pymongo import MongoClient
from bson import ObjectId

import os, logging, re, datetime
logger = logging.getLogger('limp')

class MongoDb():
	
	@classmethod
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
	
	@classmethod
	def _compile_query(self, collection, attrs, extns, modules, query):
		aggregate_prefix = [{'$match':{'$or':[{'__deleted':{'$exists':False}}, {'__deleted':False}]}}]
		aggregate_suffix = []
		aggregate_query = [{'$match':{'$and':[]}}]
		aggregate_match = aggregate_query[0]['$match']['$and']
		skip = None
		limit = None
		sort = {'_id':-1}
		group = None
		logger.debug('attempting to parse query: %s', query)

		if '$skip' in query:
			skip = query['$skip']
			del query['$skip']
		if '$limit' in query:
			limit = query['$limit']
			del query['$limit']
		if '$sort' in query:
			sort = query['$sort']
			del query['$sort']
		if '$limit' in query:
			limit = query['$limit']
			del query['$limit']
		if '$group' in query:
			group = query['$group']
			del query['$group']
		if '$search' in query:
			aggregate_prefix.insert(0, {'$match':{'$text':{'$search':query['$search']}}})
			project_query = {attr:'$'+attr for attr in attrs.keys()}
			project_query['_id'] = '$_id'
			project_query['__score'] = {'$meta': 'textScore'}
			aggregate_suffix.append({'$project':project_query})
			aggregate_suffix.append({'$match':{'__score':{'$gt':0.5}}})
			del query['$search']
		if '$geo_near' in query:
			aggregate_prefix.insert(0, {'$geoNear':{
				'near':{'type':'Point','coordinates':query['$geo_near']['val']},
				'distanceField':query['$geo_near']['attr'] + '.__distance',
				'maxDistance':query['$geo_near']['dist'],
				'spherical':True
			}})
			del query['$geo_near']

		for step in query:
			self._compile_query_step(aggregate_prefix=aggregate_prefix, aggregate_suffix=aggregate_suffix, aggregate_match=aggregate_match, collection=collection, attrs=attrs, extns=extns, modules=modules, step=step)
		
		logger.debug('parsed query, aggregate_prefix: %s, aggregate_suffix: %s, aggregate_match:%s', aggregate_prefix, aggregate_suffix, aggregate_match)
		if aggregate_match.__len__() == 1:
			aggregate_query = [{'$match':aggregate_match[0]}]
		elif aggregate_match.__len__() == 0:
			aggregate_query = []

		aggregate_query = aggregate_prefix + aggregate_query + aggregate_suffix
		return (skip, limit, sort, group, aggregate_query)
	
	@classmethod
	def _compile_query_step(self, aggregate_prefix, aggregate_suffix, aggregate_match, collection, attrs, extns, modules, step):
		if type(step) == dict and step.keys().__len__():
			child_aggregate_query = {'$and':[]}
			for attr in step.keys():
				if attr.startswith('__or'):
					child_child_aggregate_query = {'$or':[]}
					self._compile_query_step(aggregate_prefix=aggregate_prefix, aggregate_suffix=aggregate_suffix, aggregate_match=child_child_aggregate_query['$or'], collection=collection, attrs=attrs, extns=extns, modules=modules, step=step[attr])
					if child_child_aggregate_query['$or'].__len__() == 1:
						child_aggregate_query['$and'].append(child_child_aggregate_query['$or'][0])
					elif child_child_aggregate_query['$or'].__len__() > 1:
						child_aggregate_query['$and'].append(child_child_aggregate_query['$or'])
				else:
					# [DOC] Add extn query when required
					if attr.find('.') != -1 and attr.split('.')[0] in extns.keys():
						step_attr = attr.split('.')[1]
						step_attrs = modules[extns[attr.split('.')[0]][0]].attrs

						# [DOC] Don't attempt to extn attr that is already extn'ed
						lookup_query = False
						for stage in aggregate_prefix:
							if '$lookup' in stage.keys() and stage['$lookup']['as'] == attr.split('.')[0]:
								lookup_query = True
								break
						if not lookup_query:
							extn_collection = modules[extns[attr.split('.')[0]][0]].collection
							aggregate_prefix.append({'$lookup':{'from':extn_collection, 'localField':attr.split('.')[0], 'foreignField':'_id', 'as':attr.split('.')[0]}})
							aggregate_prefix.append({'$unwind':'${}'.format(attr.split('.')[0])})
							group_query = {attr:{'$first':'${}'.format(attr)} for attr in attrs.keys()}
							group_query[attr.split('.')[0]] = {'$first':'${}._id'.format(attr.split('.')[0])}
							group_query['_id'] = '$_id'
							aggregate_suffix.append({'$group':group_query})
					else:
						step_attr = attr
						step_attrs = attrs

					# [DOC] Convert strings and lists of strings to ObjectId when required
					if step_attr in step_attrs.keys() and step_attrs[step_attr] == 'id':
						step[attr] = ObjectId(step[attr])
					elif step_attr in step_attrs.keys() and step_attrs[step_attr] == ['id']:
						if type(step[attr]) == list:
							step[attr] = [ObjectId(child_attr) for child_attr in step[attr]]
						elif type(step[attr]) == str:
							step[attr] = ObjectId(step[attr])
					elif step_attr == '_id':
						if type(step[attr]) == str:
							step[attr] = ObjectId(step[attr])
						elif type(step[attr]) == list:
							step[attr] = [ObjectId(child_attr) for child_attr in step[attr]]
					# [DOC] Check for access sepcial attrs
					elif step_attr in step_attrs.keys() and step_attrs[step_attr] == 'access':
						access_query = [
							{'$project':{
								'__user':'$user',
								'__access.anon':'${}.anon'.format(attr),
								'__access.users':{'$in':[ObjectId(step[attr]['$__user']), '${}.users'.format(attr)]},
								'__access.groups':{'$or':[{'$in':[group, '${}.groups'.format(attr)]} for group in step[attr]['$__groups']]}
							}},
							# {'$project':{
							# 	attr:{'$or':[{'__user':ObjectId(step[attr]['$__user'])}, {'__access.anon':True}, {'__access.users':True}, {'__access.groups':True}]}
							# }},
							{'$match':{'$or':[{'__user':ObjectId(step[attr]['$__user'])}, {'__access.anon':True}, {'__access.users':True}, {'__access.groups':True}]}}
						]
						access_query[0]['$project'].update({attr:'$'+attr for attr in attrs.keys()})
						# access_query[1]['$project'].update({attr:'$'+attr for attr in attrs.keys()})

						aggregate_prefix.append(access_query[0])
						# aggregate_prefix.append(access_query[1])
						# aggregate_suffix.insert(0, access_query[1])
						step[attr] = access_query[1]
					# [DOC] Check for $bet query oper
					if type(step[attr]) == dict and '$bet' in step[attr].keys():
						step[attr] = {'$gte':step[attr]['$bet'][0], '$lte':step[attr]['$bet'][1]}
					
					if type(step[attr]) == dict and '$match' in step[attr].keys():
						child_aggregate_query['$and'].append(step[attr]['$match'])
					else:
						child_aggregate_query['$and'].append({attr:step[attr]})
			if child_aggregate_query['$and'].__len__() == 1:
				aggregate_match.append(child_aggregate_query['$and'][0])
			elif child_aggregate_query['$and'].__len__() > 1:
				aggregate_match.append(child_aggregate_query)
		elif type(step) == list and step.__len__():
			child_aggregate_query = {'$or':[]}
			for child_step in step:
				self._compile_query_step(aggregate_prefix=aggregate_prefix, aggregate_suffix=aggregate_suffix, aggregate_match=child_aggregate_query['$or'], collection=collection, attrs=attrs, extns=extns, modules=modules, step=child_step)
			if child_aggregate_query['$or'].__len__() == 1:
				aggregate_match.append(child_aggregate_query['$or'][0])
			elif child_aggregate_query['$or'].__len__() > 1:
				aggregate_match.append(child_aggregate_query)
	
	@classmethod
	def read(self, env, session, collection, attrs, extns, modules, query):
		conn = env['conn']
		
		skip, limit, sort, group, aggregate_query = self._compile_query(collection=collection, attrs=attrs, extns=extns, modules=modules, query=query)
		
		logger.debug('aggregate_query: %s', aggregate_query)
		logger.debug('skip, limit, sort, group: %s, %s, %s, %s:', skip, limit, sort, group)

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

		if sort:
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
						{'_id':doc[extn]}
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
							{'_id':doc[extn][i]}
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

	@classmethod
	def create(self, env, session, collection, attrs, extns, modules, doc):
		conn = env['conn']
		collection = conn[collection]
		_id = collection.insert_one(doc).inserted_id
		return {
			'count':1,
			'docs':[BaseModel({'_id':_id})]
		}
	
	@classmethod
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
			# [DOC] Check for $add update oper
			if type(doc[attr]) == dict and '$add' in doc[attr].keys():
				if '$inc' not in update_doc.keys():
					update_doc['$inc'] = {}
				update_doc['$inc'][attr] = doc[attr]['$add']
				del_attrs.append(attr)
			# [DOC] Check for $push update oper
			elif type(doc[attr]) == dict and '$push' in doc[attr].keys():
				if '$push' not in update_doc.keys():
					update_doc['$push'] = {}
				update_doc['$push'][attr] = doc[attr]['$push']
				del_attrs.append(attr)
			# [DOC] Check for $pushUnique update oper
			elif type(doc[attr]) == dict and '$pushUnique' in doc[attr].keys():
				if '$addToSet' not in update_doc.keys():
					update_doc['$addToSet'] = {}
				update_doc['$addToSet'][attr] = doc[attr]['$pushUnique']
				del_attrs.append(attr)
			# [DOC] Check for $pull update oper
			elif type(doc[attr]) == dict and '$pull' in doc[attr].keys():
				if '$pullAll' not in update_doc.keys():
					update_doc['$pullAll'] = {}
				update_doc['$pullAll'][attr] = doc[attr]['$pull']
				del_attrs.append(attr)
		for del_attr in del_attrs:
			del doc[del_attr]
		if not list(update_doc['$set'].keys()).__len__():
			del update_doc['$set']
		logger.debug('Final update doc: %s', update_doc)
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
	
	@classmethod
	def delete(self, env, session, collection, attrs, extns, modules, query, strategy):
		conn = env['conn']
		# [DOC] Perform a read query to get all matching documents
		results = self.read(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query)
		# [DOC] Check strategy to cherrypick update, delete calls and system_docs
		if strategy in [DELETE_SOFT_SKIP_SYS, DELETE_SOFT_SYS]:
			if strategy == DELETE_SOFT_SKIP_SYS:
				docs = [doc._id for doc in results['docs'] if doc._id not in Config._sys_docs.keys()]
				if docs.__len__() != results['docs'].__len__():
					logger.warning('Skipped soft delete for system docs due to \'DELETE_SOFT_SKIP_SYS\' strategy.')
			else:
				logger.warning('Detected \'DELETE_SOFT_SYS\' strategy for delete call.')
				docs = [doc._id for doc in results['docs']]
			# [DOC] Perform update call on matching docs
			collection = conn[collection]
			update_doc = {'$set':{'__deleted':True}}
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
		elif strategy in [DELETE_FORCE_SKIP_SYS, DELETE_FORCE_SYS]:
			if strategy == DELETE_FORCE_SKIP_SYS:
				docs = [doc._id for doc in results['docs'] if doc._id not in Config._sys_docs.keys()]
				if docs.__len__() != results['docs'].__len__():
					logger.warning('Skipped soft delete for system docs due to \'DELETE_FORCE_SKIP_SYS\' strategy.')
			else:
				logger.warning('Detected \'DELETE_FORCE_SYS\' strategy for delete call.')
				docs = [doc._id for doc in results['docs']]
			# [DOC] Perform delete query on matching docs
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
				'docs':[{'_id':doc} for doc in docs]
			}
		else:
			return False
	
	@classmethod
	def drop(self, env, session, collection):
		conn = env['conn']
		collection = conn[collection]
		collection.drop()
		return True