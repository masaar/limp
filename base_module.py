from config import Config
from event import Event
from data import Data
from utils import ClassSingleton, DictObj, validate_attr, call_event, Query
from base_model import BaseModel

from bson import ObjectId
import traceback, logging, datetime, time, re, copy

locales = {locale:'str' for locale in Config.locales}

logger = logging.getLogger('limp')

class BaseModule(metaclass=ClassSingleton):
	use_template = False
	collection = False
	extns = {}
	modules = {}
	privileges = ['read', 'create', 'update', 'delete', 'admin']

	def singleton(self):
		if not getattr(self, 'attrs', False): self.attrs = {}
		if not getattr(self, 'diff', False): self.diff = False
		if not getattr(self, 'optional_attrs', False): self.optional_attrs = []
		if not getattr(self, 'methods', False): self.methods = {}
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

	def pre_read(self, skip_events, env, session, query, doc):
		return (skip_events, env, session, query, doc)
	def on_read(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def read(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if Event.__PRE__ not in skip_events:
			# skip_events, env, session, query, doc = self.pre_read(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			pre_read = self.pre_read(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			if type(pre_read) in [DictObj, dict]: return pre_read
			skip_events, env, session, query, doc = pre_read
		if Event.__EXTN__ in skip_events:
			results = Data.read(env=env, session=session, collection=self.collection, attrs=self.attrs, extns={}, modules=self.modules, query=query) #pylint: disable=no-value-for-parameter
		# [DEPRECATED] query dict
		elif type(query) == dict and '$extn' in query.keys() and type(query['$extn']) == dict:
			results = Data.read(env=env, session=session, collection=self.collection, attrs=self.attrs, extns={ #pylint: disable=no-value-for-parameter
				extn:self.extns[extn] for extn in self.extns.keys() if extn in query['$extn'].keys() and query['$extn'][extn] == True
			}, modules=self.modules, query=query)
			del query['$extn']
		elif type(query) == Query and '$extn' in query and type(query['$extn']) == list:
			results = Data.read(env=env, session=session, collection=self.collection, attrs=self.attrs, extns={ #pylint: disable=no-value-for-parameter
				extn:self.extns[extn] for extn in self.extns.keys() if extn in query['$extn']
			}, modules=self.modules, query=query)
		else:
			results = Data.read(env=env, session=session, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query) #pylint: disable=no-value-for-parameter
		if Event.__ON__ not in skip_events:
			results, skip_events, env, session, query, doc = self.on_read(results=results, skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			# [DOC] if $attrs query arg is present return only required keys.
			# [DEPRECATED] query dict
			if type(query) == dict and '$attrs' in query.keys():
				query['$attrs'].insert(0, '_id')
				for i in range(0, results['docs'].__len__()):
					results['docs'][i] = {attr:results['docs'][i][attr] for attr in query['$attrs'] if attr in results['docs'][i]._attrs()}
			elif type(query) == Query and '$attrs' in query:
				query['$attrs'].insert(0, '_id')
				for i in range(0, results['docs'].__len__()):
					results['docs'][i] = {attr:results['docs'][i][attr] for attr in query['$attrs'] if attr in results['docs'][i]._attrs()}

		# [DOC] On succeful call, call notif events.
		if Event.__NOTIF__ not in skip_events:
			# [DOC] Call method events
			call_event(event='read', query=query, context_module=self, user_module=self.modules['user'], notification_module=self.modules['notification'])
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
			if attr not in doc.keys() and attr not in self.optional_attrs:
				return {
					'status':400,
					'msg':'Missing attr \'{}\' from request on module \'{}_{}\'.'.format(attr, self.__module__.replace('modules.', '').upper().split('.')[0], self.module_name.upper()), #pylint: disable=no-member
					'args':{'code':'{}_{}_MISSING_ATTR'.format(self.__module__.replace('modules.', '').upper().split('.')[0], self.module_name.upper())} #pylint: disable=no-member
				}
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
				if doc[attr] == 'true':
					doc[attr] = True
				elif doc[attr] == 'false':
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
		results = Data.create(env=env, session=session, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, doc=doc) #pylint: disable=no-value-for-parameter
		if Event.__ON__ not in skip_events:
			results, skip_events, env, session, query, doc = self.on_create(results=results, skip_events=skip_events, env=env, session=session, query=query, doc=doc)
		# [DOC] create soft action is to only retrurn the new created doc _id.
		if Event.__SOFT__ in skip_events:
			results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query=[[{'_id':results['docs'][0]}]])
			results = results['args']

		# [DOC] On succeful call, call notif events.
		if Event.__NOTIF__ not in skip_events:
			# [DOC] Call method events
			# logger.debug('checking create event on module: %s, with query: %s', self.module_name, query)
			call_event(event='create', query={'_id':{'val':results['docs']}}, context_module=self, user_module=self.modules['user'], notification_module=self.modules['notification'])
		return {
			'status':200,
			'msg':'Created {} docs.'.format(results['count']),
			'args':results
		}
	
	def pre_update(self, skip_events, env, session, query, doc):
		return (skip_events, env, session, query, doc)
	def on_update(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def update(self, skip_events=[], env={}, session=None, query=[], doc={}):
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
				if doc[attr] == 'true':
					doc[attr] = True
				elif doc[attr] == 'false':
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
		results = Data.update(env=env, session=session, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query, doc=doc) #pylint: disable=no-value-for-parameter
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
							'module':self.module_name, #pylint: disable=no-member
							'vars':doc
						})
						logger.debug('diff results: %s', diff_results)
						break
			else:
				diff_results = self.modules['diff'].methods['create'](skip_events=[Event.__PERM__], env=env, session=session, query=query, doc={
					'module':self.module_name, #pylint: disable=no-member
					'vars':doc
				})
				logger.debug('diff results: %s', diff_results)
		else:
			logger.debug('diff skipped: %s, %s, %s', results['count'], self.diff, Event.__DIFF__ not in skip_events)
		#logger.debug('docs update results: %s.', results)
		# [DOC] On succeful call, call notif events.
		if Event.__NOTIF__ not in skip_events:
			# [DOC] Call method events
			#logger.debug('checking update event on module: %s', self.module_name)
			call_event(event='update', query=query, context_module=self, user_module=self.modules['user'], notification_module=self.modules['notification'])
		return {
			'status':200,
			'msg':'Updated {} docs.'.format(results['count']),
			'args':results
		}
	
	def pre_delete(self, skip_events, env, session, query, doc):
		return (skip_events, env, session, query, doc)
	def on_delete(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def delete(self, skip_events=[], env={}, session=None, query=[], doc={}):
		# [TODO] refactor for template use
		if Event.__PRE__ not in skip_events: skip_events, env, session, query, doc = self.pre_delete(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
		# [TODO]: confirm all extns are not linked.
		# [DOC] delete soft action is to just flag the doc as deleted, without force removing it from db.
		results = Data.delete(env=env, session=session, collection=self.collection, attrs=self.attrs, extns={}, modules=self.modules, query=query, force_delete=(Event.__SOFT__ in skip_events)) #pylint: disable=no-value-for-parameter
		if Event.__ON__ not in skip_events: results, skip_events, env, session, query, doc = self.on_delete(results=results, skip_events=skip_events, env=env, session=session, query=query, doc=doc)
		return {
			'status':200,
			'msg':'Deleted {} docs.'.format(results['count']),
			'args':results
		}
	
	def retrieve_file(self, skip_events=[], env={}, session=None, query=[], doc={}):
		attr, filename = query['var']['val'].split(';')
		del query['var']
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
		if attr not in doc._attrs():
			return {
				'status': 404,
				'msg': 'File not found.',
				'args': {
					'code': '404 NOT FOUND'
				}
			}
		if type(doc[attr]) == list:
			for file in doc[attr]:
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
		else:
			if doc[attr]['name'] == filename:
				return {
					'status': 291,
					'msg': doc[attr]['content'],
					'args': {
						'name': doc[attr]['name'],
						'type': doc[attr]['type'],
						'size': doc[attr]['size']
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
						'msg':'Missing {} attr \'{}\' from request on module \'{}_{}\'.'.format(arg_list_label, arg[1:], self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper()),
						'args':DictObj({'code':'{}_{}_MISSING_ATTR'.format(self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper())})
					})
			
			elif type(arg) == tuple:
				optinal_arg_test = False
				for optional_arg in arg:
					if (arg_list_label == 'doc' and optional_arg not in args.keys()) or \
					(arg_list_label == 'query' and optional_arg not in args):
						optinal_arg_test = True
						break
				if optinal_arg_test == False:
					return DictObj({
						'status':400,
						'msg':'Missing at least one {} attr from [\'{}\'] from request on module \'{}_{}\'.'.format(arg_list_label, '\', \''.join(arg), self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper()),
						'args':DictObj({'code':'{}_{}_MISSING_ATTR'.format(self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper())})
					})

		
		# optional_args = True
		# for arg in args_list:
		# 	#logger.debug('checking optional_query_arg:%s', arg)
		# 	if arg[0] == '^':
		# 		if (args_list == 'doc' and arg[1:] in args.keys()) or \
		# 		(args_list == 'query' and arg[1:] in args):
		# 			optional_args = True
		# 			break
		# 		else:
		# 			if optional_args == True:
		# 				optional_args = []
		# 			optional_args.append(arg[1:])
		# 	#logger.debug('optional_args: %s', optional_args)
		# if optional_args != True:
		# 	return DictObj({
		# 		'status':400,
		# 		'msg':'Missing at least one {} attr from [\'{}\'] from request on module \'{}_{}\'.'.format(arg_list_label, '\', \''.join(optional_args), self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper()),
		# 		'args':DictObj({'code':'{}_{}_MISSING_ATTR'.format(self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper())})
		# 	})
		
		return True

	def __call__(self, skip_events=[], env={}, session=None, query=[], doc={}):
		# [DOC] Convert list query to Query object
		if type(query) == list:
			query = Query(query)
		if 'conn' not in env.keys():
			raise Exception('env missing conn')
		logger.debug('Calling: %s.%s, with sid:%s, query:%s, doc.keys:%s', self.module, self.method, str(session)[:30], str(query)[:250], doc.keys())

		if Event.__ARGS__ not in skip_events and Config.realm:
			# [DEPRECATED] query dict
			if type(query) == dict:
				query['realm'] = {'val':env['realm']}
			elif type(query) == Query:
				query.append({'realm':env['realm']})
			doc['realm'] = env['realm']
			logger.debug('Appended realm attrs to query, doc: %s, %s', str(query)[:250], doc.keys())

		if Event.__PERM__ not in skip_events and session:
			#logger.debug('checking permission, module: %s, permission: %s, sid:%s.', self.module, self.permissions, sid)
			permissions_check = self.module.modules['session'].check_permissions(session, self.module, self.permissions)
			#logger.debug('permissions_check: %s.', permissions_check)
			if permissions_check == False:
				return DictObj({
					'status':403,
					'msg':'You don\'t have permissions to access this endpoint.',
					'args':DictObj({'code':'CORE_SESSION_FORBIDDEN'})
				})
			else:
				# [DEPRECATED] query dict
				if type(query) == dict:
					query.update(permissions_check['query'])
				elif type(query) == Query:
					query.append(permissions_check['query'])
				doc.update(permissions_check['doc'])
	
		if Event.__ARGS__ not in skip_events:
			# [DEPRECATED] query dict
			if type(query) == dict:
				for arg in query.keys():
					if arg[0] != '$' and type(query[arg]) != dict:
						return DictObj({
							'status':400,
							'msg':'Query attr \'{}\' is not a known special attr, nor it follows the query object structure.'.format(arg),
							'args':DictObj({'code':'{}_{}_INVALID_QUERY'.format(self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper())})
						})

			test_query = self.test_args('query', query)
			if test_query != True: return test_query
		
			test_doc = self.test_args('doc', doc)
			if test_doc != True: return test_doc
				
		# [DEPRECATED] query dict
		if type(query) == dict:
			# [DOC] Convert any BaseModel object in query or docs to ObjectId
			for arg in query.keys():
				if type(query[arg]) == dict and 'val' in query[arg].keys() and type(query[arg]['val']) == BaseModel:
					query[arg]['val'] = query[arg]['val']._id

		for arg in doc.keys():
			if type(doc[arg]) == BaseModel:
				doc[arg] = doc[arg]._id

		# [DEPRECATED] query dict
		if type(query) == dict:
			# [DOC] check if $soft oper is set to add it to events
			if '$soft' in query.keys() and query['$soft'] == True:
				skip_events.append(Event.__SOFT__)
				del query['$soft']

			# [DOC] check if $extn oper is set to add it to events
			if '$extn' in query.keys() and query['$extn'] == False:
				skip_events.append(Event.__EXTN__)
				del query['$extn']
		elif type(query) == Query:
			# [DOC] check if $soft oper is set to add it to events
			if '$soft' in query and query['$soft'] == True:
				skip_events.append(Event.__SOFT__)
				del query['$soft']

			# [DOC] check if $extn oper is set to add it to events
			if '$extn' in query and query['$extn'] == False:
				skip_events.append(Event.__EXTN__)
				del query['$extn']

		if Config.debug:
			results = getattr(self.module, self.method)(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
		else:
			try:
				results = getattr(self.module, self.method)(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			except Exception as e:
				logger.error('An error occured. Details: %s.', traceback.format_exc())
				return DictObj({
					'status':500,
					'msg':'Unexpected error has occured [method:{}.{}] [{}].'.format(self.module.module_name, self.method, str(e)),
					'args':DictObj({'code':'CORE_SERVER_ERROR'})
				})
		
		results = DictObj(results)
		try:
			results.args = DictObj(results.args)
		except Exception:
			results.args = DictObj({})
		return results