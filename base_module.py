from config import Config
from event import Event
from data import Data
from utils import ClassSingleton, DictObj, validate_attr, call_event
from base_model import BaseModel

from bson import ObjectId
import traceback, logging, datetime, time, re, copy

locales = {locale:'str' for locale in Config.locales}

logger = logging.getLogger('limp')

class BaseModule(metaclass=ClassSingleton):
	use_template = False
	collection = ''
	extns = {}
	modules = {}
	privileges = ['read', 'create', 'update', 'delete', 'admin']

	def singleton(self):
		if not getattr(self, 'attrs', False): self.attrs = {}
		if not getattr(self, 'diff', False): self.diff = False
		if not getattr(self, 'optional_attrs', False): self.optional_attrs = []
		if not getattr(self, 'methods', False): self.methods = {}
		if self.use_template:
			self.attrs.update(BaseTemplate.template(self.template, 'attrs'))
			self.methods.update(BaseTemplate.template(self.template, 'methods'))
			self.diff = BaseTemplate.template(self.template, 'diff')
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
		# [DOC] If realm mode enabled, add realm attr to attrs, methods.
		# if Config.realm:
		# 	self.attrs['realm'] = 'str'
		# 	for method in self.methods.keys():
		# 		self.methods[method].query_args.append('!realm')
		# 		self.methods[method].doc_args.append('!realm')

	def pre_read(self, env, session, query, doc):
		return (env, session, query, doc)
	def on_read(self, results, env, session, query, doc):
		return (results, env, session, query, doc)
	def read(self, skip_events=[], env={}, session=None, query={}, doc={}):
		if self.use_template:
			env, session, query, doc = getattr(BaseTemplate, '{}_pre_read'.format(self.template))(env=env, session=session, query=query, doc=doc)
		if Event.__PRE__ not in skip_events:
			# env, session, query, doc = self.pre_read(env=env, session=session, query=query, doc=doc)
			pre_read = self.pre_read(env=env, session=session, query=query, doc=doc)
			if type(pre_read) in [DictObj, dict]: return pre_read
			env, session, query, doc = pre_read
		if Event.__EXTN__ in skip_events:
			results = Data.read(conn=env['conn'], session=session, collection=self.collection, attrs=self.attrs, extns={}, modules=self.modules, query=query)
		elif '$extn' in query.keys() and type(query['$extn']) == dict:
			results = Data.read(conn=env['conn'], session=session, collection=self.collection, attrs=self.attrs, extns={
				extn:self.extns[extn] for extn in self.extns.keys() if extn in query['$extn'].keys() and query['$extn'][extn] == True
			}, modules=self.modules, query=query)
			del query['$extn']
		else:
			results = Data.read(conn=env['conn'], session=session, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query)
		if Event.__ON__ not in skip_events:
			results, env, session, query, doc = self.on_read(results=results, env=env, session=session, query=query, doc=doc)
			# [DOC] if $attrs query arg is present return only required keys.
			if '$attrs' in query.keys():
				query['$attrs'].insert(0, '_id')
				for i in range(0, results['docs'].__len__()):
					results['docs'][i] = {attr:results['docs'][i][attr] for attr in query['$attrs'] if attr in results['docs'][i]._attrs()}

		if self.use_template:
			results, env, session, query, doc = getattr(BaseTemplate, '{}_on_read'.format(self.template))(results=results, env=env, session=session, query=query, doc=doc)
		# [DOC] On succeful call, call notif events.
		if Event.__NOTIF__ not in skip_events:
			# [DOC] Call method events
			#logger.debug('checking read event on module: %s', self.module_name)
			call_event(event='read', query=query, context_module=self, user_module=self.modules['user'], notification_module=self.modules['notification'])
		return {
			'status':200,#if results['count'] else 204,
			'msg':'Found {} docs.'.format(results['count']),
			'args':results
		}
	
	def pre_create(self, env, session, query, doc):
		return (env, session, query, doc)
	def on_create(self, results, env, session, query, doc):
		return (results, env, session, query, doc)
	def create(self, skip_events=[], env={}, session=None, query={}, doc={}):
		logger.debug('create method, session: %s', session)
		if self.use_template:
			env, session, query, doc = getattr(BaseTemplate, '{}_pre_create'.format(self.template))(env=env, session=session, query=query, doc=doc)
		if Event.__PRE__ not in skip_events:
			pre_create = self.pre_create(env=env, session=session, query=query, doc=doc)
			if type(pre_create) in [DictObj, dict]: return pre_create
			env, session, query, doc = pre_create
		# [TODO]: validate data
		# [DOC] Deleted all extra doc args
		del_args = []
		for arg in doc.keys():
			if arg not in self.attrs.keys() and (arg != '_id' and type(doc[arg]) != ObjectId):
				del_args.append(arg)
		for arg in del_args:
			del doc[arg]
		logger.debug('create method, session: %s', session)
		# [DOC] Append host_add, user_agent, create_time, diff if it's present in attrs.
		if 'user' in self.attrs.keys() and 'host_add' not in doc.keys() and session:
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
					'msg':'Missing attr \'{}\' from request on module \'{}_{}\'.'.format(attr, self.__module__.replace('modules.', '').upper().split('.')[0], self.module_name),
					'args':{'code':'{}_{}_MISSING_ATTR'.format(self.__module__.replace('modules.', '').upper().split('.')[0], self.module_name)}
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
			# [DOC] Pass value to validator
			if doc[attr] != None and not validate_attr(doc[attr], self.attrs[attr]):
				logger.debug('attr `%s`, value `%s` does not match required type `%s`.', attr, doc[attr], self.attrs[attr])
				return {
					'status':400,
					'msg':'Invalid value for attr \'{}\' from request on module \'{}_{}\'.'.format(attr, *self.__module__.replace('modules.', '').upper().split('.')),
					'args':{'code':'{}_{}_INVALID_ATTR'.format(*self.__module__.replace('modules.', '').upper().split('.'))}
				}
		results = Data.create(conn=env['conn'], session=session, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, doc=doc)
		if Event.__ON__ not in skip_events:
			results, env, session, query, doc = self.on_create(results=results, env=env, session=session, query=query, doc=doc)
		if self.use_template:
			results, env, session, query, doc = getattr(BaseTemplate, '{}_on_create'.format(self.template))(results=results, env=env, session=session, query=query, doc=doc)
		# [DOC] create soft action is to only retrurn the new created doc _id.
		if Event.__SOFT__ in skip_events:
			results = self.methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query={'_id':{'val':results['docs'][0]}, '$limit':1})
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
	
	def pre_update(self, env, session, query, doc):
		return (env, session, query, doc)
	def on_update(self, results, env, session, query, doc):
		return (results, env, session, query, doc)
	def update(self, skip_events=[], env={}, session=None, query={}, doc={}):
		if self.use_template:
			env, session, query, doc = getattr(BaseTemplate, '{}_pre_update'.format(self.template))(env=env, session=session, query=query, doc=doc)
		if Event.__PRE__ not in skip_events:
			pre_update = self.pre_update(env=env, session=session, query=query, doc=doc)
			if type(pre_update) in [DictObj, dict]: return pre_update
			env, session, query, doc = pre_update
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
		results = Data.update(conn=env['conn'], session=session, collection=self.collection, attrs=self.attrs, extns=self.extns, modules=self.modules, query=query, doc=doc)
		if Event.__ON__ not in skip_events:
			results, env, session, query, doc = self.on_update(results=results, env=env, session=session, query=query, doc=doc)
		if self.use_template:
			results, env, session, query, doc = getattr(BaseTemplate, '{}_on_update'.format(self.template))(results=results, env=env, session=session, query=query, doc=doc)
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
	
	def pre_delete(self, env, session, query, doc):
		return (env, session, query, doc)
	def on_delete(self, results, env, session, query, doc):
		return (results, env, session, query, doc)
	def delete(self, skip_events=[], env={}, session=None, query={}, doc={}):
		# [TODO] refactor for template use
		if Event.__PRE__ not in skip_events: env, session, query, doc = self.pre_delete(env=env, session=session, query=query, doc=doc)
		# [TODO]: confirm all extns are not linked.
		# [DOC] delete soft action is to just flag the doc as deleted, without force removing it from db.
		results = Data.delete(conn=env['conn'], session=session, collection=self.collection, attrs=self.attrs, extns={}, modules=self.modules, query=query, force_delete=(Event.__SOFT__ in skip_events))
		if Event.__ON__ not in skip_events: results, env, session, query, doc = self.on_delete(results=results, env=env, session=session, query=query, doc=doc)
		return {
			'status':200,
			'msg':'Deleted {} docs.'.format(results['count']),
			'args':results
		}
	
	def retrieve_file(self, skip_events=[], env={}, session=None, query={}, doc={}):
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

