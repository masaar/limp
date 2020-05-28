from limp.config import Config
from limp.enums import Event, DELETE_STRATEGY
from limp.data import Data
from limp.utils import (
	validate_doc,
	InvalidAttrException,
	MissingAttrException,
	ConvertAttrException,
	update_attr_values,
	expand_attr,
)
from limp.classes import (
	DictObj,
	BaseModel,
	Query,
	InvalidAttrTypeException,
	InvalidAttrTypeArgException,
	LIMP_EVENTS,
	LIMP_ENV,
	Query,
	LIMP_QUERY,
	LIMP_DOC,
	ATTR,
	PERM,
	EXTN,
	ATTR_MOD,
	CACHE,
	CACHED_QUERY,
	ANALYTIC,
)
from limp.base_method import BaseMethod

from typing import List, Dict, Union, Tuple, Callable, Any, TypedDict

from PIL import Image
from bson import ObjectId
import traceback, logging, datetime, re, sys, io, copy, asyncio

logger = logging.getLogger('limp')


class BaseModule:
	_limp_module: bool = True
	collection: Union[str, bool]
	proxy: str
	attrs: Dict[str, ATTR]
	diff: Union[bool, ATTR_MOD]
	defaults: Dict[str, Any]
	unique_attrs: List[str]
	extns: Dict[str, EXTN]
	privileges: List[str]
	methods: TypedDict(
		'METHODS',
		permissions=List[PERM],
		query_args=Dict[str, Union[ATTR, ATTR_MOD]],
		doc_args=Dict[str, Union[ATTR, ATTR_MOD]],
		get_method=bool,
		post_method=bool,
		watch_method=bool,
	)
	cache: List[CACHE]
	analytics: List[ANALYTIC]

	package_name: str
	module_name: str

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
		if not getattr(self, 'analytics', None):
			self.analytics = []

		Config.modules = {}

		# [DOC] Populate package and module names for in-context use.
		self.package_name = (
			self.__module__.replace('modules.', '').upper().split('.')[0]
		)
		self.module_name = re.sub(
			r'([A-Z])',
			r'_\1',
			self.__class__.__name__[0].lower() + self.__class__.__name__[1:],
		).lower()

	def _pre_initialise(self) -> None:
		pass

	def _initialise(self) -> None:
		# [DOC] Call _pre_initialise for advanced module initialisation
		self._pre_initialise()
		# [DOC] Check for proxy
		if self.proxy:
			logger.debug(f'Module \'{self.module_name}\' is a proxy module. Updating.')
			# [DOC] Copy regular attrs
			self.collection = Config.modules[self.proxy].collection
			self.attrs = copy.deepcopy(Config.modules[self.proxy].attrs)
			self.diff = Config.modules[self.proxy].diff
			self.defaults = copy.deepcopy(Config.modules[self.proxy].defaults)
			self.unique_attrs = copy.deepcopy(Config.modules[self.proxy].unique_attrs)
			self.extns = copy.deepcopy(Config.modules[self.proxy].extns)
			self.privileges = copy.deepcopy(Config.modules[self.proxy].privileges)
			# [DOC] Update methods from original module
			for method in Config.modules[self.proxy].methods.keys():
				# [DOC] Copy method attrs if not present in proxy
				if method not in self.methods.keys():
					if type(Config.modules[self.proxy].methods[method]) == dict:
						self.methods[method] = copy.deepcopy(
							Config.modules[self.proxy].methods[method]
						)
					elif type(Config.modules[self.proxy].methods[method]) == BaseMethod:
						self.methods[method] = {
							'permissions': copy.deepcopy(
								Config.modules[self.proxy].methods[method].permissions
							),
							'query_args': copy.deepcopy(
								Config.modules[self.proxy].methods[method].query_args
							),
							'doc_args': copy.deepcopy(
								Config.modules[self.proxy].methods[method].doc_args
							),
							'get_method': Config.modules[self.proxy]
							.methods[method]
							.get_method,
						}
				# [DOC] Create methods functions in proxy module if not present
				if not getattr(self, method, None):
					setattr(
						self,
						method,
						lambda self=self, skip_events=[], env={}, query=[], doc={}: getattr(
							Config.modules[self.proxy], method
						)(
							skip_events=skip_events,
							env=env,
							query=query,
							doc=doc,
							payload={},
						),
					)
		# [DOC] Check attrs for any invalid type
		for attr in self.attrs.keys():
			try:
				logger.debug(
					f'Attempting to validate Attr Type for \'{attr}\' of module \'{self.module_name}\'.'
				)
				ATTR.validate_type(attr_type=self.attrs[attr])
			except InvalidAttrTypeException as e:
				logger.error(
					f'Invalid Attr Type for \'{attr}\' of module \'{self.module_name}\'. Original validation error: {str(e)}. Exiting.'
				)
				exit()
			except InvalidAttrTypeArgException as e:
				logger.error(
					f'Invalid Attr Type Arg for \'{attr}\' of module \'{self.module_name}\'. Original validation error: {str(e)}. Exiting.'
				)
				exit()
			# [DOC] Update default value
			for default in self.defaults.keys():
				if (
					default == attr
					or default.startswith(f'{attr}.')
					or default.startswith(f'{attr}:')
				):
					logger.debug(
						f'Updating default value for attr \'{attr}\' to: \'{self.defaults[default]}\''
					)
					update_attr_values(
						attr=ATTR.TYPED_DICT(dict=self.attrs),
						value='default',
						value_path=default,
						value_val=self.defaults[default],
					)
			# [DOC] Update extn value
			for extn in self.extns.keys():
				if (
					extn == attr
					or extn.startswith(f'{attr}.')
					or extn.startswith(f'{attr}:')
				):
					logger.debug(
						f'Updating extn value for attr \'{extn}\' to: \'{self.extns[extn]}\''
					)
					update_attr_values(
						attr=ATTR.TYPED_DICT(dict=self.attrs),
						value='extn',
						value_path=extn,
						value_val=self.extns[extn],
					)
		# [DOC] Abstract methods as BaseMethod objects
		for method in self.methods.keys():
			# [DOC] Check for existence of at least single permissions set per method
			if not len(self.methods[method]['permissions']):
				logger.error(
					f'No permissions sets for method \'{method}\' of module \'{self.module_name}\'. Exiting.'
				)
				exit()
			# [DOC] Check method query_args attr, set it or update it if required.
			if 'query_args' not in self.methods[method].keys():
				if method == 'create_file':
					self.methods[method]['query_args'] = [
						{'_id': ATTR.ID(), 'attr': ATTR.STR()}
					]
				elif method == 'delete_file':
					self.methods[method]['query_args'] = [
						{
							'_id': ATTR.ID(),
							'attr': ATTR.STR(),
							'index': ATTR.INT(),
							'name': ATTR.STR(),
						}
					]
				else:
					self.methods[method]['query_args'] = False
			elif type(self.methods[method]['query_args']) == dict:
				self.methods[method]['query_args'] = [
					self.methods[method]['query_args']
				]
			# [DOC] Check method doc_args attr, set it or update it if required.
			if 'doc_args' not in self.methods[method].keys():
				if method == 'create_file':
					self.methods[method]['doc_args'] = [{'file': ATTR.FILE()}]
				else:
					self.methods[method]['doc_args'] = False
			elif type(self.methods[method]['doc_args']) == dict:
				self.methods[method]['doc_args'] = [self.methods[method]['doc_args']]
			# [DOC] Check method watch_method attr, set it or update it if required.
			if (
				'watch_method' not in self.methods[method].keys()
				or self.methods[method]['watch_method'] == False
			):
				self.methods[method]['watch_method'] = False
			# [DOC] Check method get_method attr, set it or update it if required.
			if 'get_method' not in self.methods[method].keys():
				self.methods[method]['get_method'] = False
			elif self.methods[method]['get_method'] == True:
				if not self.methods[method]['query_args']:
					if method == 'retrieve_file':
						self.methods[method]['query_args'] = [
							{
								'_id': ATTR.ID(),
								'attr': ATTR.STR(),
								'filename': ATTR.STR(),
							},
							{
								'_id': ATTR.ID(),
								'attr': ATTR.STR(),
								'thumb': ATTR.STR(pattern=r'[0-9]+x[0-9]+'),
								'filename': ATTR.STR(),
							},
						]
					else:
						self.methods[method]['query_args'] = [{}]
			# [DOC] Check method post_method attr, set it or update it if required.
			if 'post_method' not in self.methods[method].keys():
				self.methods[method]['post_method'] = False
			elif self.methods[method]['post_method'] == True:
				if not self.methods[method]['query_args']:
					self.methods[method]['query_args'] = [{}]
			# [DOC] Check permissions sets for any invalid set
			for permissions_set in self.methods[method]['permissions']:
				if type(permissions_set) != PERM:
					logger.error(
						f'Invalid permissions set \'{permissions_set}\' of method \'{method}\' of module \'{self.module_name}\'. Exiting.'
					)
					exit()
				# [DOC] Add default Doc Modifiers to prevent sys attrs from being modified
				if method == 'update':
					for attr in ['user', 'create_time']:
						if attr not in permissions_set.doc_mod.keys():
							permissions_set.doc_mod[attr] = None
						elif permissions_set.doc_mod[attr] == True:
							del permissions_set.doc_mod[attr]
			# [DOC] Check invalid query_args, doc_args types
			for arg_set in ['query', 'doc']:
				if self.methods[method][f'{arg_set}_args']:
					for args_set in self.methods[method][f'{arg_set}_args']:
						for attr in args_set.keys():
							try:
								ATTR.validate_type(attr_type=args_set[attr])
							except:
								logger.error(
									f'Invalid \'{arg_set}_args\' attr type for \'{attr}\' of set \'{args_set}\' of method \'{method}\' of module \'{self.module_name}\'. Exiting.'
								)
								exit()
			# [DOC] Initialise method as BaseMethod
			self.methods[method] = BaseMethod(
				module=self,
				method=method,
				permissions=self.methods[method]['permissions'],
				query_args=self.methods[method]['query_args'],
				doc_args=self.methods[method]['doc_args'],
				watch_method=self.methods[method]['watch_method'],
				get_method=self.methods[method]['get_method'],
				post_method=self.methods[method]['post_method'],
			)
		# [DOC] Check extns for invalid extended attrs
		for attr in self.extns.keys():
			if type(self.extns[attr]) not in [EXTN, ATTR_MOD]:
				logger.error(
					f'Invalid extns attr \'{attr}\' of module \'{self.module_name}\'. Exiting.'
				)
				exit()
		logger.debug(f'Initialised module {self.module_name}')

	def status(
		self, *, status: int, msg: str, args: Union[Dict[str, Any], DictObj] = None
	) -> Dict[str, Any]:
		status_dict = {'status': status, 'msg': msg, 'args': {}}
		if args:
			status_dict['args'] = args
		if type(status_dict['args']) == dict:
			if 'code' in status_dict['args'].keys():
				status_dict['args'][
					'code'
				] = f'{self.package_name.upper()}_{self.module_name.upper()}_{status_dict["args"]["code"]}'
		elif type(status_dict['args']) == DictObj:
			if 'code' in status_dict['args']:
				status_dict['args'][
					'code'
				] = f'{self.package_name.upper()}_{self.module_name.upper()}_{status_dict["args"]["code"]}'
		return status_dict

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

	async def pre_read(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, Query], LIMP_DOC, Dict[str, Any]
	]:
		return (skip_events, env, query, doc, payload)

	async def on_read(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, Query],
		LIMP_DOC,
		Dict[str, Any],
	]:
		return (results, skip_events, env, query, doc, payload)

	async def read(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, Query] = [],
		doc: LIMP_DOC = {},
	) -> DictObj:
		if Event.PRE not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module pre_read
				pre_read = await Config.modules[self.proxy].pre_read(
					skip_events=skip_events, env=env, query=query, doc=doc, payload={}
				)
				if type(pre_read) in [DictObj, dict]:
					return pre_read
				skip_events, env, query, doc, payload = pre_read
			pre_read = await self.pre_read(
				skip_events=skip_events, env=env, query=query, doc=doc, payload={}
			)
			if type(pre_read) in [DictObj, dict]:
				return pre_read
			skip_events, env, query, doc, payload = pre_read
		else:
			payload = {}
		# [DOC] Check for cache workflow instructins
		if self.cache:
			results = False
			for cache_set in self.cache:
				if (
					cache_set.condition(skip_events=skip_events, env=env, query=query)
					== True
				):
					cache_key = f'{str(query._query)}____{str(query._special)}'
					if cache_key in cache_set.queries.keys():
						if cache_set.period:
							if (
								cache_set.queries[cache_key].query_time
								+ datetime.timedelta(seconds=cache_set.period)
							) < datetime.datetime.utcnow():
								if not results:
									results = await Data.read(
										env=env,
										collection=self.collection,
										attrs=self.attrs,
										query=query,
									)
								cache_set.queries[cache_key] = CACHED_QUERY(
									results=results
								)
							else:
								results = cache_set.queries[cache_key].results
								results['cache'] = cache_set.queries[
									cache_key
								].query_time.isoformat()
						else:
							results = cache_set.queries[cache_key].results
							results['cache'] = cache_set.queries[
								cache_key
							].query_time.isoformat()
					else:
						if not results:
							results = await Data.read(
								env=env,
								collection=self.collection,
								attrs=self.attrs,
								query=query,
							)
						cache_set.queries[cache_key] = CACHED_QUERY(results=results)
			if not results:
				results = await Data.read(
					env=env,
					collection=self.collection,
					attrs=self.attrs,
					query=query,
					skip_extn='$extn' in query or Event.EXTN in skip_events,
				)
		else:
			results = await Data.read(
				env=env,
				collection=self.collection,
				attrs=self.attrs,
				query=query,
				skip_extn='$extn' in query or Event.EXTN in skip_events,
			)
		if Event.ON not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module on_read
				on_read = await Config.modules[self.proxy].on_read(
					results=results,
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					payload=payload,
				)
				if type(on_read) in [DictObj, dict]:
					return on_read
				results, skip_events, env, query, doc, payload = on_read
			on_read = await self.on_read(
				results=results,
				skip_events=skip_events,
				env=env,
				query=query,
				doc=doc,
				payload=payload,
			)
			if type(on_read) in [DictObj, dict]:
				return on_read
			results, skip_events, env, query, doc, payload = on_read
			# [DOC] if $attrs query arg is present return only required keys.
			if '$attrs' in query:
				query['$attrs'].insert(0, '_id')
				for i in range(len(results['docs'])):
					results['docs'][i] = BaseModel(
						{
							attr: results['docs'][i][attr]
							for attr in query['$attrs']
							if attr in results['docs'][i]._attrs()
						}
					)

		return self.status(
			status=200, msg=f'Found {results["count"]} docs.', args=results
		)

	async def pre_watch(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, Query], LIMP_DOC, Dict[str, Any]
	]:
		return (skip_events, env, query, doc, payload)

	async def on_watch(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, Query],
		LIMP_DOC,
		Dict[str, Any],
	]:
		return (results, skip_events, env, query, doc, payload)

	async def watch(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> DictObj:
		if Event.PRE not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module pre_watch
				pre_watch = await Config.modules[self.proxy].pre_watch(
					skip_events=skip_events, env=env, query=query, doc=doc, payload={}
				)
				if type(pre_watch) in [DictObj, dict]:
					yield pre_watch
				skip_events, env, query, doc, payload = pre_watch
			pre_watch = await self.pre_watch(
				skip_events=skip_events, env=env, query=query, doc=doc, payload={}
			)
			if type(pre_watch) in [DictObj, dict]:
				yield pre_watch
			skip_events, env, query, doc, payload = pre_watch
		else:
			payload = {}

		logger.debug('Preparing async loop at BaseModule')
		async for results in Data.watch(
			env=env,
			collection=self.collection,
			attrs=self.attrs,
			query=query,
			skip_extn='$extn' in query or Event.EXTN in skip_events,
		):
			logger.debug(f'Received watch results at BaseModule: {results}')

			if 'stream' in results.keys():
				yield results
				continue

			if Event.ON not in skip_events:
				# [DOC] Check proxy module
				if self.proxy:
					# [DOC] Call original module on_watch
					on_watch = await Config.modules[self.proxy].on_watch(
						results=results,
						skip_events=skip_events,
						env=env,
						query=query,
						doc=doc,
						payload=payload,
					)
					if type(on_watch) in [DictObj, dict]:
						yield on_watch
					results, skip_events, env, query, doc, payload = on_watch
				on_watch = await self.on_watch(
					results=results,
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					payload=payload,
				)
				if type(on_watch) in [DictObj, dict]:
					yield on_watch
				results, skip_events, env, query, doc, payload = on_watch
				# [DOC] if $attrs query arg is present return only required keys.
				if '$attrs' in query:
					query['$attrs'].insert(0, '_id')
					for i in range(len(results['docs'])):
						results['docs'][i] = BaseModel(
							{
								attr: results['docs'][i][attr]
								for attr in query['$attrs']
								if attr in results['docs'][i]._attrs()
							}
						)
			yield self.status(
				status=200, msg=f'Detected {results["count"]} docs.', args=results
			)

		logger.debug('Generator ended at BaseModule.')

	async def pre_create(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, Query], LIMP_DOC, Dict[str, Any]
	]:
		return (skip_events, env, query, doc, payload)

	async def on_create(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, Query],
		LIMP_DOC,
		Dict[str, Any],
	]:
		return (results, skip_events, env, query, doc, payload)

	async def create(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, Query] = [],
		doc: LIMP_DOC = {},
	) -> DictObj:
		if Event.PRE not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module pre_create
				pre_create = await Config.modules[self.proxy].pre_create(
					skip_events=skip_events, env=env, query=query, doc=doc, payload={}
				)
				if type(pre_create) in [DictObj, dict]:
					return pre_create
				skip_events, env, query, doc, payload = pre_create
			pre_create = await self.pre_create(
				skip_events=skip_events, env=env, query=query, doc=doc, payload={}
			)
			if type(pre_create) in [DictObj, dict]:
				return pre_create
			skip_events, env, query, doc, payload = pre_create
		else:
			payload = {}
		# [DOC] Expant dot-notated keys onto dicts
		doc = expand_attr(doc=doc)
		# [DOC] Deleted all extra doc args
		doc = {
			attr: doc[attr]
			for attr in ['_id', *self.attrs.keys()]
			if attr in doc.keys() and doc[attr] != None
		}
		# [DOC] Append host_add, user_agent, create_time, diff if it's present in attrs.
		if (
			'user' in self.attrs.keys()
			and 'host_add' not in doc.keys()
			and env['session']
			and Event.ARGS not in skip_events
		):
			doc['user'] = env['session'].user._id
		if 'create_time' in self.attrs.keys():
			doc['create_time'] = datetime.datetime.utcnow().isoformat()
		if 'host_add' in self.attrs.keys() and 'host_add' not in doc.keys():
			doc['host_add'] = env['REMOTE_ADDR']
		if 'user_agent' in self.attrs.keys() and 'user_agent' not in doc.keys():
			doc['user_agent'] = env['HTTP_USER_AGENT']
		if Event.ARGS not in skip_events:
			# [DOC] Check presence and validate all attrs in doc args
			try:
				await validate_doc(
					doc=doc,
					attrs=self.attrs,
					skip_events=skip_events,
					env=env,
					query=query,
				)
			except MissingAttrException as e:
				return self.status(
					status=400,
					msg=f'{str(e)} for \'create\' request on module \'{self.package_name.upper()}_{self.module_name.upper()}\'.',
					args={'code': 'MISSING_ATTR'},
				)
			except InvalidAttrException as e:
				return self.status(
					status=400,
					msg=f'{str(e)} for \'create\' request on module \'{self.package_name.upper()}_{self.module_name.upper()}\'.',
					args={'code': 'INVALID_ATTR'},
				)
			except ConvertAttrException as e:
				return self.status(
					status=400,
					msg=f'{str(e)} for \'create\' request on module \'{self.package_name.upper()}_{self.module_name.upper()}\'.',
					args={'code': 'CONVERT_INVALID_ATTR'},
				)
			# [DOC] Check unique_attrs
			if self.unique_attrs:
				unique_attrs_query = [[]]
				for attr in self.unique_attrs:
					if type(attr) == str:
						unique_attrs_query[0].append({attr: doc[attr]})
					elif type(attr) == tuple:
						unique_attrs_query[0].append(
							{child_attr: doc[child_attr] for child_attr in attr}
						)
				unique_attrs_query.append({'$limit': 1})
				unique_results = await self.read(
					skip_events=[Event.PERM], env=env, query=unique_attrs_query
				)
				if unique_results.args.count:
					unique_attrs_str = ', '.join(
						map(
							lambda _: ('(' + ', '.join(_) + ')')
							if type(_) == tuple
							else _,
							self.unique_attrs,
						)
					)
					return self.status(
						status=400,
						msg=f'A doc with the same \'{unique_attrs_str}\' already exists.',
						args={'code': 'DUPLICATE_DOC'},
					)
		# [DOC] Execute Data driver create
		results = await Data.create(
			env=env, collection=self.collection, attrs=self.attrs, doc=doc
		)
		if Event.ON not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module on_create
				on_create = await Config.modules[self.proxy].on_create(
					results=results,
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					payload=payload,
				)
				if type(on_create) in [DictObj, dict]:
					return on_create
				results, skip_events, env, query, doc, payload = on_create
			on_create = await self.on_create(
				results=results,
				skip_events=skip_events,
				env=env,
				query=query,
				doc=doc,
				payload=payload,
			)
			if type(on_create) in [DictObj, dict]:
				return on_create
			results, skip_events, env, query, doc, payload = on_create
		# [DOC] create soft action is to only return the new created doc _id.
		if Event.SOFT in skip_events:
			results = await self.methods['read'](
				skip_events=[Event.PERM], env=env, query=[[{'_id': results['docs'][0]}]]
			)
			results = results['args']

		# [DOC] Module collection is updated, update_cache
		asyncio.create_task(self.update_cache(env=env))

		return self.status(
			status=200, msg=f'Created {results["count"]} docs.', args=results
		)

	async def pre_update(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, Query], LIMP_DOC, Dict[str, Any]
	]:
		return (skip_events, env, query, doc, payload)

	async def on_update(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, Query],
		LIMP_DOC,
		Dict[str, Any],
	]:
		return (results, skip_events, env, query, doc, payload)

	async def update(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, Query] = [],
		doc: LIMP_DOC = {},
	) -> DictObj:
		if Event.PRE not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module pre_update
				pre_update = await Config.modules[self.proxy].pre_update(
					skip_events=skip_events, env=env, query=query, doc=doc, payload={}
				)
				if type(pre_update) in [DictObj, dict]:
					return pre_update
				skip_events, env, query, doc, payload = pre_update
			pre_update = await self.pre_update(
				skip_events=skip_events, env=env, query=query, doc=doc, payload={}
			)
			if type(pre_update) in [DictObj, dict]:
				return pre_update
			skip_events, env, query, doc, payload = pre_update
		else:
			payload = {}
		# [DOC] Check presence and validate all attrs in doc args
		try:
			await validate_doc(
				doc=doc,
				attrs=self.attrs,
				allow_opers=True,
				allow_none=True,
				skip_events=skip_events,
				env=env,
				query=query,
			)
		except MissingAttrException as e:
			return self.status(
				status=400,
				msg=f'{str(e)} for \'update\' request on module \'{self.package_name.upper()}_{self.module_name.upper()}\'.',
				args={'code': 'MISSING_ATTR'},
			)
		except InvalidAttrException as e:
			return self.status(
				status=400,
				msg=f'{str(e)} for \'update\' request on module \'{self.package_name.upper()}_{self.module_name.upper()}\'.',
				args={'code': 'INVALID_ATTR'},
			)
		except ConvertAttrException as e:
			return self.status(
				status=400,
				msg=f'{str(e)} for \'update\' request on module \'{self.package_name.upper()}_{self.module_name.upper()}\'.',
				args={'code': 'CONVERT_INVALID_ATTR'},
			)
		# [DOC] Delete all attrs not belonging to the doc, checking against top level attrs only
		doc = {
			attr: doc[attr]
			for attr in ['_id', *doc.keys()]
			if attr.split('.')[0] in self.attrs.keys() and doc[attr] != None
		}
		# [DOC] Check if there is anything yet to update
		if not len(doc.keys()):
			return self.status(status=200, msg='Nothing to update.', args={})
		# [DOC] Find which docs are to be updated
		docs_results = await Data.read(
			env=env,
			collection=self.collection,
			attrs=self.attrs,
			query=query,
			skip_process=True,
		)
		# [DOC] Check unique_attrs
		if self.unique_attrs:
			# [DOC] If any of the unique_attrs is present in doc, and docs_results is > 1, we have duplication
			if len(docs_results['docs']) > 1:
				unique_attrs_check = True
				for attr in self.unique_attrs:
					if type(attr) == str and attr in doc.keys():
						unique_attrs_check = False
						break
					elif type(attr) == tuple:
						for child_attr in attr:
							if not unique_attrs_check:
								break
							if child_attr in doc.keys():
								unique_attrs_check = False
								break

				if not unique_attrs_check:
					return self.status(
						status=400,
						msg='Update call query has more than one doc as results. This would result in duplication.',
						args={'code': 'MULTI_DUPLICATE'},
					)

			# [DOC] Check if any of the unique_attrs are present in doc
			if sum(1 for attr in doc.keys() if attr in self.unique_attrs) > 0:
				# [DOC] Check if the doc would result in duplication after update
				unique_attrs_query = [[]]
				for attr in self.unique_attrs:
					if type(attr) == str:
						if attr in doc.keys():
							unique_attrs_query[0].append({attr: doc[attr]})
					elif type(attr) == tuple:
						unique_attrs_query[0].append(
							{
								child_attr: doc[child_attr]
								for child_attr in attr
								if attr in doc.keys()
							}
						)
				unique_attrs_query.append(
					{'_id': {'$nin': [doc._id for doc in docs_results['docs']]}}
				)
				unique_attrs_query.append({'$limit': 1})
				unique_results = await self.read(
					skip_events=[Event.PERM], env=env, query=unique_attrs_query
				)
				if unique_results.args.count:
					unique_attrs_str = ', '.join(
						map(
							lambda _: ('(' + ', '.join(_) + ')')
							if type(_) == tuple
							else _,
							self.unique_attrs,
						)
					)
					return self.status(
						status=400,
						msg=f'A doc with the same \'{unique_attrs_str}\' already exists.',
						args={'code': 'DUPLICATE_DOC'},
					)
		results = await Data.update(
			env=env,
			collection=self.collection,
			attrs=self.attrs,
			docs=[doc._id for doc in docs_results['docs']],
			doc=doc,
		)
		if Event.ON not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module on_update
				on_update = await Config.modules[self.proxy].on_update(
					results=results,
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					payload=payload,
				)
				if type(on_update) in [DictObj, dict]:
					return on_update
				results, skip_events, env, query, doc, payload = on_update
			on_update = await self.on_update(
				results=results,
				skip_events=skip_events,
				env=env,
				query=query,
				doc=doc,
				payload=payload,
			)
			if type(on_update) in [DictObj, dict]:
				return on_update
			results, skip_events, env, query, doc, payload = on_update
		# [DOC] If at least one doc updated, and module has diff enabled, and __DIFF__ not skipped:
		if results['count'] and self.diff and Event.DIFF not in skip_events:
			# [DOC] If diff is a ATTR_MOD, Check condition for valid diff case
			if type(self.diff) == ATTR_MOD:
				self.diff: ATTR_MOD
				if self.diff.condition(
					skip_events=skip_events, env=env, query=query, doc=doc
				):
					# [DOC] if condition passed, create Diff doc with default callable
					diff_vars = doc
					if self.diff.default and callable(self.diff.default):
						diff_vars = self.diff.default(
							skip_events=skip_events, env=env, query=query, doc=doc
						)
					diff_results = await Config.modules['diff'].methods['create'](
						skip_events=[Event.PERM],
						env=env,
						query=query,
						doc={'module': self.module_name, 'vars': diff_vars},
					)
					if diff_results.status != 200:
						logger.error(
							f'Failed to create Diff doc, results: {diff_results}'
						)
				else:
					logger.debug(f'Skipped Diff Workflow due to failed condition.')
			else:
				diff_results = await Config.modules['diff'].methods['create'](
					skip_events=[Event.PERM],
					env=env,
					query=query,
					doc={'module': self.module_name, 'vars': doc},
				)
				if diff_results.status != 200:
					logger.error(f'Failed to create Diff doc, results: {diff_results}')
		else:
			logger.debug(
				f'Skipped Diff Workflow due to: {results["count"]}, {self.diff}, {Event.DIFF not in skip_events}'
			)

		# [DOC] Module collection is updated, update_cache
		asyncio.create_task(self.update_cache(env=env))

		return self.status(
			status=200, msg=f'Updated {results["count"]} docs.', args=results
		)

	async def pre_delete(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, Query], LIMP_DOC, Dict[str, Any]
	]:
		return (skip_events, env, query, doc, payload)

	async def on_delete(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, Query],
		LIMP_DOC,
		Dict[str, Any],
	]:
		return (results, skip_events, env, query, doc, payload)

	async def delete(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, Query] = [],
		doc: LIMP_DOC = {},
	) -> DictObj:
		if Event.PRE not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module pre_delete
				pre_delete = await Config.modules[self.proxy].pre_delete(
					skip_events=skip_events, env=env, query=query, doc=doc, payload={}
				)
				if type(pre_delete) in [DictObj, dict]:
					return pre_delete
				skip_events, env, query, doc, payload = pre_delete
			pre_delete = await self.pre_delete(
				skip_events=skip_events, env=env, query=query, doc=doc, payload={}
			)
			if type(pre_delete) in [DictObj, dict]:
				return pre_delete
			skip_events, env, query, doc, payload = pre_delete
		else:
			payload = {}
		# [TODO]: confirm all extns are not linked.
		# [DOC] Pick delete strategy based on skip_events
		strategy = DELETE_STRATEGY.SOFT_SKIP_SYS
		if Event.SOFT not in skip_events and Event.SYS_DOCS in skip_events:
			strategy = DELETE_STRATEGY.SOFT_SYS
		elif Event.SOFT in skip_events and Event.SYS_DOCS not in skip_events:
			strategy = DELETE_STRATEGY.FORCE_SKIP_SYS
		elif Event.SOFT in skip_events and Event.SYS_DOCS in skip_events:
			strategy = DELETE_STRATEGY.FORCE_SYS

		docs_results = results = await Data.read(
			env=env,
			collection=self.collection,
			attrs=self.attrs,
			query=query,
			skip_process=True,
		)
		results = await Data.delete(
			env=env,
			collection=self.collection,
			attrs=self.attrs,
			docs=[doc._id for doc in docs_results['docs']],
			strategy=strategy,
		)
		if Event.ON not in skip_events:
			# [DOC] Check proxy module
			if self.proxy:
				# [DOC] Call original module on_delete
				on_delete = await Config.modules[self.proxy].on_delete(
					results=results,
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					payload=payload,
				)
				if type(on_delete) in [DictObj, dict]:
					return on_delete
				results, skip_events, env, query, doc, payload = on_delete
			on_delete = await self.on_delete(
				results=results,
				skip_events=skip_events,
				env=env,
				query=query,
				doc=doc,
				payload=payload,
			)
			if type(on_delete) in [DictObj, dict]:
				return on_delete
			results, skip_events, env, query, doc, payload = on_delete

		# [DOC] Module collection is updated, update_cache
		asyncio.create_task(self.update_cache(env=env))

		return self.status(
			status=200, msg=f'Deleted {results["count"]} docs.', args=results
		)

	def pre_create_file(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, Query], LIMP_DOC, Dict[str, Any]
	]:
		return (skip_events, env, query, doc, payload)

	def on_create_file(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, Query],
		LIMP_DOC,
		Dict[str, Any],
	]:
		return (results, skip_events, env, query, doc, payload)

	def create_file(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, Query] = [],
		doc: LIMP_DOC = {},
	) -> DictObj:
		if Event.PRE not in skip_events:
			pre_create_file = self.pre_create_file(
				skip_events=skip_events, env=env, query=query, doc=doc, payload={}
			)
			if type(pre_create_file) in [DictObj, dict]:
				return pre_create_file
			skip_events, env, query, doc, payload = pre_create_file
		else:
			payload = {}

		if (
			query['attr'][0] not in self.attrs.keys()
			or type(self.attrs[query['attr'][0]]) != list
			or not self.attrs[query['attr'][0]][0].startswith('file')
		):
			return self.status(
				status=400, msg='Attr is invalid.', args={'code': 'INVALID_ATTR'}
			)

		results = self.update(
			skip_events=[Event.PERM],
			env=env,
			query=[{'_id': query['_id'][0]}],
			doc={query['attr'][0]: {'$append': doc['file']}},
		)

		if Event.ON not in skip_events:
			results, skip_events, env, query, doc, payload = self.on_create_file(
				results=results,
				skip_events=skip_events,
				env=env,
				query=query,
				doc=doc,
				payload=payload,
			)

		return results

	async def pre_delete_file(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, Query], LIMP_DOC, Dict[str, Any]
	]:
		return (skip_events, env, query, doc, payload)

	async def on_delete_file(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, Query],
		LIMP_DOC,
		Dict[str, Any],
	]:
		return (results, skip_events, env, query, doc, payload)

	async def delete_file(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, Query] = [],
		doc: LIMP_DOC = {},
	) -> DictObj:
		if Event.PRE not in skip_events:
			pre_delete_file = await self.pre_delete_file(
				skip_events=skip_events, env=env, query=query, doc=doc, payload={}
			)
			if type(pre_delete_file) in [DictObj, dict]:
				return pre_delete_file
			skip_events, env, query, doc, payload = pre_delete_file
		else:
			payload = {}

		if (
			query['attr'][0] not in self.attrs.keys()
			or type(self.attrs[query['attr'][0]]) != list
			or not self.attrs[query['attr'][0]][0].startswith('file')
		):
			return self.status(
				status=400, msg='Attr is invalid.', args={'code': 'INVALID_ATTR'}
			)

		results = await self.read(
			skip_events=[Event.PERM], env=env, query=[{'_id': query['_id'][0]}]
		)
		if not results.args.count:
			return self.status(
				status=400, msg='Doc is invalid.', args={'code': 'INVALID_DOC'}
			)
		doc = results.args.docs[0]

		if query['attr'][0] not in doc:
			return self.status(
				status=400,
				msg='Doc attr is invalid.',
				args={'code': 'INVALID_DOC_ATTR'},
			)

		if query['index'][0] not in range(len(doc[query['attr'][0]])):
			return self.status(
				status=400, msg='Index is invalid.', args={'code': 'INVALID_INDEX'}
			)

		if (
			type(doc[query['attr'][0]][query['index'][0]]) != dict
			or 'name' not in doc[query['attr'][0]][query['index'][0]].keys()
		):
			return self.status(
				status=400,
				msg='Index value is invalid.',
				args={'code': 'INVALID_INDEX_VALUE'},
			)

		if doc[query['attr'][0]][query['index'][0]]['name'] != query['name'][0]:
			return self.status(
				status=400,
				msg='File name in query doesn\'t match value.',
				args={'code': 'FILE_NAME_MISMATCH'},
			)

		results = await self.update(
			skip_events=[Event.PERM],
			env=env,
			query=[{'_id': query['_id'][0]}],
			doc={
				query['attr'][0]: {
					'$del_val': [doc[query['attr'][0]][query['index'][0]]]
				}
			},
		)

		if Event.ON not in skip_events:
			results, skip_events, env, query, doc, payload = await self.on_delete_file(
				results=results,
				skip_events=skip_events,
				env=env,
				query=query,
				doc=doc,
				payload=payload,
			)

		return results

	async def pre_retrieve_file(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, Query], LIMP_DOC, Dict[str, Any]
	]:
		return (skip_events, env, query, doc, payload)

	async def on_retrieve_file(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, Query],
		LIMP_DOC,
		Dict[str, Any],
	]:
		return (results, skip_events, env, query, doc, payload)

	async def retrieve_file(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, Query] = [],
		doc: LIMP_DOC = {},
	) -> DictObj:
		if Event.PRE not in skip_events:
			pre_retrieve_file = await self.pre_retrieve_file(
				skip_events=skip_events, env=env, query=query, doc=doc, payload={}
			)
			if type(pre_retrieve_file) in [DictObj, dict]:
				return pre_retrieve_file
			skip_events, env, query, doc, payload = pre_retrieve_file
		else:
			payload = {}

		attr_name = query['attr'][0]
		filename = query['filename'][0]
		if 'thumb' in query:
			thumb_dims = [int(dim) for dim in query['thumb'][0].split('x')]
		else:
			thumb_dims = False

		results = await self.read(
			skip_events=[Event.PERM] + skip_events,
			env=env,
			query=[{'_id': query['_id'][0]}],
		)
		if not results.args.count:
			return self.status(
				status=400,
				msg='File not found.',
				args={'code': 'NOT_FOUND', 'return': 'json'},
			)
		doc = results.args.docs[0]
		try:
			attr_path = attr_name.split('.')
			attr = doc
			for path in attr_path:
				attr = doc[path]
		except:
			return self.status(
				status=404,
				msg='File not found.',
				args={'code': 'NOT_FOUND', 'return': 'json'},
			)

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
				'docs': [
					DictObj(
						{
							'_id': query['_id'][0],
							'name': file['name'],
							'type': file['type'],
							'lastModified': file['lastModified'],
							'size': file['size'],
							'content': file['content'],
						}
					)
				]
			}

			if thumb_dims:
				if file['type'].split('/')[0] != 'image':
					return self.status(
						status=400,
						msg='File is not of type image to create thumbnail for.',
						args={'code': 'NOT_IMAGE', 'return': 'json'},
					)
				try:
					image = Image.open(io.BytesIO(file['content']))
					image.thumbnail(thumb_dims)
					stream = io.BytesIO()
					image.save(stream, format=image.format)
					stream.seek(0)
					results['docs'][0]['content'] = stream.read()
				except:
					pass

			if Event.ON not in skip_events:
				(
					results,
					skip_events,
					env,
					query,
					doc,
					payload,
				) = await self.on_retrieve_file(
					results=results,
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					payload=payload,
				)

			results['return'] = 'file'
			return self.status(
				status=200, msg='File attached to response.', args=results
			)
		else:
			# [DOC] No filename match
			return self.status(
				status=404,
				msg='File not found.',
				args={'code': 'NOT_FOUND', 'return': 'json'},
			)

	async def update_cache(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, Query] = [],
		doc: LIMP_DOC = {},
	) -> DictObj:
		if self.cache:
			for cache_set in self.cache:
				for cache_key in cache_set.queries.keys():
					cache_set.queries[cache_key] = None
					cache_query: LIMP_QUERY = eval(cache_key.split('____')[0])
					cache_special: LIMP_QUERY = eval(cache_key.split('____')[1])
					cache_query.append(cache_special)
					results = await Data.read(
						env=env,
						collection=self.collection,
						attrs=self.attrs,
						query=Query(cache_query),
					)
					cache_set.queries[cache_key] = CACHED_QUERY(results=results)
		return self.status(status=200, msg='Cache deleted.', args={})
