from .utils import validate_attr, InvalidAttrException, ConvertAttrException
from .classes import (
	DictObj,
	BaseModel,
	Query,
	JSONEncoder,
	ATTR_MOD,
	LIMP_DOC,
	LIMP_QUERY,
	PERM,
)
from .enums import Event, LIMP_VALUES
from .config import Config

from asyncio import coroutine
from aiohttp.web import WebSocketResponse
from typing import List, Dict, Union, Any, Tuple, Set, AsyncGenerator

import logging, copy, traceback, sys, asyncio

logger = logging.getLogger('limp')


class BaseMethod:
	def __init__(
		self,
		module: 'BaseModule',
		method: str,
		permissions: List[PERM],
		query_args: List[Dict[str, Union[str, Tuple[Any], Set[str]]]],
		doc_args: List[Dict[str, Union[str, Tuple[Any], Set[str]]]],
		watch_method: bool,
		get_method: bool,
		post_method: bool,
	):
		self.module = module
		self.method = method
		self.permissions = permissions
		self.query_args = query_args
		self.doc_args = doc_args
		self.watch_method = watch_method
		self.get_method = get_method
		self.post_method = post_method

	def validate_args(self, args: Dict[str, Any], args_list: str):
		args_list_label = args_list
		args_list = getattr(self, f'{args_list}_args')

		sets_check = []

		for args_set in args_list:
			set_status = True
			set_check = len(sets_check)
			sets_check.append({arg: True for arg in args_set.keys()})

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
							for i in range(len(args[arg])):
								args[arg][i] = validate_attr(
									attr_name=arg,
									attr_type=args_set[arg],
									attr_val=args[arg][i],
								)
						elif args_list_label == 'query' and arg[0] == '$':
							args[arg] = validate_attr(
								attr_name=arg,
								attr_type=args_set[arg],
								attr_val=args[arg],
							)
						elif args_list_label == 'doc':
							args[arg] = validate_attr(
								attr_name=arg,
								attr_type=args_set[arg],
								attr_val=args[arg],
							)
					except InvalidAttrException:
						set_status = False
						sets_check[set_check][arg] = 'invalid'
					except ConvertAttrException:
						set_status = False
						sets_check[set_check][arg] = 'convert'

			if set_status:
				return True

		return sets_check

	async def __call__(
		self,
		*,
		skip_events: List[Event] = None,
		env: Dict[str, Any] = None,
		query: Union[LIMP_QUERY, Query] = None,
		doc: LIMP_DOC = None,
		call_id: str = None,
	) -> DictObj:
		if skip_events == None:
			skip_events = []
		if env == None:
			env = {}
		if query == None:
			query = []
		if doc == None:
			doc = {}
		# [DOC] Convert list query to Query object
		query = Query(copy.deepcopy(query))
		# [DOC] deepcopy() doc object ro prevent duplicate memory alloc
		doc = copy.deepcopy(doc)

		logger.debug(
			f'Calling: {self.module.module_name}.{self.method}, with skip_events:{skip_events}, query:{str(query)[:250]}, doc.keys:{doc.keys()}'
		)

		if call_id:
			for analytics_set in self.module.analytics:
				if analytics_set.condition(
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					method=self.method,
				):
					try:
						analytic_doc = analytics_set.doc(
							skip_events=skip_events,
							env=env,
							query=query,
							doc=doc,
							method=self.method,
						)
						analytic_results = await Config.modules['analytic'].create(
							skip_events=[Event.PERM], env=env, doc=analytic_doc
						)
					except Exception as e:
						logger.error(
							f'Failed to create \'Analytic\' doc: {analytic_doc}. Results: {analytic_results}'
						)
					if analytic_results.status != 200:
						logger.error(
							f'Failed to create \'Analytic\' doc: {analytic_doc}. Results: {analytic_results}'
						)

		if Event.ARGS not in skip_events and Config.realm:
			if self.module.module_name == 'realm':
				if self.method != 'create':
					query.append({'name': env['realm']})
					doc['name'] = env['realm']
					logger.debug(
						f'Appended realm name attrs to query, doc: {str(query)[:250]}, {doc.keys()}'
					)
				else:
					logger.debug(
						'Skipped Appending realm name attrs to query, doc for realm.create call'
					)
			else:
				query.append({'realm': env['realm']})
				doc['realm'] = env['realm']
				logger.debug(
					f'Appended realm attrs to query, doc: {JSONEncoder().encode(query)}, {doc.keys()}'
				)

		if Event.PERM not in skip_events and env['session']:
			permissions_check = Config.modules['session'].check_permissions(
				skip_events=skip_events,
				env=env,
				query=query,
				doc=doc,
				module=self.module,
				permissions=self.permissions,
			)
			logger.debug(f'permissions_check: {permissions_check}.')
			if permissions_check == False:
				return await self.return_results(
					ws=env['ws'],
					results=DictObj(
						{
							'status': 403,
							'msg': 'You don\'t have permissions to access this endpoint.',
							'args': DictObj({'code': 'CORE_SESSION_FORBIDDEN'}),
						}
					),
					call_id=call_id,
				)
			else:
				if type(permissions_check['query']) == dict:
					permissions_check['query'] = [permissions_check['query']]
				for i in range(len(permissions_check['query'])):
					del_args = []
					for attr in permissions_check['query'][i].keys():
						# [DOC] Flag attr for deletion if value is None
						if permissions_check['query'][i][attr] == None:
							del_args.append(attr)
					for attr in del_args:
						del permissions_check['query'][i][attr]
				# [DOC] Append query permissions args to query
				query.append(permissions_check['query'])

				del_args = []
				for attr in permissions_check['doc'].keys():
					# [DOC] Replace None value with NONE_VALUE to bypass later validate step
					if permissions_check['doc'][attr] == None:
						permissions_check['doc'][attr] = LIMP_VALUES.NONE_VALUE
				for attr in del_args:
					del permissions_check['doc'][attr]
				# [DOC] Update doc with doc permissions args
				doc.update(permissions_check['doc'])
				doc = {
					attr: doc[attr]
					for attr in doc.keys()
					if doc[attr] != LIMP_VALUES.NONE_VALUE
				}

		if Event.ARGS not in skip_events:
			if self.query_args:
				test_query = self.validate_args(query, 'query')
				if test_query != True:
					for i in range(len(test_query)):
						test_query[i] = (
							'['
							+ ', '.join(
								[
									f'\'{arg}\': {val.capitalize()}'
									for arg, val in test_query[i].items()
									if val != True
								]
							)
							+ ']'
						)
					return await self.return_results(
						ws=env['ws'],
						results=DictObj(
							{
								'status': 400,
								'msg': 'Could not match query with any of the required query_args. Failed sets:'
								+ ', '.join(test_query),
								'args': DictObj(
									{
										'code': f'{self.module.package_name.upper()}_{self.module.module_name.upper()}_INVALID_QUERY'
									}
								),
							}
						),
						call_id=call_id,
					)

			if self.doc_args:
				test_doc = self.validate_args(doc, 'doc')
				if test_doc != True:
					for i in range(len(test_doc)):
						test_doc[i] = (
							'['
							+ ', '.join(
								[
									f'\'{arg}\': {val.capitalize()}'
									for arg, val in test_doc[i].items()
									if val != True
								]
							)
							+ ']'
						)
					return await self.return_results(
						ws=env['ws'],
						results=DictObj(
							{
								'status': 400,
								'msg': 'Could not match doc with any of the required doc_args. Failed sets:'
								+ ', '.join(test_doc),
								'args': DictObj(
									{
										'code': f'{self.module.package_name.upper()}_{self.module.module_name.upper()}_INVALID_DOC'
									}
								),
							}
						),
						call_id=call_id,
					)

		for arg in doc.keys():
			if type(doc[arg]) == BaseModel:
				doc[arg] = doc[arg]._id

		# [DOC] check if $soft oper is set to add it to events
		if '$soft' in query and query['$soft'] == True:
			skip_events.append(Event.SOFT)
			del query['$soft']

		# [DOC] check if $extn oper is set to add it to events
		if '$extn' in query and query['$extn'] == False:
			skip_events.append(Event.EXTN)
			del query['$extn']

		try:
			# [DOC] Check for proxy module
			if self.module.proxy:
				if not getattr(self.module, f'_method_{self.method}', None):
					method = getattr(
						Config.modules[self.module.proxy], f'_method_{self.method}'
					)
				else:
					method = getattr(self.module, f'_method_{self.method}')
			else:
				method = getattr(self.module, f'_method_{self.method}')
			# [DOC] Call method function
			if self.watch_method:
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 200,
							'msg': 'Created watch task.',
							'args': {
								'code': 'CORE_WATCH_OK',
								'watch': call_id,
								'call_id': call_id,
							},
						}
					)
				)
				env['watch_tasks'][call_id] = {
					'watch': method(
						skip_events=skip_events, env=env, query=query, doc=doc
					)
				}
				env['watch_tasks'][call_id]['watch'] = self.watch_loop(
					ws=env['ws'],
					stream=env['watch_tasks'][call_id]['watch'],
					call_id=call_id,
					watch_task=env['watch_tasks'][call_id],
				)  # pylint: disable=assignment-from-no-return
				env['watch_tasks'][call_id]['task'] = asyncio.create_task(
					env['watch_tasks'][call_id]['watch']
				)
				return
			else:
				results = await method(
					skip_events=skip_events, env=env, query=query, doc=doc
				)
				if type(results) == coroutine:
					raise TypeError(
						'Method returned coroutine rather than acceptable results format.'
					)
				results = DictObj(results)
				try:
					results['args'] = DictObj(results.args)
				except Exception:
					results['args'] = DictObj({})

				logger.debug(f'Call results: {JSONEncoder().encode(results)}')
				# [DOC] Check for session in results
				if 'session' in results.args:
					if results.args.session._id == 'f00000000000000000000012':
						# [DOC] Updating session to __ANON
						env['session'] = None
					else:
						# [DOC] Updating session to user
						env['session'] = results.args.session

				return await self.return_results(
					ws=env['ws'], results=results, call_id=call_id
				)
			# query = Query([])
		except Exception as e:
			logger.error(f'An error occured. Details: {traceback.format_exc()}.')
			tb = sys.exc_info()[2]
			if tb is not None:
				prev = tb
				curr = tb.tb_next
				while curr is not None:
					prev = curr
					curr = curr.tb_next
				logger.error(f'Scope variables: {JSONEncoder().encode(prev.tb_frame.f_locals)}')
			query = Query([])
			if Config.debug:
				return await self.return_results(
					ws=env['ws'],
					results=DictObj(
						{
							'status': 500,
							'msg': f'Unexpected error has occured [method:{self.module.module_name}.{self.method}] [{str(e)}].',
							'args': DictObj(
								{
									'code': 'CORE_SERVER_ERROR',
									'method': f'{self.module.module_name}.{self.method}',
									'err': str(e),
								}
							),
						}
					),
					call_id=call_id,
				)
			else:
				return await self.return_results(
					ws=env['ws'],
					results=DictObj(
						{
							'status': 500,
							'msg': 'Unexpected error has occured.',
							'args': DictObj({'code': 'CORE_SERVER_ERROR'}),
						}
					),
					call_id=call_id,
				)

	async def return_results(
		self, ws: WebSocketResponse, results: DictObj, call_id: str
	) -> Union[None, DictObj]:
		if call_id and call_id != '__TEST__':
			results.args['call_id'] = call_id
			await ws.send_str(JSONEncoder().encode(results))
			return
		else:
			return results

	async def watch_loop(
		self,
		ws: WebSocketResponse,
		stream: AsyncGenerator,
		call_id: str,
		watch_task: Dict[str, Any],
	):
		logger.debug('Preparing async loop at BaseMethod')
		async for results in stream:
			logger.debug(f'Received watch results at BaseMethod: {results}')
			# [DOC] Update watch_task stream value with stream object
			if 'stream' in results.keys():
				watch_task['stream'] = results['stream']
				continue

			results = DictObj(results)
			try:
				results['args'] = DictObj(results.args)
			except Exception:
				results['args'] = DictObj({})

			results.args['call_id'] = call_id
			results.args['watch'] = call_id

			await ws.send_str(JSONEncoder().encode(results))

		logger.debug('Generator ended at BaseMethod.')
