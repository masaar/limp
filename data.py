from config import Config
from enums import Event, DELETE_STRATEGY
from utils import DictObj, Query
from base_model import BaseModel

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from typing import Dict, Union, List, Tuple, Any

import os, logging, re, datetime, copy
logger = logging.getLogger('limp')

class UnknownDeleteStrategyException(Exception):
	pass

class InvalidQueryException(Exception):
	pass

class Data():
	
	@classmethod
	def create_conn(cls) -> AsyncIOMotorClient:
		connection_config = {
			'ssl':Config.data_ssl
		}
		if Config.data_ca:
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			connection_config['ssl_ca_certs'] = os.path.join(__location__, '..', 'certs', Config.data_ca_name)
		# [DOC] Check for multiple servers
		if type(Config.data_server) == list:
			for data_server in Config.data_server:
				conn = AsyncIOMotorClient(data_server, **connection_config, connect=True)
				try:
					logger.debug('Check if data_server: %s isMaster.', data_server)
					results = conn.admin.command('ismaster')
					logger.debug('-Check results: %s', results)
					if results['ismaster']:
						# conn = conn[Config.data_name]
						break
				except Exception as err:
					logger.debug('Not master. Error: %s', err)
					pass
		elif type(Config.data_server) == str:
			# [DOC] If it's single server just connect directly
			conn = AsyncIOMotorClient(Config.data_server, **connection_config, connect=True) #[Config.data_name]
		return conn
	
	@classmethod
	def _compile_query(
				cls,
				collection: str,
				attrs: Dict[str, Union[str, List[str], Tuple[str]]],
				extns: Dict[str, List[Union[str, List[str]]]],
				modules: Dict[str, 'BaseModule'],
				query: Query,
				watch_mode: bool
			) -> Tuple[
				int,
				int,
				Dict[str, int],
				List[Dict[str, Union[str, int]]],
				List[Any]
			]:
		aggregate_prefix = [{'$match':{'$or':[{'__deleted':{'$exists':False}}, {'__deleted':False}]}}]
		aggregate_suffix = []
		aggregate_query = [{'$match':{'$and':[]}}]
		aggregate_match = aggregate_query[0]['$match']['$and']
		skip: int = None
		limit: int = None
		sort: Dict[str, int] = {'_id':-1}
		group: List[Dict[str, Union[str, int]]] = None
		logger.debug('attempting to parse query: %s', query)

		if not isinstance(query, Query):
			raise InvalidQueryException(f'Query of type \'{type(query)}\' is invalid.')

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
			cls._compile_query_step(aggregate_prefix=aggregate_prefix, aggregate_suffix=aggregate_suffix, aggregate_match=aggregate_match, collection=collection, attrs=attrs, extns=extns, modules=modules, step=step, watch_mode=watch_mode)
		
		if '$attrs' in query and type(query['$attrs']) == list:
			aggregate_suffix.append({
				'$group':{'_id':'$_id', **{attr:{
					'$first':f'${attr}'
				} for attr in query['$attrs'] if attr in attrs.keys()}}
			})
		else:
			aggregate_suffix.append({
				'$group':{'_id':'$_id', **{attr:{
					'$first':f'${attr}'
				} for attr in attrs.keys()}}
			})
		
		logger.debug('parsed query, aggregate_prefix: %s, aggregate_suffix: %s, aggregate_match:%s', aggregate_prefix, aggregate_suffix, aggregate_match)
		if len(aggregate_match) == 1:
			aggregate_query = [{'$match':aggregate_match[0]}]
		elif len(aggregate_match) == 0:
			aggregate_query = []

		aggregate_query = aggregate_prefix + aggregate_query + aggregate_suffix
		return (skip, limit, sort, group, aggregate_query)
	
	@classmethod
	def _compile_query_step(
				cls,
				aggregate_prefix: List[Any],
				aggregate_suffix: List[Any],
				aggregate_match: List[Any],
				collection: str,
				attrs: Dict[str, Union[str, List[str], Tuple[str]]],
				extns: Dict[str, List[Union[str, List[str]]]],
				modules: Dict[str, 'BaseModule'],
				step: Union[Dict, List],
				watch_mode: bool
			) -> None:
		if type(step) == dict and len(step.keys()):
			child_aggregate_query = {'$and':[]}
			for attr in step.keys():
				if attr.startswith('__or'):
					child_child_aggregate_query = {'$or':[]}
					cls._compile_query_step(aggregate_prefix=aggregate_prefix, aggregate_suffix=aggregate_suffix, aggregate_match=child_child_aggregate_query['$or'], collection=collection, attrs=attrs, extns=extns, modules=modules, step=step[attr], watch_mode=watch_mode)
					if len(child_child_aggregate_query['$or']) == 1:
						child_aggregate_query['$and'].append(child_child_aggregate_query['$or'][0])
					elif len(child_child_aggregate_query['$or']) > 1:
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
						try:
							if type(step[attr]) == dict and '$in' in step[attr].keys():
								step[attr] = {'$in':[ObjectId(child_attr) for child_attr in step[attr]['$in']]}
							elif type(step[attr]) == str:
								step[attr] = ObjectId(step[attr])
						except:
							logger.warning('Failed to convert attr to id type: %s', step[attr])
					elif step_attr in step_attrs.keys() and step_attrs[step_attr] == ['id']:
						try:
							if type(step[attr]) == list:
								step[attr] = [ObjectId(child_attr) for child_attr in step[attr]]
							elif type(step[attr]) == dict and '$in' in step[attr].keys():
								step[attr] = {'$in':[ObjectId(child_attr) for child_attr in step[attr]['$in']]}
							elif type(step[attr]) == str:
								step[attr] = ObjectId(step[attr])
						except:
							logger.warning('Failed to convert attr to id type: %s', step[attr])
					elif step_attr == '_id':
						try:
							if type(step[attr]) == str:
								step[attr] = ObjectId(step[attr])
							elif type(step[attr]) == list:
								step[attr] = [ObjectId(child_attr) for child_attr in step[attr]]
							elif type(step[attr]) == dict and '$in' in step[attr].keys():
								step[attr] = {'$in':[ObjectId(child_attr) for child_attr in step[attr]['$in']]}
						except:
							logger.warning('Failed to convert attr to id type: %s', step[attr])
					# [DOC] Check for access sepcial attrs
					elif step_attr in step_attrs.keys() and step_attrs[step_attr] == 'access':
						access_query = [
							{'$project':{
								'__user':'$user',
								'__access.anon':'${}.anon'.format(attr),
								'__access.users':{'$in':[ObjectId(step[attr]['$__user']), '${}.users'.format(attr)]},
								'__access.groups':{'$or':[{'$in':[group, '${}.groups'.format(attr)]} for group in step[attr]['$__groups']]}
							}},
							{'$match':{'$or':[{'__user':ObjectId(step[attr]['$__user'])}, {'__access.anon':True}, {'__access.users':True}, {'__access.groups':True}]}}
						]
						access_query[0]['$project'].update({attr:'$'+attr for attr in attrs.keys()})

						aggregate_prefix.append(access_query[0])
						step[attr] = access_query[1]
					# [DOC] Check for $bet query oper
					if type(step[attr]) == dict and '$bet' in step[attr].keys():
						step[attr] = {'$gte':step[attr]['$bet'][0], '$lte':step[attr]['$bet'][1]}
					
					if type(step[attr]) == dict and '$match' in step[attr].keys():
						child_aggregate_query['$and'].append(step[attr]['$match'])
					else:
						if watch_mode:
							child_aggregate_query['$and'].append({f'fullDocument.{attr}':step[attr]})
						else:
							child_aggregate_query['$and'].append({attr:step[attr]})
			if len(child_aggregate_query['$and']) == 1:
				aggregate_match.append(child_aggregate_query['$and'][0])
			elif len(child_aggregate_query['$and']) > 1:
				aggregate_match.append(child_aggregate_query)
		elif type(step) == list and len(step):
			child_aggregate_query = {'$or':[]}
			for child_step in step:
				cls._compile_query_step(aggregate_prefix=aggregate_prefix, aggregate_suffix=aggregate_suffix, aggregate_match=child_aggregate_query['$or'], collection=collection, attrs=attrs, extns=extns, modules=modules, step=child_step, watch_mode=watch_mode)
			if len(child_aggregate_query['$or']) == 1:
				aggregate_match.append(child_aggregate_query['$or'][0])
			elif len(child_aggregate_query['$or']) > 1:
				aggregate_match.append(child_aggregate_query)
	
	@classmethod
	async def _process_results_doc(
				cls,
				env: Dict[str, Any],
				collection: str,
				attrs: Dict[str, Union[str, List[str], Tuple[str]]],
				extns: Dict[str, List[Union[str, List[str]]]],
				modules: Dict[str, 'BaseModule'],
				query: Query,
				doc: Dict[str, Any],
				extn_models: Dict[str, 'BaseModel'] = {}
			) -> Dict[str, Any]:
		# [DOC] Process doc attrs
		for attr in attrs.keys():
			if attrs[attr] == 'locale':
				if type(doc[attr]) == dict and Config.locale in doc[attr].keys():
					doc[attr] = {locale:doc[attr][locale] if locale in doc[attr].keys() else doc[attr][Config.locale] for locale in Config.locales}
		# [DOC] Attempt to extned the doc per extns
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
				if not (len(extns[extn]) == 3 and extns[extn][2] == True):
					skip_events.append(Event.__EXTN__)
				# [DOC] Read doc if not in extn_models
				if str(doc[extn]) not in extn_models.keys():
					extn_results = await extn_module.methods['read'](skip_events=skip_events, env=env, query=[
						{'_id':doc[extn]}
					])
					if extn_results['args']['count']:
						extn_models[str(doc[extn])] = extn_results['args']['docs'][0]
					else:
						extn_models[str(doc[extn])] = None
				# [DOC] Set attr to extn_models doc
				doc[extn] = copy.deepcopy(extn_models[str(doc[extn])])
				if doc[extn]:
					# [DOC] delete all unneeded keys from the resulted doc
					del_attrs = []
					for attr in doc[extn]._attrs().keys():
						if attr not in extn_attrs.keys():
							del_attrs.append(attr)
					for attr in del_attrs:
						del doc[extn][attr]
			elif attrs[extn] == ['id']:
				# [DOC] In case value is null, do not attempt to extend doc
				if not doc[extn]: continue
				# [DOC] Loop over every _id in the extn array
				for i in range(0, len(doc[extn])):
					# [DOC] In case value is null, do not attempt to extend doc
					if not doc[extn][i]: continue
					# [DOC] Read doc if not in extn_models
					if str(doc[extn][i]) not in extn_models.keys():
						extn_results = await extn_module.methods['read'](skip_events=[Event.__PERM__, Event.__EXTN__], env=env, query=[
							{'_id':doc[extn][i]}
						])
						if extn_results['args']['count']:
							extn_models[str(doc[extn][i])] = extn_results['args']['docs'][0]
						else:
							extn_models[str(doc[extn][i])] = None
					# [DOC] Set attr to extn_models doc
					doc[extn][i] = copy.deepcopy(extn_models[str(doc[extn][i])])
					if doc[extn][i]:
						# [DOC] delete all unneeded keys from the resulted doc
						del_attrs = []
						for attr in doc[extn][i]._attrs().keys():
							if attr not in extn_attrs.keys():
								del_attrs.append(attr)
						# logger.debug('extn del_attrs: %s against: %s.', del_attrs, extn_attrs)
						for attr in del_attrs:
							del doc[extn][i][attr]
		return doc

	@classmethod
	async def read(
				cls,
				env: Dict[str, Any],
				collection: str,
				attrs: Dict[str, Union[str, List[str], Tuple[str]]],
				extns: Dict[str, List[Union[str, List[str]]]],
				modules: Dict[str, 'BaseModule'],
				query: Query,
				skip_process: bool = False
			) -> Dict[str, Any]:
		skip, limit, sort, group, aggregate_query = cls._compile_query(collection=collection, attrs=attrs, extns=extns, modules=modules, query=query, watch_mode=False)
		
		logger.debug('aggregate_query: %s', aggregate_query)
		logger.debug('skip, limit, sort, group: %s, %s, %s, %s.', skip, limit, sort, group)

		collection = env['conn'][Config.data_name][collection]
		docs_total_results = collection.aggregate(aggregate_query + [{'$count':'__docs_total'}])
		try:
			async for doc in docs_total_results:
				docs_total = doc['__docs_total']
			docs_total
		except:
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
				for i in range(0, len(group_query)):
					if list(group_query[i].keys())[0] == '$match' and list(group_query[i]['$match'].keys())[0] == group_condition['by']:
						check_group = True
						break
				if check_group:
					del group_query[i]
				group_query = collection.aggregate(group_query)
				groups[group_condition['by']] = [{'min':group['_id']['min'], 'max':group['_id']['max'], 'count':group['count']} async for group in group_query]

		if sort:
			aggregate_query.append({'$sort':sort})
		if skip:
			aggregate_query.append({'$skip':skip})
		if limit:
			aggregate_query.append({'$limit':limit})
		
		logger.debug('final query: %s, %s.', collection, aggregate_query)

		docs_count_results = collection.aggregate(aggregate_query + [{'$count':'__docs_count'}])
		try:
			async for doc in docs_count_results:
				docs_count = doc['__docs_count']
			docs_count
		except:
			return {
				'total':docs_total,
				'count':0,
				'docs':[],
				'groups': {} if not group else groups
			}
		docs = collection.aggregate(aggregate_query)
		models = []
		extn_models = {}
		async for doc in docs:
			if not skip_process:
				doc = await cls._process_results_doc(env=env, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query, doc=doc, extn_models=extn_models)
			if doc:
				models.append(BaseModel(doc))
		return {
			'total':docs_total,
			'count':docs_count,
			'docs':models,
			'groups': {} if not group else groups
		}
	
	@classmethod
	async def watch(
				cls,
				env: Dict[str, Any],
				collection: str,
				attrs: Dict[str, Union[str, List[str], Tuple[str]]],
				extns: Dict[str, List[Union[str, List[str]]]],
				modules: Dict[str, 'BaseModule'],
				query: Query
			) -> Dict[str, Any]:
		aggregate_query = cls._compile_query(collection=collection, attrs=attrs, extns=extns, modules=modules, query=query, watch_mode=True)[4]

		collection = env['conn'][Config.data_name][collection]

		logger.debug('Preparing generator at Data')
		async with collection.watch(pipeline=aggregate_query, full_document='updateLookup') as stream:
			yield {
				'stream':stream
			}
			async for change in stream:
				logger.debug('Detected change at Data: %s', change)

				oper = change['operationType']
				if oper in ['insert', 'replace', 'update']:
					if oper == 'insert': oper = 'create'
					elif oper == 'replace': oper = 'update'
					doc = await cls._process_results_doc(env=env, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query, doc=change['fullDocument'])
					model = BaseModel(doc)
				elif oper == 'delete':
					model = BaseModel({'_id':change['documentKey']['_id']})

				yield {
					'count':1,
					'oper':oper,
					'docs':[model]
				}
		
		logger.debug('changeStream has been close. Generator ended at Data')

	@classmethod
	async def create(
				cls,
				env: Dict[str, Any],
				collection: str,
				attrs: Dict[str, Union[str, List[str], Tuple[str]]],
				modules: Dict[str, 'BaseModule'],
				doc: Dict[str, Any]
			) -> Dict[str, Any]:
		collection = env['conn'][Config.data_name][collection]
		results = await collection.insert_one(doc)
		_id = results.inserted_id
		return {
			'count':1,
			'docs':[BaseModel({'_id':_id})]
		}
	
	@classmethod
	async def update(
				cls,
				env: Dict[str, Any],
				collection: str,
				attrs: Dict[str, Union[str, List[str], Tuple[str]]],
				modules: Dict[str, 'BaseModule'],
				docs: List[str],
				doc: Dict[str, Any]
			) -> Dict[str, Any]:
		# [DOC] Recreate docs list by converting all docs items to ObjectId
		docs = [ObjectId(doc) for doc in docs]
		# [DOC] Perform update query on matching docs
		collection = env['conn'][Config.data_name][collection]
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
			# [DOC] Check for $push_unique update oper
			elif type(doc[attr]) == dict and '$push_unique' in doc[attr].keys():
				if '$addToSet' not in update_doc.keys():
					update_doc['$addToSet'] = {}
				update_doc['$addToSet'][attr] = doc[attr]['$push_unique']
				del_attrs.append(attr)
			# [DOC] Check for $pull update oper
			elif type(doc[attr]) == dict and '$pull' in doc[attr].keys():
				if '$pullAll' not in update_doc.keys():
					update_doc['$pullAll'] = {}
				update_doc['$pullAll'][attr] = doc[attr]['$pull']
				del_attrs.append(attr)
		for del_attr in del_attrs:
			del doc[del_attr]
		if not len(list(update_doc['$set'].keys())):
			del update_doc['$set']
		logger.debug('Final update doc: %s', update_doc)
		# [DOC] If using Azure Mongo service update docs one by one
		if Config.data_azure_mongo:
			update_count = 0
			for _id in docs:
				results = await collection.update_one({'_id':_id}, update_doc)
				update_count += results.modified_count
		else:
			results = await collection.update_many({'_id':{'$in':docs}}, update_doc)
			update_count = results.modified_count
		return {
			'count':update_count,
			'docs':[{'_id':doc} for doc in docs]
		}
	
	@classmethod
	async def delete(
				cls,
				env: Dict[str, Any],
				collection: str,
				attrs: Dict[str, Union[str, List[str], Tuple[str]]],
				modules: Dict[str, 'BaseModule'],
				docs: List[str],
				strategy: DELETE_STRATEGY
			) -> Dict[str, Any]:
		# [DOC] Check strategy to cherrypick update, delete calls and system_docs
		if strategy in [DELETE_STRATEGY.SOFT_SKIP_SYS, DELETE_STRATEGY.SOFT_SYS]:
			if strategy == DELETE_STRATEGY.SOFT_SKIP_SYS:
				del_docs = [ObjectId(doc) for doc in docs if ObjectId(doc) not in Config._sys_docs.keys()]
				if len(del_docs) != len(docs):
					logger.warning('Skipped soft delete for system docs due to \'DELETE_SOFT_SKIP_SYS\' strategy.')
			else:
				logger.warning('Detected \'DELETE_SOFT_SYS\' strategy for delete call.')
				del_docs = [ObjectId(doc) for doc in docs]
			# [DOC] Perform update call on matching docs
			collection = env['conn'][Config.data_name][collection]
			update_doc = {'$set':{'__deleted':True}}
			# [DOC] If using Azure Mongo service update docs one by one
			if Config.data_azure_mongo:
				update_count = 0
				for _id in docs:
					results = await collection.update_one({'_id':_id}, update_doc)
					update_count += results.modified_count
			else:
				results = await collection.update_many({'_id':{'$in':docs}}, update_doc)
				update_count = results.modified_count
			return {
				'count':update_count,
				'docs':[{'_id':doc} for doc in docs]
			}
		elif strategy in [DELETE_STRATEGY.FORCE_SKIP_SYS, DELETE_STRATEGY.FORCE_SYS]:
			if strategy == DELETE_STRATEGY.FORCE_SKIP_SYS:
				del_docs = [ObjectId(doc) for doc in docs if ObjectId(doc) not in Config._sys_docs.keys()]
				if len(del_docs) != len(docs):
					logger.warning('Skipped soft delete for system docs due to \'DELETE_FORCE_SKIP_SYS\' strategy.')
			else:
				logger.warning('Detected \'DELETE_FORCE_SYS\' strategy for delete call.')
				del_docs = [ObjectId(doc) for doc in docs]
			# [DOC] Perform delete query on matching docs
			collection = env['conn'][Config.data_name][collection]
			if Config.data_azure_mongo:
				delete_count = 0
				for _id in del_docs:
					results = await collection.delete_one({'_id':_id})
					delete_count += results.deleted_count
			else:
				results = await collection.delete_many({'_id':{'$in':del_docs}})
				delete_count = results.deleted_count
			return {
				'count':delete_count,
				'docs':[{'_id':doc} for doc in docs]
			}
		else:
			raise UnknownDeleteStrategyException(f'DELETE_STRATEGY \'{strategy}\' is unknown.')
	
	@classmethod
	async def drop(
				cls,
				env: Dict[str, Any],
				collection: str,
			) -> True:
		collection = env['conn'][Config.data_name][collection]
		await collection.drop()
		return True