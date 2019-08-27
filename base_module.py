from config import Config
from event import Event
from data import Data, DELETE_SOFT_SKIP_SYS, DELETE_SOFT_SYS, DELETE_FORCE_SKIP_SYS, DELETE_FORCE_SYS
from utils import DictObj, validate_doc, InvalidAttrException, MissingAttrException, ConvertAttrException, Query
from base_model import BaseModel
from base_method import BaseMethod

from typing import List, Dict, Union, Tuple, Any

from PIL import Image
from bson import ObjectId
import traceback, logging, datetime, re, sys, io, copy

logger = logging.getLogger('limp')

class BaseModule:
	collection: Union[str, bool]
	proxy: str
	attrs: Dict[str, Union[str, List[str], Tuple[str]]]
	diff: bool
	defaults: Dict[str, Any]
	unique_attrs: List[str]
	extns: Dict[str, List[Union[str, List[str]]]]
	privileges: List[str]
	methods: Dict[str, 'BaseMethod']
	cache: List[Dict[str, Any]]

	package_name: str
	module_name: str
	modules: Dict[str, 'BaseModule']

	def __init__(self):
		if not getattr(self, 'collection', None):
			self.collection = False
		if not getattr(self, 'proxy', None):
			self.proxy = False
		if not getattr(self, 'attrs', None):
			self.attrs = {}
		if not getattr(self, 'diff', None):
			self.diff = False
		if not getattr(self, 'defaults', None):
			self.defaults = {}
		if not getattr(self, 'unique_attrs', None):
			self.unique_attrs = []
		if not getattr(self, 'extns', None):
			self.extns = {}
		if not getattr(self, 'privileges', None):
			self.privileges = ['read', 'create', 'update', 'delete', 'admin']
		if not getattr(self, 'methods', None):
			self.methods = {}
		if not getattr(self, 'cache', None):
			self.cache = []
		
		self.modules = {}
		
		# [DOC] Populate package and module names for in-context use.
		self.package_name = self.__module__.replace('modules.', '').upper().split('.')[0]
		self.module_name = re.sub(r'([A-Z])', r'_\1', self.__class__.__name__[0].lower() + self.__class__.__name__[1:]).lower()
	
	def __initilise(self):
		# [DOC] Abstract methods as BaseMethod objects
		for method in self.methods.keys():
			# [DOC] Check method query_args attr, set it or update it if required.
			if 'query_args' not in self.methods[method].keys():
				self.methods[method]['query_args'] = False
			elif type(self.methods[method]['query_args']) == dict:
				self.methods[method]['query_args'] = [self.methods[method]['query_args']]
			# [DOC] Check method doc_args attr, set it or update it if required.
			if 'doc_args' not in self.methods[method].keys():
				self.methods[method]['doc_args'] = False
			elif type(self.methods[method]['doc_args']) == dict:
				self.methods[method]['doc_args'] = [self.methods[method]['doc_args']]
			# [DOC] Check method get_method attr, set it or update it if required.
			if 'get_method' not in self.methods[method].keys() or self.methods[method]['get_method'] == False:
				self.methods[method]['get_method'] = False
				self.methods[method]['get_args'] = False
			elif self.methods[method]['get_method'] == True:
				if 'get_args' not in self.methods[method].keys():
					if method == 'retrieve_file':
						self.methods[method]['get_args'] = [
							{'_id':'id', 'attr':'str', 'filename':'str'},
							{'_id':'id', 'attr':'str', 'thumb':'str[[0-9]+x[0-9]+]', 'filename':'str'}
						]
					else:
						self.methods[method]['get_args'] = [{'_id':'id', 'var':'str'}]
				elif type(self.methods[method]['get_args']) == dict:
					self.methods[method]['get_args'] = [self.methods[method]['get_args']]
			# [DOC] Initlise method as BaseMethod
			self.methods[method] = BaseMethod(
				module=self,
				method=method,
				permissions=self.methods[method]['permissions'],
				query_args=self.methods[method]['query_args'],
				doc_args=self.methods[method]['doc_args'],
				get_method=self.methods[method]['get_method'],
				get_args=self.methods[method]['get_args']
			)
		logger.debug('Initialised module %s', self.module_name)

	def update_modules(self, modules):
		self.modules = modules
		# [DOC] Check for proxy
		if self.proxy:
			logger.debug('Module \'%s\' is a proxy module. Updating.', self.module_name)
			# [DOC] Copy regular attrs
			self.collection = self.modules[self.proxy].collection
			self.attrs = copy.deepcopy(self.modules[self.proxy].attrs)
			self.diff = self.modules[self.proxy].diff
			self.defaults = copy.deepcopy(self.modules[self.proxy].defaults)
			self.unique_attrs = copy.deepcopy(self.modules[self.proxy].unique_attrs)
			self.extns = copy.deepcopy(self.modules[self.proxy].extns)
			self.privileges = copy.deepcopy(self.modules[self.proxy].privileges)
			# [DOC] Update methods from original module
			for method in self.modules[self.proxy].methods.keys():
				# [DOC] Copy method attrs if not present in proxy
				if method not in self.methods.keys():
					if type(self.modules[self.proxy].methods[method]) == dict:
						self.methods[method] = copy.deepcopy(self.modules[self.proxy].methods[method])
					elif type(self.modules[self.proxy].methods[method]) == BaseMethod:
						self.methods[method] = {
							'permissions':copy.deepcopy(self.modules[self.proxy].methods[method].permissions),
							'query_args':copy.deepcopy(self.modules[self.proxy].methods[method].query_args),
							'doc_args':copy.deepcopy(self.modules[self.proxy].methods[method].doc_args),
							'get_method':self.modules[self.proxy].methods[method].get_method
						}
				# [DOC] Create methods functions in proxy module if not present
				if not getattr(self, method, None):
					setattr(self, method, lambda self=self, skip_events=[], env={}, query=[], doc={}: getattr(self.modules[self.proxy], method)(skip_events=skip_events, env=env, query=query, doc=doc))
		# [DOC] Initlise module
		self.__initilise()
			
	
	def __getattribute__(self, attr):
		# [DOC] Module is not yet initialised, skip to return exact attr
		try:
			object.__getattribute__(self, 'methods')
		except AttributeError:
			return object.__getattribute__(self, attr)
		# [DOC] Module is initialised attempt to check for methods
		if attr in object.__getattribute__(self, 'methods').keys():
			return object.__getattribute__(self, 'methods')[attr]
		elif attr.startswith('_method_'):
			return object.__getattribute__(self, attr.replace('_method_', ''))
		else:
			return object.__getattribute__(self, attr)

	def pre_read(self, skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (skip_events, env, query, doc)
	def on_read(self, results: Dict[str, Any], skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (Dict[str, Any], List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (results, skip_events, env, query, doc)
	def read(self, skip_events: List[str]=[], env: Dict[str, Any]={}, query: Query=[], doc: Dict[str, Any]={}) -> DictObj:
		if Event.__PRE__ not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module pre_read
				pre_read = self.modules[self.proxy].pre_read(skip_events=skip_events, env=env, query=query, doc=doc)
				if type(pre_read) in [DictObj, dict]: return pre_read
				skip_events, env, query, doc = pre_read
			pre_read = self.pre_read(skip_events=skip_events, env=env, query=query, doc=doc)
			if type(pre_read) in [DictObj, dict]: return pre_read
			skip_events, env, query, doc = pre_read
		if Event.__EXTN__ in skip_events:
			results = Data.read(env=env, collection=self.collection, attrs=self.attrs, extns={}, modules=self.modules, query=query)
		elif '$extn' in query and type(query['$extn']) == list:
			results = Data.read(env=env, collection=self.collection, attrs=self.attrs, extns={
				extn:self.extns[extn] for extn in self.extns.keys() if extn in query['$extn']
			}, modules=self.modules, query=query)
		else:
			# [DOC] Check for cache workflow instructins
			if self.cache:
				results = False
				for cache_set in self.cache:
					if cache_set['condition'](skip_events=skip_events, env=env, query=query) == True:
						cache_key = str(query._query) + str(query._special)
						if 'queries' not in cache_set.keys():
							cache_set['queries'] = {}
							if not results:
								results = Data.read(env=env, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query)
							cache_set['queries'][cache_key] = {
								'results':results,
								'query_time':datetime.datetime.utcnow()
							}
						else:
							if cache_key in cache_set['queries'].keys():
								if 'period' in cache_set.keys():
									if (cache_set['queries'][cache_key]['query_time'] + datetime.timedelta(seconds=cache_set['period'])) < datetime.datetime.utcnow():
										if not results:
											results = Data.read(env=env, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query)
										cache_set['queries'][cache_key] = {
											'results':results,
											'query_time':datetime.datetime.utcnow()
										}
									else:
										results = cache_set['queries'][cache_key]['results']
										results['cache'] = cache_set['queries'][cache_key]['query_time'].isoformat()
								else:
									results = cache_set['queries'][cache_key]['results']
									results['cache'] = cache_set['queries'][cache_key]['query_time'].isoformat()
							else:
								if not results:
									results = Data.read(env=env, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query)
								cache_set['queries'][cache_key] = {
									'results':results,
									'query_time':datetime.datetime.utcnow()
								}
				if not results:
					results = Data.read(env=env, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query)
			else:
				results = Data.read(env=env, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query)
		if Event.__ON__ not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module on_read
				on_read = self.modules[self.proxy].on_read(results=results, skip_events=skip_events, env=env, query=query, doc=doc)
				if type(on_read) in [DictObj, dict]: return on_read
				results, skip_events, env, query, doc = on_read
			on_read = self.on_read(results=results, skip_events=skip_events, env=env, query=query, doc=doc)
			if type(on_read) in [DictObj, dict]: return on_read
			results, skip_events, env, query, doc = on_read
			# [DOC] if $attrs query arg is present return only required keys.
			if '$attrs' in query:
				query['$attrs'].insert(0, '_id')
				for i in range(0, results['docs'].__len__()):
					results['docs'][i] = BaseModel({attr:results['docs'][i][attr] for attr in query['$attrs'] if attr in results['docs'][i]._attrs()})

		return {
			'status':200,
			'msg':'Found {} docs.'.format(results['count']),
			'args':results
		}
	
	def pre_create(self, skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (skip_events, env, query, doc)
	def on_create(self, results: Dict[str, Any], skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (Dict[str, Any], List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (results, skip_events, env, query, doc)
	def create(self, skip_events: List[str]=[], env: Dict[str, Any]={}, query: Query=[], doc: Dict[str, Any]={}) -> DictObj:
		if Event.__PRE__ not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module pre_create
				pre_create = self.modules[self.proxy].pre_create(skip_events=skip_events, env=env, query=query, doc=doc)
				if type(pre_create) in [DictObj, dict]: return pre_create
				skip_events, env, query, doc = pre_create
			pre_create = self.pre_create(skip_events=skip_events, env=env, query=query, doc=doc)
			if type(pre_create) in [DictObj, dict]: return pre_create
			skip_events, env, query, doc = pre_create
		# [DOC] Deleted all extra doc args
		del_args = []
		for arg in doc.keys():
			if arg not in self.attrs.keys() and (arg != '_id' and type(doc[arg]) != ObjectId):
				del_args.append(arg)
		for arg in del_args:
			del doc[arg]
		# [DOC] Append host_add, user_agent, create_time, diff if it's present in attrs.
		if 'user' in self.attrs.keys() and 'host_add' not in doc.keys() and env['session'] and Event.__ARGS__ not in skip_events:
			doc['user'] = env['session'].user._id
		if 'create_time' in self.attrs.keys():
			doc['create_time'] = datetime.datetime.utcnow().isoformat()
		if 'host_add' in self.attrs.keys() and 'host_add' not in doc.keys():
			doc['host_add'] = env['REMOTE_ADDR']
		if 'user_agent' in self.attrs.keys() and 'user_agent' not in doc.keys():
			doc['user_agent'] = env['HTTP_USER_AGENT']
		if Event.__ARGS__ not in skip_events:
			# [DOC] Check presence and validate all attrs in doc args
			try:
				validate_doc(doc=doc, attrs=self.attrs, defaults=self.defaults)
			except MissingAttrException as e:
				return {
					'status':400,
					'msg':'{} for \'create\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
					'args':{'code':'{}_{}_MISSING_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
				}
			except InvalidAttrException as e:
				return {
					'status':400,
					'msg':'{} for \'create\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
					'args':{'code':'{}_{}_INVALID_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
				}
			except ConvertAttrException as e:
				return {
					'status':400,
					'msg':'{} for \'create\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
					'args':{'code':'{}_{}_CONVERT_INVALID_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
				}
			# [DOC] Check unique_attrs
			if self.unique_attrs:
				unique_results = self.read(skip_events=[Event.__PERM__], env=env, query=[[{attr:doc[attr]} for attr in self.unique_attrs], {'$limit':1}])
				if unique_results.args.count: # pylint: disable=no-member
					return {
						'status':400,
						'msg':'A doc with the same \'{}\' already exists.'.format('\', \''.join(self.unique_attrs)),
						'args':{'code':'{}_{}_DUPLICATE_DOC'.format(self.package_name.upper(), self.module_name.upper())}
					}
		# [DOC] Execute Data driver create
		results = Data.create(env=env, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, doc=doc)
		if Event.__ON__ not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module on_create
				on_create = self.modules[self.proxy].on_create(results=results, skip_events=skip_events, env=env, query=query, doc=doc)
				if type(on_create) in [DictObj, dict]: return on_create
				results, skip_events, env, query, doc = on_create
			on_create = self.on_create(results=results, skip_events=skip_events, env=env, query=query, doc=doc)
			if type(on_create) in [DictObj, dict]: return on_create
			results, skip_events, env, query, doc = on_create
		# [DOC] create soft action is to only retrurn the new created doc _id.
		if Event.__SOFT__ in skip_events:
			results = self.methods['read'](skip_events=[Event.__PERM__], env=env, query=[[{'_id':results['docs'][0]}]])
			results = results['args']

		# [DOC] Module collection is updated, delete_cache
		self.delete_cache()

		return {
			'status':200,
			'msg':'Created {} docs.'.format(results['count']),
			'args':results
		}
	
	def pre_update(self, skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (skip_events, env, query, doc)
	def on_update(self, results: Dict[str, Any], skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (Dict[str, Any], List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (results, skip_events, env, query, doc)
	def update(self, skip_events: List[str]=[], env: Dict[str, Any]={}, query: Query=[], doc: Dict[str, Any]={}) -> DictObj:
		if Event.__PRE__ not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module pre_update
				pre_update = self.modules[self.proxy].pre_update(skip_events=skip_events, env=env, query=query, doc=doc)
				if type(pre_update) in [DictObj, dict]: return pre_update
				skip_events, env, query, doc = pre_update
			pre_update = self.pre_update(skip_events=skip_events, env=env, query=query, doc=doc)
			if type(pre_update) in [DictObj, dict]: return pre_update
			skip_events, env, query, doc = pre_update
		# [DOC] Check presence and validate all attrs in doc args
		try:
			validate_doc(doc=doc, attrs=self.attrs, allow_opers=True, allow_none=True)
		except MissingAttrException as e:
			return {
				'status':400,
				'msg':'{} for \'update\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
				'args':{'code':'{}_{}_MISSING_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
			}
		except InvalidAttrException as e:
			return {
				'status':400,
				'msg':'{} for \'update\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
				'args':{'code':'{}_{}_INVALID_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
			}
		except ConvertAttrException as e:
			return {
				'status':400,
				'msg':'{} for \'update\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
				'args':{'code':'{}_{}_CONVERT_INVALID_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
			}
		# [DOC] Delete all attrs not belonging to the doc
		del_args = []
		for arg in doc.keys():
			# [DOC] When checken if the arg is an attr split it with '.' to make sure you check only top level attrs.
			if arg.split('.')[0] not in self.attrs.keys() or doc[arg] == None:
				del_args.append(arg)
		for arg in del_args:
			del doc[arg]
		# [DOC] Check if there is anything yet to update
		if not doc.keys().__len__():
			return {
				'status':200,
				'msg':'Nothing to update.',
				'args':{}
			}
		# [DOC] Find which docs are to be updated
		docs_results = results = Data.read(env=env, collection=self.collection, attrs=self.attrs, extns={}, modules=self.modules, query=query)
		# [DOC] Check unique_attrs
		if self.unique_attrs and sum([1 if attr in doc.keys() else 0 for attr in self.unique_attrs]) > 0:
			# [DOC] If any of the unique_attrs is present in doc, and docs_results is > 1, we have duplication
			if len(docs_results['docs']) > 1:
				return {
					'status':400,
					'msg':'Update call query has more than one doc as results. This would result in duplication.',
					'args':{'code':'{}_{}_MULTI_DUPLICATE'.format(self.package_name.upper(), self.module_name.upper())}
				}
			else:
				unique_results = self.read(skip_events=[Event.__PERM__], env=env, query=[
					[{attr:doc[attr]} for attr in self.unique_attrs if attr in doc.keys()],
					{'_id':{'$not':{'$in':[doc._id for doc in docs_results['docs']]}}},
					{'$limit':1}
				])
				if unique_results.args.count: # pylint: disable=no-member
					return {
						'status':400,
						'msg':'A doc with the same \'{}\' already exists.'.format('\', \''.join(self.unique_attrs)),
						'args':{'code':'{}_{}_DUPLICATE_DOC'.format(self.package_name.upper(), self.module_name.upper())}
					}
		results = Data.update(env=env, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, docs=[doc._id for doc in docs_results['docs']], doc=doc)
		if Event.__ON__ not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module on_update
				on_update = self.modules[self.proxy].on_update(results=results, skip_events=skip_events, env=env, query=query, doc=doc)
				if type(on_update) in [DictObj, dict]: return on_update
				results, skip_events, env, query, doc = on_update
			on_update = self.on_update(results=results, skip_events=skip_events, env=env, query=query, doc=doc)
			if type(on_update) in [DictObj, dict]: return on_update
			results, skip_events, env, query, doc = on_update
		# [DOC] If at least one doc updated, and module has diff enabled, and __DIFF__ not skippend:
		if results['count'] and self.diff and Event.__DIFF__ not in skip_events:
			# [DOC] If diff is a list, make sure the updated fields are not in the execluded list.
			if type(self.diff) == list:
				for attr in doc.keys():
					# [DOC] If at least on attr is not in the execluded list, create diff doc.
					if attr not in self.diff:
						diff_results = self.modules['diff'].methods['create'](skip_events=[Event.__PERM__], env=env, query=query, doc={
							'module':self.module_name,
							'vars':doc
						})
						logger.debug('diff results: %s', diff_results)
						break
			else:
				diff_results = self.modules['diff'].methods['create'](skip_events=[Event.__PERM__], env=env, query=query, doc={
					'module':self.module_name,
					'vars':doc
				})
				logger.debug('diff results: %s', diff_results)
		else:
			logger.debug('diff skipped: %s, %s, %s', results['count'], self.diff, Event.__DIFF__ not in skip_events)

		# [DOC] Module collection is updated, delete_cache
		self.delete_cache()

		return {
			'status':200,
			'msg':'Updated {} docs.'.format(results['count']),
			'args':results
		}
	
	def pre_delete(self, skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (skip_events, env, query, doc)
	def on_delete(self, results: Dict[str, Any], skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (Dict[str, Any], List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (results, skip_events, env, query, doc)
	def delete(self, skip_events: List[str]=[], env: Dict[str, Any]={}, query: Query=[], doc: Dict[str, Any]={}) -> DictObj:
		# [TODO] refactor for template use
		if Event.__PRE__ not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module pre_delete
				pre_delete = self.modules[self.proxy].pre_delete(skip_events=skip_events, env=env, query=query, doc=doc)
				if type(pre_delete) in [DictObj, dict]: return pre_delete
				skip_events, env, query, doc = pre_delete
			pre_delete = self.pre_delete(skip_events=skip_events, env=env, query=query, doc=doc)
			if type(pre_delete) in [DictObj, dict]: return pre_delete
			skip_events, env, query, doc = pre_delete
		# [TODO]: confirm all extns are not linked.
		# [DOC] Pick delete strategy based on skip_events
		strategy = DELETE_SOFT_SKIP_SYS
		if Event.__SOFT__ not in skip_events and Event.__SYS_DOCS__ in skip_events:
			strategy = DELETE_SOFT_SYS
		elif Event.__SOFT__ in skip_events and Event.__SYS_DOCS__ not in skip_events:
			strategy = DELETE_FORCE_SKIP_SYS
		elif Event.__SOFT__ in skip_events and Event.__SYS_DOCS__ in skip_events:
			strategy = DELETE_FORCE_SYS
		
		docs_results = results = Data.read(env=env, collection=self.collection, attrs=self.attrs, extns={}, modules=self.modules, query=query)
		results = Data.delete(env=env, collection=self.collection, attrs=self.attrs, extns={}, modules=self.modules, docs=[doc._id for doc in docs_results['docs']], strategy=strategy)
		if Event.__ON__ not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module on_delete
				on_delete = self.modules[self.proxy].on_delete(results=results, skip_events=skip_events, env=env, query=query, doc=doc)
				if type(on_delete) in [DictObj, dict]: return on_delete
				results, skip_events, env, query, doc = on_delete
			on_delete = self.on_delete(results=results, skip_events=skip_events, env=env, query=query, doc=doc)
			if type(on_delete) in [DictObj, dict]: return on_delete
			results, skip_events, env, query, doc = on_delete
		return {
			'status':200,
			'msg':'Deleted {} docs.'.format(results['count']),
			'args':results
		}
	
	def pre_create_file(self, skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (skip_events, env, query, doc)
	def on_create_file(self, results: Dict[str, Any], skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (Dict[str, Any], List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (results, skip_events, env, query, doc)
	def create_file(self, skip_events: List[str]=[], env: Dict[str, Any]={}, query: Query=[], doc: Dict[str, Any]={}) -> DictObj:
		if Event.__PRE__ not in skip_events:
			pre_create_file = self.pre_create_file(skip_events=skip_events, env=env, query=query, doc=doc)
			if type(pre_create_file) in [DictObj, dict]: return pre_create_file
			skip_events, env, query, doc = pre_create_file
		
		if query['attr'][0] not in self.attrs.keys() or type(self.attrs[query['attr'][0]]) != list or not self.attrs[query['attr'][0]][0].startswith('file'):
			return {
				'status':400,
				'msg':'Attr is invalid.',
				'args':{'code':'{}_{}_INVALID_ATTR'.format(self.package_name, self.module_name.upper())}
			}
		
		results = self.update(skip_events=[Event.__PERM__], env=env, query=[{'_id':query['_id'][0]}], doc={
			query['attr'][0]:{'$push':doc['file'][0]}
		})

		if Event.__ON__ not in skip_events:
			results, skip_events, env, query, doc = self.on_create_file(results=results, skip_events=skip_events, env=env, query=query, doc=doc)
		
		return results
	
	def pre_delete_file(self, skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (skip_events, env, query, doc)
	def on_delete_file(self, results: Dict[str, Any], skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (Dict[str, Any], List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (results, skip_events, env, query, doc)
	def delete_file(self, skip_events: List[str]=[], env: Dict[str, Any]={}, query: Query=[], doc: Dict[str, Any]={}) -> DictObj:
		if Event.__PRE__ not in skip_events:
			pre_delete_file = self.pre_delete_file(skip_events=skip_events, env=env, query=query, doc=doc)
			if type(pre_delete_file) in [DictObj, dict]: return pre_delete_file
			skip_events, env, query, doc = pre_delete_file

		if query['attr'][0] not in self.attrs.keys() or type(self.attrs[query['attr'][0]]) != list or not self.attrs[query['attr'][0]][0].startswith('file'):
			return {
				'status':400,
				'msg':'Attr is invalid.',
				'args':{'code':'{}_{}_INVALID_ATTR'.format(self.package_name, self.module_name.upper())}
			}

		results = self.read(skip_events=[Event.__PERM__], env=env, query=[{'_id':query['_id'][0]}])
		if not results.args.count: # pylint: disable=no-member
			return {
				'status':400,
				'msg':'Doc is invalid.',
				'args':{'code':'{}_{}_INVALID_DOC'.format(self.package_name, self.module_name.upper())}
			}
		doc = results.args.docs[0] # pylint: disable=no-member

		if query['attr'][0] not in doc:
			return {
				'status':400,
				'msg':'Doc attr is invalid.',
				'args':{'code':'{}_{}_INVALID_DOC_ATTR'.format(self.package_name, self.module_name.upper())}
			}
		
		if query['index'][0] not in range(0, doc[query['attr'][0]].__len__()):
			return {
				'status':400,
				'msg':'Index is invalid.',
				'args':{'code':'{}_{}_INVALID_INDEX'.format(self.package_name, self.module_name.upper())}
			}
		
		if type(doc[query['attr'][0]][query['index'][0]]) != dict or 'name' not in doc[query['attr'][0]][query['index'][0]].keys():
			return {
				'status':400,
				'msg':'Index value is invalid.',
				'args':{'code':'{}_{}_INVALID_INDEX_VALUE'.format(self.package_name, self.module_name.upper())}
			}
		
		if doc[query['attr'][0]][query['index'][0]]['name'] != query['name'][0]:
			return {
				'status':400,
				'msg':'File name in query doesn\'t match value.',
				'args':{'code':'{}_{}_FILE_NAME_MISMATCH'.format(self.package_name, self.module_name.upper())}
			}
		
		results = self.update(skip_events=[Event.__PERM__], env=env, query=[{'_id':query['_id'][0]}], doc={
			query['attr'][0]:{'$pull':[doc[query['attr'][0]][query['index'][0]]]}
		})

		if Event.__ON__ not in skip_events:
			results, skip_events, env, query, doc = self.on_delete_file(results=results, skip_events=skip_events, env=env, query=query, doc=doc)

		return results

	def pre_retrieve_file(self, skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (skip_events, env, query, doc)
	def on_retrieve_file(self, results: Dict[str, Any], skip_events: List[str], env: Dict[str, Any], query: Query, doc: Dict[str, Any]) -> (Dict[str, Any], List[str], Dict[str, Any], Query, Dict[str, Any]):
		return (results, skip_events, env, query, doc)
	def retrieve_file(self, skip_events: List[str]=[], env: Dict[str, Any]={}, query: Query=[], doc: Dict[str, Any]={}) -> DictObj:
		if Event.__PRE__ not in skip_events:
			pre_retrieve_file = self.pre_retrieve_file(skip_events=skip_events, env=env, query=query, doc=doc)
			if type(pre_retrieve_file) in [DictObj, dict]: return pre_retrieve_file
			skip_events, env, query, doc = pre_retrieve_file

		attr_name = query['attr'][0]
		filename = query['filename'][0]
		if 'thumb' in query:
			thumb_dims = [int(dim) for dim in query['thumb'][0].split('x')]
		else:
			thumb_dims = False

		results = self.read(skip_events=[Event.__PERM__], env=env, query=[{'_id':query['_id'][0]}])
		if not results.args.count: # pylint: disable=no-member
			return {
				'status':404,
				'msg':'File not found.',
				'args':{
					'code':f'{self.package_name.upper()}_{self.module_name.upper()}_NOT_FOUND',
					'return':'json'
				}
			}
		doc = results.args.docs[0] # pylint: disable=no-member
		try:
			attr_path = attr_name.split('.')
			attr = doc
			for path in attr_path:
				attr = doc[path]
		except:
			return {
				'status':404,
				'msg':'File not found.',
				'args':{
					'code':f'{self.package_name.upper()}_{self.module_name.upper()}_NOT_FOUND',
					'return':'json'
				}
			}

		file = False

		if type(attr) == list:
			for item in attr:
				if item['name'] == filename:
					file = item
					break
		elif type(attr) == dict:
			if attr['name'] == filename:
				file = attr
		
		if file:
			results = {
				'docs':[
					DictObj({
						'_id':query['_id'][0],
						'name':file['name'],
						'type':file['type'],
						'lastModified':file['lastModified'],
						'size':file['size'],
						'content':file['content']
					})
				]
			}

			if thumb_dims:
				if file['type'].split('/')[0] != 'image':
					return {
						'status':400,
						'msg':'File is not of type image to create thumbnail for.',
						'args':{
							'code':f'{self.package_name.upper()}_{self.module_name.upper()}_NOT_IMAGE',
							'return':'json'
						}
					}
				try:
					image = Image.open(io.BytesIO(file['content']))
					image.thumbnail(thumb_dims)
					stream = io.BytesIO()
					image.save(stream, format=image.format)
					stream.seek(0)
					results['docs'][0]['content'] = stream.read()
				except:
					pass

			if Event.__ON__ not in skip_events:
				results, skip_events, env, query, doc = self.on_retrieve_file(results=results, skip_events=skip_events, env=env, query=query, doc=doc)

			results['return'] = 'file'
			return {
				'status':200,
				'msg':'File attached to response.',
				'args':results
			}
		else:
			# [DOC] No filename match
			return {
				'status':404,
				'msg':'File not found.',
				'args':{
					'code':f'{self.package_name.upper()}_{self.module_name.upper()}_NOT_FOUND',
					'return':'json'
				}
			}
	
	def delete_cache(self, skip_events: List[str]=[], env: Dict[str, Any]={}, query: Query=[], doc: Dict[str, Any]={}) -> DictObj:
		if self.cache:
			for cache_set in self.cache:
				cache_set['queries'] = {}
		return {
			'status':200,
			'msg':'Cache deleted.',
			'args':{}
		}