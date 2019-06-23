from config import Config
from event import Event
from data import Data, DELETE_SOFT_SKIP_SYS, DELETE_SOFT_SYS, DELETE_FORCE_SKIP_SYS, DELETE_FORCE_SYS
from utils import DictObj, validate_attr, Query
from base_model import BaseModel

from typing import List, Dict, Union, Tuple, Any

from bson import ObjectId
import traceback, logging, datetime, time, re, sys, copy

locales = {locale:'str' for locale in Config.locales}

logger = logging.getLogger('limp')

class BaseModule():
	collection: Union[str, bool] = False
	attrs: Dict[str, Union[str, List[str], Tuple[str]]] = {}
	diff: bool = False
	optional_attrs: List[str] = []
	extns: Dict[str, List[Union[str, List[str]]]] = {}
	privileges: List[str] = ['read', 'create', 'update', 'delete', 'admin']
	methods: Dict[str, 'BaseMethod'] = {}

	module_name: str = None
	modules: Dict[str, 'BaseModule'] = {}

	def __init__(self):
		self.module_name = re.sub(r'([A-Z])', r'_\1', self.__class__.__name__[0].lower() + self.__class__.__name__[1:]).lower()
		for method in self.methods.keys():
			if 'query_args' not in self.methods[method].keys():
				self.methods[method]['query_args'] = []
			if 'doc_args' not in self.methods[method].keys():
				self.methods[method]['doc_args'] = []
			if 'get_method' not in self.methods[method].keys():
				self.methods[method]['get_method'] = False
			self.methods[method] = BaseMethod(
				module=self,
				method=method,
				permissions=self.methods[method]['permissions'],
				query_args=self.methods[method]['query_args'],
				doc_args=self.methods[method]['doc_args'],
				get_method=self.methods[method]['get_method']
			)
		for attr in self.attrs.keys():
			if self.attrs[attr] == 'locale':
				self.attrs[attr] = locales
		logger.debug('Initialised module %s', self.module_name)
	
	def __getattribute__(self, attr):
		if attr in object.__getattribute__(self, 'methods').keys():
			return object.__getattribute__(self, 'methods')[attr]
		elif attr.startswith('_method_'):
			return object.__getattribute__(self, attr.replace('_method_', ''))
		else:
			return object.__getattribute__(self, attr)

	def pre_read(self, skip_events: List[str], env: Dict[str, Any], session: BaseModel, query: Query, doc: Dict[str, Any]) -> (List[str], Dict[str, Any], BaseModel, Query, Dict[str, Any]):
		return (skip_events, env, session, query, doc)
	def on_read(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def read(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if Event.__PRE__ not in skip_events:
			
			pre_read = self.pre_read(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			if type(pre_read) in [DictObj, dict]: return pre_read
			skip_events, env, session, query, doc = pre_read
		if Event.__EXTN__ in skip_events:
			results = Data.read(env=env, session=session, collection=self.collection, attrs=self.attrs, extns={}, modules=self.modules, query=query)
		elif '$extn' in query and type(query['$extn']) == list:
			results = Data.read(env=env, session=session, collection=self.collection, attrs=self.attrs, extns={
				extn:self.extns[extn] for extn in self.extns.keys() if extn in query['$extn']
			}, modules=self.modules, query=query)
		else:
			results = Data.read(env=env, session=session, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query)
		if Event.__ON__ not in skip_events:
			results, skip_events, env, session, query, doc = self.on_read(results=results, skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			# [DOC] if $attrs query arg is present return only required keys.
			if '$attrs' in query:
				query['$attrs'].insert(0, '_id')
				for i in range(0, results['docs'].__len__()):
					results['docs'][i] = {attr:results['docs'][i][attr] for attr in query['$attrs'] if attr in results['docs'][i]._attrs()}

		return {
			'status':200,#if results['count'] else 204,
			'msg':'Found {} docs.'.format(results['count']),
			'args':results
		}
	
	def pre_create(self, skip_events, env, session, query, doc):
		return (skip_events, env, session, query, doc)
	def on_create(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def create(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if Event.__PRE__ not in skip_events:
			pre_create = self.pre_create(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			if type(pre_create) in [DictObj, dict]: return pre_create
			skip_events, env, session, query, doc = pre_create
		# [TODO]: validate data
		# [DOC] Deleted all extra doc args
		del_args = []
		for arg in doc.keys():
			if arg not in self.attrs.keys() and (arg != '_id' and type(doc[arg]) != ObjectId):
				del_args.append(arg)
		for arg in del_args:
			del doc[arg]
		# [DOC] Append host_add, user_agent, create_time, diff if it's present in attrs.
		if 'user' in self.attrs.keys() and 'host_add' not in doc.keys() and session and Event.__ARGS__ not in skip_events:
			doc['user'] = session.user._id
		if 'create_time' in self.attrs.keys():
			doc['create_time'] = datetime.datetime.fromtimestamp(time.time())
		if 'host_add' in self.attrs.keys() and 'host_add' not in doc.keys():
			doc['host_add'] = env['REMOTE_ADDR']
		if 'user_agent' in self.attrs.keys() and 'user_agent' not in doc.keys():
			doc['user_agent'] = env['HTTP_USER_AGENT']
		# [DOC] Check presence and validate all attrs in doc args
		#logger.debug('%s has following attrs: %s.', self.__module__, self.attrs.keys())
		for attr in self.attrs.keys():
			# [DOC] Allow optional_attrs to bypass requirement check
			if Event.__ARGS__ not in skip_events and attr not in doc.keys() and attr not in self.optional_attrs:
				return {
					'status':400,
					'msg':'Missing doc attr \'{}\' from \'create\' request on module \'{}_{}\'.'.format(attr, self.__module__.replace('modules.', '').upper().split('.')[0], self.module_name.upper()),
					'args':{'code':'{}_{}_MISSING_ATTR'.format(self.__module__.replace('modules.', '').upper().split('.')[0], self.module_name.upper())}
				}
			elif Event.__ARGS__ in skip_events and attr not in doc.keys():
				continue
			elif attr not in doc.keys() and attr in self.optional_attrs:
				doc[attr] = None
			# [DOC] Convert id attr passed as str to ObjectId
			if self.attrs[attr] == 'id' and type(doc[attr]) == str:
				try:
					doc[attr] = ObjectId(doc[attr])
				except:
					return {
						'status':400,
						'msg':'Value for attr \'{}\' couldn\'t be converted to \'id\' from request on module \'{}_{}\'.'.format(attr, *self.__module__.replace('modules.', '').upper().split('.')),
						'args':{'code':'{}_{}_INVALID_ATTR'.format(*self.__module__.replace('modules.', '').upper().split('.'))}
					}
			if type(self.attrs[attr]) == list and self.attrs[attr][0] == 'id' and type(doc[attr]) == list:
				try:
					id_list = []
					for _id in doc[attr]:
						if type(_id) == BaseModel: _id = _id._id
						id_list.append(ObjectId(_id))
					doc[attr] = id_list
				except:
					return {
						'status':400,
						'msg':'Value for attr \'{}\' couldn\'t be converted to \'id\' from request on module \'{}_{}\'.'.format(attr, *self.__module__.replace('modules.', '').upper().split('.')),
						'args':{'code':'{}_{}_INVALID_ATTR'.format(*self.__module__.replace('modules.', '').upper().split('.'))}
					}
			# [DOC] Convert bool attr passed as str to bool
			if self.attrs[attr] == 'bool' and type(doc[attr]) == str:
				#logger.debug('Converting str %s attr to bool %s', attr,doc[attr])
				if doc[attr].lower() == 'true':
					doc[attr] = True
				elif doc[attr].lower() == 'false':
					doc[attr] = False
			# [DOC] Convert time attr passed as int to datetime
			if self.attrs[attr] == 'time' and type(doc[attr]) == int:
				try:
					doc[attr] = datetime.datetime.fromtimestamp(doc[attr])
				except:
					return {
						'status':400,
						'msg':'Value for attr \'{}\' couldn\'t be converted to \'datetime\' from request on module \'{}_{}\'.'.format(attr, *self.__module__.replace('modules.', '').upper().split('.')),
						'args':{'code':'{}_{}_INVALID_ATTR'.format(*self.__module__.replace('modules.', '').upper().split('.'))}
					}
			# [DOC] Check file attr and extract first file
			if self.attrs[attr] == 'file' and type(doc[attr]) == list and doc[attr].__len__() and validate_attr(doc[attr][0], self.attrs[attr]):
				doc[attr] = doc[attr][0]
			# [DOC] Pass value to validator
			if doc[attr] != None and not validate_attr(doc[attr], self.attrs[attr]):
				logger.debug('attr `%s`, value `%s` does not match required type `%s`.', attr, doc[attr], self.attrs[attr])
				return {
					'status':400,
					'msg':'Invalid value for attr \'{}\' from request on module \'{}_{}\'.'.format(attr, *self.__module__.replace('modules.', '').upper().split('.')),
					'args':{'code':'{}_{}_INVALID_ATTR'.format(*self.__module__.replace('modules.', '').upper().split('.'))}
				}
		results = Data.create(env=env, session=session, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, doc=doc)
		if Event.__ON__ not in skip_events:
			results, skip_events, env, session, query, doc = self.on_create(results=results, skip_events=skip_events, env=env, session=session, query=query, doc=doc)
		# [DOC] create soft action is to only retrurn the new created doc _id.
		if Event.__SOFT__ in skip_events:
			results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=[[{'_id':results['docs'][0]}]])
			results = results['args']

		return {
			'status':200,
			'msg':'Created {} docs.'.format(results['count']),
			'args':results
		}
	
	def pre_update(self, skip_events, env, session, query, doc):
		return (skip_events, env, session, query, doc)
	def on_update(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def update(self, skip_events=[], env={}, session=None, query=[], doc={}) -> DictObj:
		if Event.__PRE__ not in skip_events:
			pre_update = self.pre_update(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			if type(pre_update) in [DictObj, dict]: return pre_update
			skip_events, env, session, query, doc = pre_update
		# [TODO] validate data
		for attr in self.attrs.keys():
			if attr not in doc.keys(): continue
			# [DOC] Convert id attr passed as str to ObjectId
			if self.attrs[attr] == 'id' and type(doc[attr]) == str:
				try:
					doc[attr] = ObjectId(doc[attr])
				except:
					return {
						'status':400,
						'msg':'Value for attr \'{}\' couldn\'t be converted to \'id\' from request on module \'{}_{}\'.'.format(attr, *self.__module__.replace('modules.', '').upper().split('.')),
						'args':{'code':'{}_{}_INVALID_ATTR'.format(*self.__module__.replace('modules.', '').upper().split('.'))}
					}
			# HERE HERE HERE
			if type(self.attrs[attr]) == list and self.attrs[attr][0] == 'id' and type(doc[attr]) == list:
				try:
					id_list = []
					for _id in doc[attr]:
						if type(_id) == BaseModel: _id = _id._id
						id_list.append(ObjectId(_id))
					doc[attr] = id_list
					# doc[attr] = [ObjectId(_id) for _id in doc[attr]]
				except:
					return {
						'status':400,
						'msg':'Value for attr \'{}\' couldn\'t be converted to \'id\' from request on module \'{}_{}\'.'.format(attr, *self.__module__.replace('modules.', '').upper().split('.')),
						'args':{'code':'{}_{}_INVALID_ATTR'.format(*self.__module__.replace('modules.', '').upper().split('.'))}
					}
			# [DOC] Convert bool attr passed as str to bool
			if self.attrs[attr] == 'bool' and type(doc[attr]) == str:
				if doc[attr].lower() == 'true':
					doc[attr] = True
				elif doc[attr].lower() == 'false':
					doc[attr] = False
			# [DOC] Convert time attr passed as int to datetime
			if self.attrs[attr] == 'time' and type(doc[attr]) == int:
				try:
					doc[attr] = datetime.datetime.fromtimestamp(doc[attr])
				except:
					return {
						'status':400,
						'msg':'Value for attr \'{}\' couldn\'t be converted to \'datetime\' from request on module \'{}_{}\'.'.format(attr, *self.__module__.replace('modules.', '').upper().split('.')),
						'args':{'code':'{}_{}_INVALID_ATTR'.format(*self.__module__.replace('modules.', '').upper().split('.'))}
					}
			# [DOC] Check file attr and extract first file
			if self.attrs[attr] == 'file' and type(doc[attr]) == list and doc[attr].__len__() and validate_attr(doc[attr][0], self.attrs[attr]):
				doc[attr] = doc[attr][0]
			# [DOC] Pass value to validator
			if not validate_attr(doc[attr], self.attrs[attr]):
				return {
					'status':400,
					'msg':'Invalid value for attr \'{}\' from request on module \'{}_{}\'.'.format(attr, *self.__module__.replace('modules.', '').upper().split('.')),
					'args':{'code':'{}_{}_INVALID_ATTR'.format(*self.__module__.replace('modules.', '').upper().split('.'))}
				}
		# [DOC] Delete all attrs not belonging to the doc
		del_args = []
		for arg in doc.keys():
			if arg not in self.attrs.keys() or doc[arg] == None:
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
		results = Data.update(env=env, session=session, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query, doc=doc)
		if Event.__ON__ not in skip_events:
			results, skip_events, env, session, query, doc = self.on_update(results=results, skip_events=skip_events, env=env, session=session, query=query, doc=doc)
		# [DOC] If at least one doc updated, and module has diff enabled, and __DIFF__ not skippend:
		if results['count'] and self.diff and Event.__DIFF__ not in skip_events:
			# [DOC] If diff is a list, make sure the updated fields are not in the execluded list.
			if type(self.diff) == list:
				for attr in doc.keys():
					# [DOC] If at least on attr is not in the execluded list, create diff doc.
					if attr not in self.diff:
						diff_results = self.modules['diff'].methods['create'](skip_events=[Event.__PERM__], env=env, session=session, query=query, doc={
							'module':self.module_name,
							'vars':doc
						})
						logger.debug('diff results: %s', diff_results)
						break
			else:
				diff_results = self.modules['diff'].methods['create'](skip_events=[Event.__PERM__], env=env, session=session, query=query, doc={
					'module':self.module_name,
					'vars':doc
				})
				logger.debug('diff results: %s', diff_results)
		else:
			logger.debug('diff skipped: %s, %s, %s', results['count'], self.diff, Event.__DIFF__ not in skip_events)

		return {
			'status':200,
			'msg':'Updated {} docs.'.format(results['count']),
			'args':results
		}
	
	def pre_delete(self, skip_events, env, session, query, doc):
		return (skip_events, env, session, query, doc)
	def on_delete(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def delete(self, skip_events=[], env={}, session=None, query=[], doc={}) -> DictObj:
		# [TODO] refactor for template use
		if Event.__PRE__ not in skip_events: skip_events, env, session, query, doc = self.pre_delete(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
		# [TODO]: confirm all extns are not linked.
		# [DOC] Pick delete strategy based on skip_events
		strategy = DELETE_SOFT_SKIP_SYS
		if Event.__SOFT__ not in skip_events and Event.__SYS_DOCS__ in skip_events:
			strategy = DELETE_SOFT_SYS
		elif Event.__SOFT__ in skip_events and Event.__SYS_DOCS__ not in skip_events:
			strategy = DELETE_FORCE_SKIP_SYS
		elif Event.__SOFT__ in skip_events and Event.__SYS_DOCS__ in skip_events:
			strategy = DELETE_FORCE_SYS
		results = Data.delete(env=env, session=session, collection=self.collection, attrs=self.attrs, extns={}, modules=self.modules, query=query, strategy=strategy)
		if Event.__ON__ not in skip_events: results, skip_events, env, session, query, doc = self.on_delete(results=results, skip_events=skip_events, env=env, session=session, query=query, doc=doc)
		return {
			'status':200,
			'msg':'Deleted {} docs.'.format(results['count']),
			'args':results
		}
	
	def retrieve_file(self, skip_events=[], env={}, session=None, query=[], doc={}):
		attr_name, filename = query['var'][0].split(';')
		del query['var'][0]
		results = self.methods['read'](skip_events=[Event.__PERM__, Event.__ON__], env=env, session=session, query=query)
		if not results['args']['count']:
			return {
				'status': 404,
				'msg': 'File not found.',
				'args': {
					'code': '404 NOT FOUND'
				}
			}
		doc = results['args']['docs'][0]
		try:
			attr_path = attr_name.split('.')
			attr = doc
			for path in attr_path:
				attr = doc[path]
		except:
			return {
				'status': 404,
				'msg': 'File not found.',
				'args': {
					'code': '404 NOT FOUND'
				}
			}

		if type(attr) == list:
			for file in attr:
				if file['name'] == filename:
					return {
						'status': 291,
						'msg': file['content'],
						'args': {
							'name': file['name'],
							'type': file['type'],
							'size': file['size']
						}
					}
		elif type(attr) == dict:
			if attr['name'] == filename:
				return {
					'status': 291,
					'msg': attr['content'],
					'args': {
						'name': attr['name'],
						'type': attr['type'],
						'size': attr['size']
					}
				}
		# [DOC] No filename match
		return {
			'status': 404,
			'msg': 'File not found.',
			'args': {
				'code': '404 NOT FOUND'
			}
		}

class BaseMethod:

	def __init__(self, module, method, permissions, query_args, doc_args, get_method = False):
		self.module = module
		self.method = method
		self.permissions = permissions
		self.query_args = query_args
		self.doc_args = doc_args
		self.get_method = get_method
	
	def test_args(self, args_list, args):
		arg_list_label = args_list
		if args_list == 'query':
			args_list = self.query_args
		elif args_list == 'doc':
			args_list = self.doc_args

		logger.debug('testing args, list: %s, args: %s', arg_list_label, str(args)[:256])

		for arg in args_list:

			if type(arg) == str:
				if (arg_list_label == 'doc' and arg not in args.keys()) or \
				(arg_list_label == 'query' and arg not in args):
					return DictObj({
						'status':400,
						'msg':'Missing {} attr \'{}\' from request on module \'{}_{}\'.'.format(arg_list_label, arg, self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper()),
						'args':DictObj({'code':'{}_{}_MISSING_ATTR'.format(self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper())})
					})
			
			elif type(arg) == tuple:
				optinal_arg_test = False
				for optional_arg in arg:
					if (arg_list_label == 'doc' and optional_arg in args.keys()) or \
					(arg_list_label == 'query' and optional_arg in args):
						optinal_arg_test = True
						break
				if optinal_arg_test == False:
					return DictObj({
						'status':400,
						'msg':'Missing at least one {} attr from [\'{}\'] from request on module \'{}_{}\'.'.format(arg_list_label, '\', \''.join(arg), self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper()),
						'args':DictObj({'code':'{}_{}_MISSING_ATTR'.format(self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper())})
					})
		
		return True

	def __call__(self, skip_events=[], env={}, session=None, query=[], doc={}) -> DictObj:
		# [DEPRECATED] Convert dict query to compatible list query
		if type(query) == dict:
			logger.debug('Detected deprecated dict query. Attempting to convert it to Query object: %s', query)
			dict_query = query
			query = [{}, []]

			for attr in dict_query.keys():
				query_attr = dict_query[attr]
				if attr[0] != '$':
					if type(query_attr) != dict: continue
					if 'oper' in query_attr.keys() and query_attr['oper'] in ['$gt', '$lt', '$gte', '$lte', '$bet', '$not', '$regex', '$all', '$in']:
						if query_attr['oper'] == '$bet':
							query_attr = {'$bet':[query_attr['val'], query_attr['val2']]}
						else:
							query_attr = {query_attr['oper']:query_attr['val']}
					else:
						query_attr = query_attr['val']
					query[0][attr] = query_attr
				elif attr.startswith('__OR:'):
					query[1].append({attr.replace('__OR:', ''):query_attr})
				else:
					query[0][attr] = query_attr

		# [DOC] Convert list query to Query object
		query = Query(copy.deepcopy(query))
		# [DOC] deepcopy() doc object ro prevent duplicate memory alloc
		doc = copy.deepcopy(doc)


		logger.debug('Calling: %s.%s, with sid:%s, query:%s, doc.keys:%s', self.module.module_name, self.method, str(session)[:30], str(query)[:250], doc.keys())

		if Event.__ARGS__ not in skip_events and Config.realm:
			if self.module.module_name == 'realm':
				query.append({'name':env['realm']})
				doc['name'] = env['realm']
				logger.debug('Appended realm name attrs to query, doc: %s, %s', str(query)[:250], doc.keys())
			else:
				query.append({'realm':env['realm']})
				doc['realm'] = env['realm']
				logger.debug('Appended realm attrs to query, doc: %s, %s', str(query)[:250], doc.keys())

		if Event.__PERM__ not in skip_events and session:
			#logger.debug('checking permission, module: %s, permission: %s, sid:%s.', self.module, self.permissions, sid)
			permissions_check = self.module.modules['session'].check_permissions(session, self.module, self.permissions)
			logger.debug('permissions_check: %s.', permissions_check)
			if permissions_check == False:
				return DictObj({
					'status':403,
					'msg':'You don\'t have permissions to access this endpoint.',
					'args':DictObj({'code':'CORE_SESSION_FORBIDDEN'})
				})
			else:
				query.append(copy.deepcopy(permissions_check['query']))
				doc.update(copy.deepcopy(permissions_check['doc']))
	
		if Event.__ARGS__ not in skip_events:
			test_query = self.test_args('query', query)
			if test_query != True: return test_query
		
			test_doc = self.test_args('doc', doc)
			if test_doc != True: return test_doc

		for arg in doc.keys():
			if type(doc[arg]) == BaseModel:
				doc[arg] = doc[arg]._id
				
		# [DOC] check if $soft oper is set to add it to events
		if '$soft' in query and query['$soft'] == True:
			skip_events.append(Event.__SOFT__)
			del query['$soft']

		# [DOC] check if $extn oper is set to add it to events
		if '$extn' in query and query['$extn'] == False:
			skip_events.append(Event.__EXTN__)
			del query['$extn']

		try:
			results = getattr(self.module, '_method_{}'.format(self.method))(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			query = Query([])
		except Exception as e:
			logger.error('An error occured. Details: %s.', traceback.format_exc())
			exc_type, exc_value, tb = sys.exc_info()
			if tb is not None:
				prev = tb
				curr = tb.tb_next
				while curr is not None:
					prev = curr
					curr = curr.tb_next
				logger.error('Scope variables: %s', prev.tb_frame.f_locals)
			query = Query([])
			if Config.debug:
				return DictObj({
					'status':500,
					'msg':'Unexpected error has occured [method:{}.{}] [{}].'.format(self.module.module_name, self.method, str(e)),
					'args':DictObj({'code':'CORE_SERVER_ERROR', 'method':'{}.{}'.format(self.module.module_name, self.method), 'err':str(e)})
				})
			else:
				return DictObj({
					'status':500,
					'msg':'Unexpected error has occured.',
					'args':DictObj({'code':'CORE_SERVER_ERROR'})
				})
		
		results = DictObj(results)
		try:
			results.args = DictObj(results.args)
		except Exception:
			results.args = DictObj({})
		return results