class BaseTemplate:
	templates = {
		'content':{
			'attrs':{
				'user':'id',
				'status':('scheduled', 'draft', 'pending', 'rejected', 'published'),
				'title':'locale',
				'subtitle':'locale',
				'permalink':'str',
				'content':'locale',
				'tags':['str'],
				'cat':'id',
				'access':'access',
				'create_time':'time',
				# 'update_time':'time',
				'expiry_time':'time'
			},
			'diff':True,
			'methods':{
				'read':{
					'permissions':[['read', {}, {}], ['__NOT:read', {'__OR:expiry_time':{'val':'$__time', 'oper':'$gt'}, '__OR:user':'$__user', 'access':'$__access'}, {}]]
				},
				'create':{
					'permissions':[['admin', {}, {}], ['create', {}, {'user':'$__user'}]]
				},
				'update':{
					'permissions':[['admin', {}, {}], ['update', {'user':'$__user'}, {'user':None}]],
					'query_args':['!_id']
				},
				'delete':{
					'permissions':[['admin', {}, {}], ['delete', {'user':'$__user'}, {}]],
					'query_args':['!_id']
				}
			}
		},
		'content_cat':{
			'attrs':{
				'user':'id',
				'title':'locale',
				'desc':'locale'
			},
			'diff':False,
			'methods':{
				'read':{
					'permissions':[['*', {}, {}]]
				},
				'create':{
					'permissions':[['create', {}, {'user':'$__user'}]]
				},
				'update':{
					'permissions':[['update', {}, {}], ['__NOT:update', {'user':'$__user'}, {'user':None}]],
					'query_args':['!_id']
				},
				'delete':{
					'permissions':[['delete', {}, {}], ['__NOT:delete', {'user':'$__user'}, {}]],
					'query_args':['!_id']
				}
			}
		}
	}
	
	@classmethod
	def template(self, template, attr):
		return self.templates[template][attr]
	
	# content method:
	@classmethod
	def content_pre_read(self, env, session, query, doc):
		return (env, session, query, doc)
	@classmethod
	def content_on_read(self, results, env, session, query, doc):
		return (results, env, session, query, doc)
	@classmethod
	def content_pre_create(self, env, session, query, doc):
		if 'subtitle' not in doc.keys(): doc['subtitle'] = {locale:'' for locale in Config.locales}
		if 'permalink' not in doc.keys(): doc['permalink'] = re.sub(r'\s+', '-', re.sub(r'[^\s\-\w]', '', doc['title'][Config.locale]))
		if 'tags' not in doc.keys(): doc['tags'] = []
		if 'cat' not in doc.keys(): doc['cat'] = False
		return (env, session, query, doc)
	@classmethod
	def content_on_create(self, results, env, session, query, doc):
		return (results, env, session, query, doc)
	@classmethod
	def content_pre_update(self, env, session, query, doc):
		return (env, session, query, doc)
	@classmethod
	def content_on_update(self, results, env, session, query, doc):
		return (results, env, session, query, doc)
	@classmethod
	def content_pre_delete(self, env, session, query, doc):
		return (env, session, query, doc)
	@classmethod
	def content_on_delete(self, results, env, session, query, doc):
		return (results, env, session, query, doc)

	# cat methods:
	@classmethod
	def content_cat_pre_read(self, env, session, query, doc):
		return (env, session, query, doc)
	@classmethod
	def content_cat_on_read(self, results, env, session, query, doc):
		return (results, env, session, query, doc)
	@classmethod
	def content_cat_pre_create(self, env, session, query, doc):
		return (env, session, query, doc)
	@classmethod
	def content_cat_on_create(self, results, env, session, query, doc):
		return (results, env, session, query, doc)
	@classmethod
	def content_cat_pre_update(self, env, session, query, doc):
		return (env, session, query, doc)
	@classmethod
	def content_cat_on_update(self, results, env, session, query, doc):
		return (results, env, session, query, doc)
	@classmethod
	def content_cat_pre_delete(self, env, session, query, doc):
		return (env, session, query, doc)
	@classmethod
	def content_cat_on_delete(self, results, env, session, query, doc):
		return (results, env, session, query, doc)

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

		for arg in args_list:

			if arg[0] == '!':
				if arg[1:] not in args.keys() \
				or (
					arg_list_label == 'query' and arg[1] != '$' and (args[arg[1:]]['val'] == None or args[arg[1:]]['val'] == '') \
					or arg_list_label == 'query' and arg[1] == '$' and (args[arg[1:]] == None or args[arg[1:]] == '')
				):
					return DictObj({
						'status':400,
						'msg':'Missing attr \'{}\' from request on module \'{}_{}\'.'.format(arg[1:], self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper()),
						'args':DictObj({'code':'{}_{}_MISSING_ATTR'.format(self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper())})
					})
		
		optional_args = True
		for arg in args_list:
			#logger.debug('checking optional_query_arg:%s', arg)
			if arg[0] == '^':
				if arg[1:] in args.keys() \
				and (arg_list_label != 'query' or \
				(arg_list_label == 'query' and arg[1] != '$' and (args[arg[1:]]['val'] != None and args[arg[1:]]['val'] != '') \
				or arg_list_label == 'query' and arg[1] == '$' and (args[arg[1:]] != None and args[arg[1:]] != ''))):
					optional_args = True
					break
				else:
					if optional_args == True:
						optional_args = []
					optional_args.append(arg[1:])
			#logger.debug('optional_args: %s', optional_args)
		if optional_args != True:
			return DictObj({
				'status':400,
				'msg':'Missing at least one attr from [\'{}\'] from request on module \'{}_{}\'.'.format('\', \''.join(optional_args), self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper()),
				'args':DictObj({'code':'{}_{}_MISSING_ATTR'.format(self.module.__module__.replace('modules.', '').upper().split('.')[0], self.module.module_name.upper())})
			})
		
		return True

	def __call__(self, skip_events=[], env={}, session=None, query={}, doc={}):
		if 'conn' not in env.keys():
			raise Exception('env missing conn')
		logger.debug('Calling: %s.%s, with sid:%s, query:%s, doc.keys:%s', self.module, self.method, str(session)[:30], str(query)[:250], doc.keys())

		if Config.realm:
			try:
				query['realm'] = {'val':session.user.attrs['realm']}
				doc['realm'] = session.user.attrs['realm']
			except Exception:
				query['realm'] = {'val':env['realm']}
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
				query.update(permissions_check['query'])
				doc.update(permissions_check['doc'])
	
		if Event.__ARGS__ not in skip_events:
			test_query = self.test_args('query', query)
			if test_query != True: return test_query
		
			test_doc = self.test_args('doc', doc)
			if test_doc != True: return test_doc
				
		# [DOC] Convert any BaseModel object in query or docs to ObjectId
		for arg in query.keys():
			if type(query[arg]) == dict and 'val' in query[arg].keys() and type(query[arg]['val']) == BaseModel:
				query[arg]['val'] = query[arg]['val']._id
		for arg in doc.keys():
			if type(doc[arg]) == BaseModel:
				doc[arg] = doc[arg]._id


		#logger.debug('$extn is in skip_events: %s.', Event.__EXTN__ in skip_events)
		# [DOC] check if $soft oper is set to add it to events
		if '$soft' in query.keys() and query['$soft'] == True:
			skip_events.append(Event.__SOFT__)
			del query['$soft']
		#logger.debug('$soft is in skip_events: %s.', Event.__SOFT__ in skip_events)
		# [DOC] check if $extn oper is set to add it to events
		if '$extn' in query.keys() and query['$extn'] == False:
			skip_events.append(Event.__EXTN__)
			del query['$extn']
		#logger.debug('$extn is in skip_events: %s.', Event.__EXTN__ in skip_events)
		# [DOC] check if $diff oper is set to add it to events
		# if '$diff' not in query.keys() or query['$diff'] != True:
		# 	skip_events.append(Event.__DIFF__)

		if Config.debug:
			results = getattr(self.module, self.method)(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
		else:
			try:
				# #logger.debug('2. calling: %s.%s, with sid:%s, query:%s, doc:%s. skip_events:%s.', self.module, self.method, env, session, query, doc, skip_events)
				results = getattr(self.module, self.method)(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			except Exception as e:
				logger.error('An error occured. Details: %s.', traceback.format_exc())
				# raise e
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