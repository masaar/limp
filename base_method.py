from utils import DictObj, Query, NONE_VALUE, JSONEncoder, validate_attr, InvalidAttrException, ConvertAttrException
from event import Event
from config import Config
from base_model import BaseModel

import logging, copy, traceback, sys, asyncio

logger = logging.getLogger('limp')

class BaseMethod:
	def __init__(self, module, method, permissions, query_args, doc_args, watch_method, get_method, get_args):
		self.module = module
		self.method = method
		self.permissions = permissions
		self.query_args = query_args
		self.doc_args = doc_args
		self.watch_method = watch_method
		self.get_method = get_method
		self.get_args = get_args
	
	def validate_args(self, args, args_list):
		args_list_label = args_list
		args_list = getattr(self, f'{args_list}_args')

		sets_check = []

		for args_set in args_list:
			set_status = True
			set_check = len(sets_check)
			sets_check.append({arg:True for arg in args_set.keys()})

			if args_list_label == 'query':
				args_check = args
			elif args_list_label == 'doc':
				args_check = args.keys()

			for arg in args_set.keys():
				if arg not in args_check:
					set_status = False
					sets_check[set_check][arg] = 'missing'
				else:
					try:
						if args_list_label == 'query' and arg[0] != '$':
							for i in range(0, len(args[arg])):
								args[arg][i] = validate_attr(arg, args_set[arg], args[arg][i])
						elif args_list_label == 'query' and arg[0] == '$':
							args[arg] = validate_attr(arg, args_set[arg], args[arg])
						elif args_list_label == 'doc':
							args[arg] = validate_attr(arg, args_set[arg], args[arg])
					except InvalidAttrException:
						set_status = False
						sets_check[set_check][arg] = 'invalid'
					except ConvertAttrException:
						set_status = False
						sets_check[set_check][arg] = 'convert'
			
			if set_status:
				return True
		
		return sets_check

	async def __call__(self, skip_events=[], env={}, query=[], doc={}, call_id=None) -> DictObj:
		# [DEPRECATED] Return error for obsolete dict query
		if type(query) == dict:
			logger.debug('Detected obsolete dict query. Returning error: %s')
			return await self.return_results(ws=env['ws'], results=DictObj({
				'status':400,
				'msg':'Request was sent using obsolete Query structure. Upgrade your SDK.',
				'args':DictObj({'code':'CORE_REQ_OBSOLETE_QUERY'})
			}), call_id=call_id)

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
				logger.debug('Appended realm attrs to query, doc: %s, %s', JSONEncoder().encode(query), doc.keys())

		if Event.__PERM__ not in skip_events and env['session']:
			#logger.debug('checking permission, module: %s, permission: %s, sid:%s.', self.module, self.permissions, sid)
			permissions_check = self.module.modules['session'].check_permissions(env['session'], self.module, self.permissions)
			logger.debug('permissions_check: %s.', permissions_check)
			if permissions_check == False:
				return await self.return_results(ws=env['ws'], results=DictObj({
					'status':403,
					'msg':'You don\'t have permissions to access this endpoint.',
					'args':DictObj({'code':'CORE_SESSION_FORBIDDEN'})
				}), call_id=call_id)
			else:
				# [TODO] Implement NONE_VALUE handler
				if type(permissions_check['query']) == dict:
					permissions_check['query'] = [permissions_check['query']]
				for i in range(0, permissions_check['query'].__len__()):
					del_args = []
					for attr in permissions_check['query'][i].keys():
						# [DOC] Check for optional attr
						if type(permissions_check['query'][i][attr]) == dict and '__optional' in permissions_check['query'][i][attr].keys():
							# [TODO] Implement condition
							# [DOC] Flag attr for deletion if attr is present in query
							if attr in query or permissions_check['query'][i][attr]['__optional'] == None:
								del_args.append(attr)
							permissions_check['query'][i][attr] = permissions_check['query'][i][attr]['__optional']
						# [DOC] Flag attr for deletion if value is None
						if permissions_check['query'][i][attr] == None:
							del_args.append(attr)
					for attr in del_args:
						del permissions_check['query'][i][attr]
				# [DOC] Append query permissions args to query
				query.append(permissions_check['query'])

				del_args = []
				for attr in permissions_check['doc'].keys():
					# [DOC] Check for optional attr
					if type(permissions_check['doc'][attr]) == dict and '__optional' in permissions_check['doc'][attr].keys():
						# [TODO] Implement condition
						# [DOC] Flag attr for deletion if attr is present in doc
						if attr in doc.keys():
							del_args.append(attr)
						permissions_check['doc'][attr] = permissions_check['doc'][attr]['__optional']
					# [DOC] Replace None value with NONE_VALUE to bypass later validate step
					if permissions_check['doc'][attr] == None:
						permissions_check['doc'][attr] = NONE_VALUE
				for attr in del_args:
					del permissions_check['doc'][attr]
				# [DOC] Update doc with doc permissions args
				doc.update(permissions_check['doc'])
	
		if Event.__ARGS__ not in skip_events:
			if self.query_args:
				test_query = self.validate_args(query, 'query')
				if test_query != True:
					for i in range(0, len(test_query)):
						test_query[i] = '[' + ', '.join([f'\'{arg}\': {val.capitalize()}' for arg, val in test_query[i].items() if val != True]) + ']'
					return await self.return_results(ws=env['ws'], results=DictObj({
						'status':400,
						'msg':'Could not match query with any of the required query_args. Failed sets:' + ', '.join(test_query),
						'args':DictObj({'code':'{}_{}_INVALID_QUERY'.format(self.module.package_name.upper(), self.module.module_name.upper())})
					}), call_id=call_id)
			
			if self.doc_args:
				test_doc = self.validate_args(doc, 'doc')
				if test_doc != True:
					for i in range(0, len(test_doc)):
						test_doc[i] = '[' + ', '.join([f'\'{arg}\': {val.capitalize()}' for arg, val in test_doc[i].items() if val != True]) + ']'
					return await self.return_results(ws=env['ws'], results=DictObj({
						'status':400,
						'msg':'Could not match doc with any of the required doc_args. Failed sets:' + ', '.join(test_doc),
						'args':DictObj({'code':'{}_{}_INVALID_DOC'.format(self.module.package_name.upper(), self.module.module_name.upper())})
					}), call_id=call_id)

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
			# [DOC] Check for proxy module
			if self.module.proxy:
				if not getattr(self.module, '_method_{}'.format(self.method), None):
					method = getattr(self.module.modules[self.module.proxy], '_method_{}'.format(self.method))
				else:
					method = getattr(self.module, '_method_{}'.format(self.method))
			else:
				method = getattr(self.module, '_method_{}'.format(self.method))
			# [DOC] Call method function
			if self.watch_method:
				await env['ws'].send_str(JSONEncoder().encode({
					'status':200,
					'msg':'Created watch task.',
					'args':{'code':'CORE_WATCH_OK', 'watch':call_id, 'call_id':call_id}
				}))
				env['watch_tasks'][call_id] = {
					'stream':self.watch_loop(ws=env['ws'], stream=method(skip_events=skip_events, env=env, query=query, doc=doc), call_id=call_id)
				}
				env['watch_tasks'][call_id]['task'] = asyncio.create_task(env['watch_tasks'][call_id]['stream'])
				return
			else:
				results = await method(skip_events=skip_events, env=env, query=query, doc=doc)
				results = DictObj(results)
				try:
					results['args'] = DictObj(results.args)
				except Exception:
					results['args'] = DictObj({})
				
				logger.debug('Call results: %s', JSONEncoder().encode(results))
				# [DOC] Check for session in results
				if 'session' in results.args:
					if results.args.session._id == 'f00000000000000000000012':
						# [DOC] Updating session to __ANON
						env['session'] = None
					else:
						# [DOC] Updating session to user
						env['session'] = results.args.session
				
				return await self.return_results(ws=env['ws'], results=results, call_id=call_id)
			# query = Query([])
		except Exception as e:
			logger.error('An error occured. Details: %s.', traceback.format_exc())
			tb = sys.exc_info()[2]
			if tb is not None:
				prev = tb
				curr = tb.tb_next
				while curr is not None:
					prev = curr
					curr = curr.tb_next
				logger.error('Scope variables: %s', JSONEncoder().encode(prev.tb_frame.f_locals))
			query = Query([])
			if Config.debug:
				return await self.return_results(ws=env['ws'], results=DictObj({
					'status':500,
					'msg':'Unexpected error has occured [method:{}.{}] [{}].'.format(self.module.module_name, self.method, str(e)),
					'args':DictObj({'code':'CORE_SERVER_ERROR', 'method':'{}.{}'.format(self.module.module_name, self.method), 'err':str(e)})
				}), call_id=call_id)
			else:
				return await self.return_results(ws=env['ws'], results=DictObj({
					'status':500,
					'msg':'Unexpected error has occured.',
					'args':DictObj({'code':'CORE_SERVER_ERROR'})
				}), call_id=call_id)

	async def return_results(self, ws, results, call_id):
		if call_id:
			results.args['call_id'] = call_id
			await ws.send_str(JSONEncoder().encode(results))
			return
		else:
			return results

	async def watch_loop(self, ws, stream, call_id):
		logger.debug('Preparing async loop at BaseMethod')
		async for results in stream:
			logger.debug('Received watch results at BaseMethod: %s', results)
			results = DictObj(results)
			try:
				results['args'] = DictObj(results.args)
			except Exception:
				results['args'] = DictObj({})
			
			results.args['call_id'] = call_id
			await ws.send_str(JSONEncoder().encode(results))