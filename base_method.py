from utils import DictObj, Query
from event import Event
from config import Config
from base_model import BaseModel

import logging, copy, traceback, sys

logger = logging.getLogger('limp')

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
						'msg':'Missing {} attr \'{}\' from request on module \'{}_{}\'.'.format(arg_list_label, arg, self.module.package_name.upper(), self.module.module_name.upper()),
						'args':DictObj({'code':'{}_{}_MISSING_ATTR'.format(self.module.package_name.upper(), self.module.module_name.upper())})
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
						'msg':'Missing at least one {} attr from [\'{}\'] from request on module \'{}_{}\'.'.format(arg_list_label, '\', \''.join(arg), self.module.package_name.upper(), self.module.module_name.upper()),
						'args':DictObj({'code':'{}_{}_MISSING_ATTR'.format(self.module.package_name.upper(), self.module.module_name.upper())})
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


		logger.debug('Calling: %s.%s, with skip_events:%s, query:%s, doc.keys:%s', self.module.module_name, self.method, skip_events, str(query)[:250], doc.keys())

		if Event.__ARGS__ not in skip_events and Config.realm:
			if self.module.module_name == 'realm':
				if self.method != 'create':
					query.append({'name':env['realm']})
					doc['name'] = env['realm']
					logger.debug('Appended realm name attrs to query, doc: %s, %s', str(query)[:250], doc.keys())
				else:
					logger.debug('Skipped Appending realm name attrs to query, doc for realm.create call')
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
			tb = sys.exc_info()[2]
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
			results['args'] = DictObj(results.args)
		except Exception:
			results['args'] = DictObj({})
		return results