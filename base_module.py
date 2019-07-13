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

locales = {locale:'str' for locale in Config.locales}

logger = logging.getLogger('limp')

class BaseModule:
	collection: Union[str, bool] = False
	attrs: Dict[str, Union[str, List[str], Tuple[str]]] = {}
	diff: bool = False
	optional_attrs: List[str] = []
	extns: Dict[str, List[Union[str, List[str]]]] = {}
	privileges: List[str] = ['read', 'create', 'update', 'delete', 'admin']
	methods: Dict[str, 'BaseMethod'] = {}

	package_name: str = None
	module_name: str = None
	modules: Dict[str, 'BaseModule'] = {}

	def __init__(self):
		self.package_name = self.__module__.replace('modules.', '').upper().split('.')[0]
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
					results['docs'][i] = BaseModel({attr:results['docs'][i][attr] for attr in query['$attrs'] if attr in results['docs'][i]._attrs()})

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
			doc['create_time'] = datetime.datetime.utcnow().isoformat()
		if 'host_add' in self.attrs.keys() and 'host_add' not in doc.keys():
			doc['host_add'] = env['REMOTE_ADDR']
		if 'user_agent' in self.attrs.keys() and 'user_agent' not in doc.keys():
			doc['user_agent'] = env['HTTP_USER_AGENT']
		# [DOC] Check presence and validate all attrs in doc args
		try:
			validate_doc(doc=doc, attrs=self.attrs, optional_attrs=self.optional_attrs)
		except MissingAttrException as e:
			return {
				'status':400,
				'msg':'{} \'create\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
				'args':{'code':'{}_{}_MISSING_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
			}
		except InvalidAttrException as e:
			return {
				'status':400,
				'msg':'{} \'create\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
				'args':{'code':'{}_{}_INVALID_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
			}
		except ConvertAttrException as e:
			return {
				'status':400,
				'msg':'{} \'create\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
				'args':{'code':'{}_{}_CONVERT_INVALID_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
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
		# [DOC] Check presence and validate all attrs in doc args
		try:
			validate_doc(doc=doc, attrs=self.attrs, optional_attrs=self.attrs.keys(), allow_opers=True)
		except MissingAttrException as e:
			return {
				'status':400,
				'msg':'{} \'update\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
				'args':{'code':'{}_{}_MISSING_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
			}
		except InvalidAttrException as e:
			return {
				'status':400,
				'msg':'{} \'update\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
				'args':{'code':'{}_{}_INVALID_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
			}
		except ConvertAttrException as e:
			return {
				'status':400,
				'msg':'{} \'update\' request on module \'{}_{}\'.'.format(str(e), self.package_name.upper(), self.module_name.upper()),
				'args':{'code':'{}_{}_CONVERT_INVALID_ATTR'.format(self.package_name.upper(), self.module_name.upper())}
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
	
	def pre_create_file(self, skip_events, env, session, query, doc):
		return (skip_events, env, session, query, doc)
	def on_create_file(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def create_file(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if Event.__PRE__ not in skip_events:
			pre_create_file = self.pre_create_file(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			if type(pre_create_file) in [DictObj, dict]: return pre_create_file
			skip_events, env, session, query, doc = pre_create_file
		
		if query['attr'][0] not in self.attrs.keys() or type(self.attrs[query['attr'][0]]) != list or not self.attrs[query['attr'][0]][0].startswith('file'):
			return {
				'status':400,
				'msg':'Attr is invalid.',
				'args':{'code':'{}_{}_INVALID_ATTR'.format(self.package_name, self.module_name.upper())}
			}
		
		results = self.update(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':query['_id'][0]}], doc={
			query['attr'][0]:{'$push':doc['file']}
		})

		if Event.__ON__ not in skip_events:
			results, skip_events, env, session, query, doc = self.on_create_file(results=results, skip_events=skip_events, env=env, session=session, query=query, doc=doc)
		
		return results

	def pre_update_file(self, skip_events, env, session, query, doc):
		return (skip_events, env, session, query, doc)
	def on_update_file(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def update_file(self, skip_events=[], env={}, session=None, query=[], doc={}):
		pass
	
	def pre_delete_file(self, skip_events, env, session, query, doc):
		return (skip_events, env, session, query, doc)
	def on_delete_file(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def delete_file(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if Event.__PRE__ not in skip_events:
			pre_delete_file = self.pre_delete_file(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			if type(pre_delete_file) in [DictObj, dict]: return pre_delete_file
			skip_events, env, session, query, doc = pre_delete_file

		if query['attr'][0] not in self.attrs.keys() or type(self.attrs[query['attr'][0]]) != list or not self.attrs[query['attr'][0]][0].startswith('file'):
			return {
				'status':400,
				'msg':'Attr is invalid.',
				'args':{'code':'{}_{}_INVALID_ATTR'.format(self.package_name, self.module_name.upper())}
			}

		results = self.read(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':query['_id'][0]}])
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
		
		results = self.update(skip_events=[Event.__PERM__], env=env, session=session, query=[{'_id':query['_id'][0]}], doc={
			query['attr'][0]:{'$pull':[doc[query['attr'][0]][query['index'][0]]]}
		})

		if Event.__ON__ not in skip_events:
			results, skip_events, env, session, query, doc = self.on_delete_file(results=results, skip_events=skip_events, env=env, session=session, query=query, doc=doc)

		return results

	def pre_retrieve_file(self, skip_events, env, session, query, doc):
		return (skip_events, env, session, query, doc)
	def on_retrieve_file(self, results, skip_events, env, session, query, doc):
		return (results, skip_events, env, session, query, doc)
	def retrieve_file(self, skip_events=[], env={}, session=None, query=[], doc={}):
		if Event.__PRE__ not in skip_events:
			pre_retrieve_file = self.pre_retrieve_file(skip_events=skip_events, env=env, session=session, query=query, doc=doc)
			if type(pre_retrieve_file) in [DictObj, dict]: return pre_retrieve_file
			skip_events, env, session, query, doc = pre_retrieve_file

		try:
			attr_name, thumb_dims, filename = query['var'][0].split(';')
			thumb_dims = tuple([int(dim) for dim in thumb_dims.split(',')])
		except:
			thumb_dims = False
			attr_name, filename = query['var'][0].split(';')
		del query['var'][0]

		results = self.read(skip_events=[Event.__PERM__], env=env, session=session, query=query)
		if not results.args.count: # pylint: disable=no-member
			return {
				'status': 404,
				'msg': 'File not found.',
				'args': {
					'code': '404 NOT FOUND'
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
				'status': 404,
				'msg': 'File not found.',
				'args': {
					'code': '404 NOT FOUND'
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
				file = item
		
		if file:
			results = {
				'status': 291,
				'msg': file['content'],
				'args': {
					'name': file['name'],
					'type': file['type'],
					'size': file['size']
				}
			}

			if thumb_dims:
				try:
					image = Image.open(io.BytesIO(file['content']))
					image.thumbnail(thumb_dims)
					stream = io.BytesIO()
					image.save(stream, format=image.format)
					stream.seek(0)
					file['content'] = stream.read()
				except:
					pass

			if Event.__ON__ not in skip_events:
				results, skip_events, env, session, query, doc = self.on_retrieve_file(results=results, skip_events=skip_events, env=env, session=session, query=query, doc=doc)

			return results
		else:
			# [DOC] No filename match
			return {
				'status': 404,
				'msg': 'File not found.',
				'args': {
					'code': '404 NOT FOUND'
				}
			}