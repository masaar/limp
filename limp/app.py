from typing import Dict, Any, Union, List


async def run_app():
	from limp.utils import (
		import_modules,
		SignalHandler,
		process_multipart,
		process_file_obj,
		validate_doc,
		InvalidAttrException,
		ConvertAttrException,
	)
	from limp.classes import JSONEncoder, DictObj, LIMP_ENV
	from limp.base_module import BaseModule
	from limp.enums import Event
	from limp.config import Config
	from limp.data import Data
	from limp.test import Test

	from bson import ObjectId
	from passlib.hash import pbkdf2_sha512

	import aiohttp.web, asyncio, nest_asyncio, traceback, jwt, argparse, json, re, signal, urllib.parse, os, datetime, logging

	nest_asyncio.apply()

	signal.signal(signal.SIGINT, SignalHandler.sigint_handler)

	logger = logging.getLogger('limp')

	# [DOC] Use import_modules to load and initialise modules
	import_modules()
	# [DOC] If realm mode is not enabled drop realm module.
	if not Config.realm:
		del Config.modules['realm']
	await Config.config_data()
	# [DOC] Populate get_routes, post_routes
	get_routes = []
	post_routes = []
	for module in Config.modules.values():
		for method in module.methods.values():
			if method.get_method:
				for get_args_set in method.query_args:
					if get_args_set:
						get_args = f'/{{{"}/{".join(list(get_args_set.keys()))}}}'
					else:
						get_args = ''
					if Config.realm:
						get_args = get_args.replace('/{realm}', '')
						get_routes.append(
							f'/{{realm}}/{module.module_name}/{method.method}{get_args}'
						)
					else:
						get_routes.append(
							f'/{module.module_name}/{method.method}{get_args}'
						)
			elif method.post_method:
				for post_args_set in method.query_args:
					if post_args_set:
						post_args = f'/{{{"}/{".join(list(post_args_set.keys()))}}}'
					else:
						post_args = ''
					if Config.realm:
						post_args = post_args.replace('/{realm}', '')
						post_routes.append(
							f'/{{realm}}/{module.module_name}/{method.method}{post_args}'
						)
					else:
						post_routes.append(
							f'/{module.module_name}/{method.method}{post_args}'
						)

	logger.debug(
		'Loaded modules: %s',
		{module: Config.modules[module].attrs for module in Config.modules.keys()},
	)
	logger.debug(
		'Config has attrs: %s',
		{
			k: str(v)
			for k, v in Config.__dict__.items()
			if not type(v) == classmethod and not k.startswith('_')
		},
	)
	logger.debug(f'Generated get_routes: {get_routes}')
	logger.debug(f'Generated post_routes: {post_routes}')

	sessions: List[Dict[int, Any]] = []
	ip_quota: Dict[str, Dict[str, Union[int, datetime.datetime]]] = {}

	async def not_found_handler(request):
		headers = [
			('Server', 'LIMPd'),
			('Powered-By', 'Masaar, https://masaar.com'),
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Methods', 'GET,POST'),
			('Access-Control-Allow-Headers', 'Content-Type'),
			('Access-Control-Expose-Headers', 'Content-Disposition'),
		]
		return aiohttp.web.Response(
			status=404,
			headers=headers,
			body=JSONEncoder().encode({'status': 404, 'msg': '404 NOT FOUND'}),
		)

	async def not_allowed_handler(request):
		headers = [
			('Server', 'limpd'),
			('Powered-By', 'Masaar, https://masaar.com'),
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Methods', '*'),
			('Access-Control-Allow-Headers', 'Content-Type'),
			('Access-Control-Expose-Headers', 'Content-Disposition'),
		]
		return aiohttp.web.Response(
			status=405,
			headers=headers,
			body=JSONEncoder().encode({'status': 405, 'msg': '404 NOT ALLOWED'}),
		)

	async def root_handler(request: aiohttp.web.Request):
		headers = [
			('Server', 'limpd'),
			('Powered-By', 'Masaar, https://masaar.com'),
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Methods', 'GET'),
			('Access-Control-Allow-Headers', 'Content-Type'),
			('Access-Control-Expose-Headers', 'Content-Disposition'),
		]
		return aiohttp.web.Response(
			status=200,
			headers=headers,
			body=JSONEncoder().encode(
				{
					'status': 200,
					'msg': f'Welcome to {Config._app_name}!',
					'args': {'version': Config._app_version, 'powered_by': 'LIMP'},
				}
			),
		)

	async def http_handler(request: aiohttp.web.Request):
		headers = [
			('Server', 'limpd'),
			('Powered-By', 'Masaar, https://masaar.com'),
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Methods', 'GET,POST,OPTIONS'),
			(
				'Access-Control-Allow-Headers',
				'Content-Type,X-Auth-Bearer,X-Auth-Token,X-Auth-App',
			),
			('Access-Control-Expose-Headers', 'Content-Disposition'),
		]

		logger.debug(f'Received new {request.method} request: {request.match_info}')

		if request.method == 'OPTIONS':
			return aiohttp.web.Response(
				status=200,
				headers=headers,
				body=JSONEncoder().encode(
					{'status': 200, 'msg': 'OPTIONS request is allowed.',}
				),
			)

		# [DOC] Check for IP quota
		if str(request.remote) not in ip_quota:
			ip_quota[str(request.remote)] = {
				'counter': Config.quota_ip_min,
				'last_check': datetime.datetime.utcnow(),
			}
		else:
			if (
				datetime.datetime.utcnow() - ip_quota[str(request.remote)]['last_check']
			).seconds > 259:
				ip_quota[str(request.remote)]['last_check'] = datetime.datetime.utcnow()
				ip_quota[str(request.remote)]['counter'] = Config.quota_ip_min
			else:
				if ip_quota[str(request.remote)]['counter'] - 1 <= 0:
					logger.warning(
						f'Denying \'{request.method}\' request from \'{request.remote}\' for hitting IP quota.'
					)
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(
						status=429,
						headers=headers,
						body=JSONEncoder().encode(
							{
								'status': 429,
								'msg': 'You have hit calls quota from this IP.',
								'args': {'code': 'CORE_REQ_IP_QUOTA_HIT'},
							}
						),
					)
				else:
					ip_quota[str(request.remote)]['counter'] -= 1

		if Config.realm:
			module = request.url.parts[2].lower()
			method = request.url.parts[3].lower()
		else:
			module = request.url.parts[1].lower()
			method = request.url.parts[2].lower()
		request_args = dict(request.match_info.items())

		# [DOC] Extract Args Sets based on request.method
		args_sets = Config.modules[module].methods[method].query_args

		# [DOC] Attempt to validate query as doc
		for args_set in args_sets:
			if len(args_set.keys()) == len(args_set.keys()) and sum(
				1 for arg in args_set.keys() if arg in args_set.keys()
			) == len(args_set.keys()):
				# [DOC] Check presence and validate all attrs in doc args
				try:
					await validate_doc(doc=request_args, attrs=args_set)
				except InvalidAttrException as e:
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(
						status=400,
						headers=headers,
						body=JSONEncoder()
						.encode(
							{
								'status': 400,
								'msg': f'{str(e)} for \'{request.method}\' request on module \'{Config.modules[module].package_name.upper()}_{module.upper()}\'.',
								'args': {
									'code': f'{Config.modules[module].package_name.upper()}_{module.upper()}_INVALID_ATTR'
								},
							}
						)
						.encode('utf-8'),
					)
				except ConvertAttrException as e:
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(
						status=400,
						headers=headers,
						body=JSONEncoder()
						.encode(
							{
								'status': 400,
								'msg': f'{str(e)} for \'{request.method}\' request on module \'{Config.modules[module].package_name.upper()}_{module.upper()}\'.',
								'args': {
									'code': f'{Config.modules[module].package_name.upper()}_{module.upper()}_CONVERT_INVALID_ATTR'
								},
							}
						)
						.encode('utf-8'),
					)
				break

		conn = Data.create_conn()
		env = {
			'conn': conn,
			'REMOTE_ADDR': request.remote,
			'ws': None,
			'client_app': '__public',
		}

		try:
			env['HTTP_USER_AGENT'] = request.headers['user-agent']
			env['HTTP_ORIGIN'] = request.headers['origin']
		except:
			env['HTTP_USER_AGENT'] = ''
		if Config.realm:
			env['realm'] = request.url.parts[1].lower()

		if 'X-Auth-Bearer' in request.headers or 'X-Auth-Token' in request.headers:
			logger.debug('Detected \'X-Auth\' header[s].')
			if (
				'X-Auth-Bearer' not in request.headers
				or 'X-Auth-Token' not in request.headers
				or 'X-Auth-App' not in request.headers
			):
				logger.debug('Denying request due to missing \'X-Auth\' header.')
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				return aiohttp.web.Response(
					status=400,
					headers=headers,
					body=JSONEncoder()
					.encode(
						{
							'status': 400,
							'msg': 'One \'X-Auth\' headers was set but not the other.',
						}
					)
					.encode('utf-8'),
				)
			if len(Config.client_apps.keys()) and (
				request.headers['X-Auth-App'] not in Config.client_apps.keys()
				or (
					Config.client_apps[request.headers['X-Auth-App']]['type'] == 'web'
					and env['HTTP_ORIGIN']
					not in Config.client_apps[request.headers['X-Auth-App']]['hosts']
				)
			):
				logger.debug('Denying request due to unauthorised client_app.')
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				return aiohttp.web.Response(
					status=403,
					headers=headers,
					body=JSONEncoder()
					.encode(
						{
							'status': 403,
							'msg': 'X-Auth headers could not be verified.',
							'args': {'code': 'CORE_SESSION_INVALID_XAUTH'},
						}
					)
					.encode('utf-8'),
				)
			try:
				session_results = await Config.modules['session'].read(
					skip_events=[Event.PERM],
					env=env,
					query=[{'_id': request.headers['X-Auth-Bearer'],}],
				)
			except:
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				if Config.debug:
					return aiohttp.web.Response(
						status=500,
						headers=headers,
						body=JSONEncoder()
						.encode(
							{
								'status': 500,
								'msg': f'Unexpected error has occurred [{str(e)}].',
								'args': {'code': 'CORE_SERVER_ERROR', 'err': str(e)},
							}
						)
						.encode('utf-8'),
					)
				else:
					return aiohttp.web.Response(
						status=500,
						headers=headers,
						body=JSONEncoder()
						.encode(
							{
								'status': 500,
								'msg': 'Unexpected error has occurred.',
								'args': {'code': 'CORE_SERVER_ERROR'},
							}
						)
						.encode('utf-8'),
					)

			if not session_results.args.count or not pbkdf2_sha512.verify(
				request.headers['X-Auth-Token'], session_results.args.docs[0].token_hash
			):
				logger.debug(
					'Denying request due to missing failed Call Authorisation.'
				)
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				return aiohttp.web.Response(
					status=403,
					headers=headers,
					body=JSONEncoder()
					.encode(
						{
							'status': 403,
							'msg': 'X-Auth headers could not be verified.',
							'args': {'code': 'CORE_SESSION_INVALID_XAUTH'},
						}
					)
					.encode('utf-8'),
				)
			else:
				session = session_results.args.docs[0]
				session_results = await Config.modules['session'].reauth(
					skip_events=[Event.PERM],
					env=env,
					query=[
						{
							'_id': request.headers['X-Auth-Bearer'],
							'token': request.headers['X-Auth-Token'],
						}
					],
				)
				logger.debug('Denying request due to fail to reauth.')
				if session_results.status != 200:
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(
						status=403,
						headers=headers,
						body=JSONEncoder().encode(session_results).encode('utf-8'),
					)
				else:
					session = session_results.args.session
		else:
			anon_user = Config.compile_anon_user()
			anon_session = Config.compile_anon_session()
			anon_session['user'] = DictObj(anon_user)
			session = DictObj(anon_session)

		env['session'] = session

		doc = await request.content.read()
		try:
			doc = json.loads(doc)
		except:
			try:
				multipart_boundary = request.headers['Content-Type'][
					request.headers['Content-Type'].index('=') + 1 :
				].encode('utf-8')
				doc = process_multipart(rfile=doc, boundary=multipart_boundary)
			except Exception as e:
				doc = {}

		results = await Config.modules[module].methods[method](
			env=env, query=[request_args], doc=doc
		)

		logger.debug('Closing connection.')
		env['conn'].close()

		if 'return' not in results.args or results.args['return'] == 'json':
			if 'return' in results.args:
				del results.args['return']
			headers.append(('Content-Type', 'application/json; charset=utf-8'))
			if results.status == 404:
				return aiohttp.web.Response(
					status=results.status,
					headers=headers,
					body=JSONEncoder()
					.encode({'status': 404, 'msg': 'Requested content not found.'})
					.encode('utf-8'),
				)
			else:
				return aiohttp.web.Response(
					status=results.status,
					headers=headers,
					body=JSONEncoder().encode(results),
				)
		elif results.args['return'] == 'file':
			del results.args['return']
			expiry_time = datetime.datetime.utcnow() + datetime.timedelta(days=30)
			headers.append(('lastModified', str(results.args.docs[0].lastModified)))
			headers.append(('Content-Type', results.args.docs[0].type))
			headers.append(('Cache-Control', 'public, max-age=31536000'))
			headers.append(
				('Expires', expiry_time.strftime('%a, %d %b %Y %H:%M:%S GMT'))
			)
			return aiohttp.web.Response(
				status=results.status,
				headers=headers,
				body=results.args.docs[0].content,
			)
		elif results.args['return'] == 'msg':
			del results.args['return']
			headers.append(('Content-Type', 'application/json; charset=utf-8'))
			return aiohttp.web.Response(
				status=results.status, headers=headers, body=results.msg
			)

		headers.append(('Content-Type', 'application/json; charset=utf-8'))
		return aiohttp.web.Response(
			status=405,
			headers=headers,
			body=JSONEncoder().encode({'status': 405, 'msg': 'METHOD NOT ALLOWED'}),
		)

	async def websocket_handler(request: aiohttp.web.Request):
		conn = Data.create_conn()
		logger.debug(
			f'Websocket connection starting with client at \'{request.remote}\''
		)
		ws = aiohttp.web.WebSocketResponse()
		await ws.prepare(request)

		env = {
			'id': len(sessions),
			'conn': conn,
			'REMOTE_ADDR': request.remote,
			'ws': ws,
			'session': None,
			'watch_tasks': {},
			'init': False,
			'last_call': datetime.datetime.utcnow(),
			'files': {},
			'quota': {
				'counter': Config.quota_anon_min,
				'last_check': datetime.datetime.utcnow(),
			},
		}
		sessions.append(env)
		try:
			env['HTTP_USER_AGENT'] = request.headers['user-agent']
			env['HTTP_ORIGIN'] = request.headers['origin']
		except:
			env['HTTP_USER_AGENT'] = ''
			env['HTTP_ORIGIN'] = ''

		if Config.realm:
			env['realm'] = request.match_info['realm'].lower()

			realm_detected = False
			for realm in Config._realms.keys():
				if Config._realms[realm].name == env['realm']:
					realm_detected = True
					break
			if not realm_detected:
				await ws.send_str(
					JSONEncoder().encode(
						{
							'status': 1008,
							'msg': 'Connection closed',
							'args': {'code': 'CORE_CONN_CLOSED'},
						}
					)
				)
				await ws.close()

		logger.debug(
			f'Websocket connection #\'{env["id"]}\' ready with client at \'{env["REMOTE_ADDR"]}\''
		)

		await ws.send_str(
			JSONEncoder().encode(
				{
					'status': 200,
					'msg': 'Connection ready',
					'args': {'code': 'CORE_CONN_READY'},
				}
			)
		)

		async for msg in ws:
			if 'conn' not in env:
				await ws.close()
				break
			logger.debug(
				f'Received new message from session #\'{env["id"]}\': {msg.data[:256]}'
			)
			if msg.type == aiohttp.WSMsgType.TEXT:
				logger.debug(f'ip_quota on session #\'{env["id"]}\': {ip_quota}')
				logger.debug(
					f'session_quota: on session #\'{env["id"]}\': {env["quota"]}'
				)
				# [DOC] Check for IP quota
				if str(request.remote) not in ip_quota:
					ip_quota[str(request.remote)] = {
						'counter': Config.quota_ip_min,
						'last_check': datetime.datetime.utcnow(),
					}
				else:
					if (
						datetime.datetime.utcnow()
						- ip_quota[str(request.remote)]['last_check']
					).seconds > 59:
						ip_quota[str(request.remote)][
							'last_check'
						] = datetime.datetime.utcnow()
						ip_quota[str(request.remote)]['counter'] = Config.quota_ip_min
					else:
						if ip_quota[str(request.remote)]['counter'] - 1 <= 0:
							logger.warning(
								f'Denying Websocket request from \'{request.remote}\' for hitting IP quota.'
							)
							asyncio.create_task(
								handle_msg(env=env, msg=msg, decline_quota='ip',)
							)
							continue
						else:
							ip_quota[str(request.remote)]['counter'] -= 1
				# [DOC] Check for session quota
				if (
					datetime.datetime.utcnow() - env['quota']['last_check']
				).seconds > 59:
					env['quota']['last_check'] = datetime.datetime.utcnow()
					env['quota']['counter'] = (
						(Config.quota_anon_min - 1)
						if not env['session']
						or env['session'].token == Config.anon_token
						else (Config.quota_auth_min - 1)
					)
					asyncio.create_task(handle_msg(env=env, msg=msg))
				else:
					if env['quota']['counter'] - 1 <= 0:
						asyncio.create_task(
							handle_msg(env=env, msg=msg, decline_quota='session',)
						)
						continue
					else:
						env['quota']['counter'] -= 1
						asyncio.create_task(handle_msg(env=env, msg=msg))

		if 'id' in env.keys():
			await close_session(env['id'])

		return ws

	async def handle_msg(
		env: LIMP_ENV, msg: aiohttp.WSMessage, decline_quota: str = None,
	):
		try:
			env['last_call'] = datetime.datetime.utcnow()
			try:
				env['session'].token
			except Exception:
				anon_user = Config.compile_anon_user()
				anon_session = Config.compile_anon_session()
				anon_session['user'] = DictObj(anon_user)
				env['session'] = DictObj(anon_session)
			res = json.loads(msg.data)
			try:
				res = jwt.decode(
					res['token'], env['session'].token, algorithms=['HS256']
				)
			except Exception:
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 403,
							'msg': 'Request token is not accepted.',
							'args': {
								'call_id': res['call_id']
								if 'call_id' in res.keys()
								else None,
								'code': 'CORE_REQ_INVALID_TOKEN',
							},
						}
					)
				)
				if env['init'] == False:
					await env['ws'].close()
					return
				else:
					return

			# [DOC] Check if msg should be denied for quota hit
			if decline_quota == 'ip':
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 429,
							'msg': 'You have hit calls quota from this IP.',
							'args': {
								'call_id': res['call_id']
								if 'call_id' in res.keys()
								else None,
								'code': 'CORE_REQ_IP_QUOTA_HIT',
							},
						}
					)
				)
				return
			elif decline_quota == 'session':
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 429,
							'msg': 'You have hit calls quota.',
							'args': {
								'call_id': res['call_id']
								if 'call_id' in res.keys()
								else None,
								'code': 'CORE_REQ_SESSION_QUOTA_HIT',
							},
						}
					)
				)
				return

			logger.debug(f'Decoded request: {JSONEncoder().encode(res)}')

			if 'endpoint' not in res.keys():
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 400,
							'msg': 'Request missing endpoint.',
							'args': {
								'call_id': res['call_id']
								if 'call_id' in res.keys()
								else None,
								'code': 'CORE_REQ_NO_ENDPOINT',
							},
						}
					)
				)
				return

			if env['init'] == False:
				if res['endpoint'] != 'conn/verify':
					await env['ws'].send_str(
						JSONEncoder().encode(
							{
								'status': 1008,
								'msg': 'Request token is not accepted.',
								'args': {
									'call_id': res['call_id']
									if 'call_id' in res.keys()
									else None,
									'code': 'CORE_REQ_NO_VERIFY',
								},
							}
						)
					)
					await env['ws'].close()
					return
				else:
					if len(Config.client_apps.keys()) and (
						'doc' not in res.keys()
						or 'app' not in res['doc'].keys()
						or res['doc']['app'] not in Config.client_apps.keys()
						or (
							Config.client_apps[res['doc']['app']]['type'] == 'web'
							and env['HTTP_ORIGIN']
							not in Config.client_apps[res['doc']['app']]['hosts']
						)
					):
						await env['ws'].send_str(
							JSONEncoder().encode(
								{
									'status': 1008,
									'msg': 'Request token is not accepted.',
									'args': {
										'call_id': res['call_id']
										if 'call_id' in res.keys()
										else None,
										'code': 'CORE_REQ_NO_VERIFY',
									},
								}
							)
						)
						await env['ws'].close()
						return
					else:
						env['init'] = True
						if not Config.client_apps:
							env['client_app'] = '__public'
						else:
							env['client_app'] = res['doc']['app']
						logger.debug(
							f'Connection on session #\'{env["id"]}\' is verified.'
						)
						if Config.analytics_events['app_conn_verified']:
							asyncio.create_task(
								Config.modules['analytic'].create(
									skip_events=[Event.PERM],
									env=env,
									doc={
										'event': 'CONN_VERIFIED',
										'subevent': env['client_app'],
										'args': {
											'REMOTE_ADDR': env['REMOTE_ADDR'],
											'HTTP_USER_AGENT': env['HTTP_USER_AGENT'],
										},
									},
								)
							)
						await env['ws'].send_str(
							JSONEncoder().encode(
								{
									'status': 200,
									'msg': 'Connection established',
									'args': {
										'call_id': res['call_id']
										if 'call_id' in res.keys()
										else None,
										'code': 'CORE_CONN_OK',
									},
								}
							)
						)
						return

			if res['endpoint'] == 'conn/close':
				logger.debug(
					f'Received connection close instructions on session #\'{env["id"]}\'.'
				)
				await env['ws'].close()
				return

			if res['endpoint'] == 'heart/beat':
				logger.debug(
					f'Received connection heartbeat on session #\'{env["id"]}\'.'
				)
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 200,
							'msg': 'Heartbeat received.',
							'args': {
								'call_id': res['call_id']
								if 'call_id' in res.keys()
								else None,
								'code': 'CORE_HEARTBEAT_OK',
							},
						}
					)
				)
				return

			res['endpoint'] = res['endpoint'].lower()
			if (
				res['endpoint'] in ['session/auth', 'session/reauth']
				and str(env['session']._id) != 'f00000000000000000000012'
			):
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 400,
							'msg': 'You are already authed.',
							'args': {
								'call_id': res['call_id']
								if 'call_id' in res.keys()
								else None,
								'code': 'CORE_SESSION_ALREADY_AUTHED',
							},
						}
					)
				)
				return
			elif (
				res['endpoint'] == 'session/signout'
				and str(env['session']._id) == 'f00000000000000000000012'
			):
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 400,
							'msg': 'Singout is not allowed for \'__ANON\' user.',
							'args': {
								'call_id': res['call_id']
								if 'call_id' in res.keys()
								else None,
								'code': 'CORE_SESSION_ANON_SIGNOUT',
							},
						}
					)
				)
				return

			if 'query' not in res.keys():
				res['query'] = []
			if 'doc' not in res.keys():
				res['doc'] = {}
			if 'call_id' not in res.keys():
				res['call_id'] = ''

			request = {
				'call_id': res['call_id'],
				'sid': res['sid'] or False,
				'query': res['query'],
				'doc': res['doc'],
				'path': res['endpoint'].split('/'),
			}

			if len(request['path']) != 2:
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 400,
							'msg': 'Endpoint path is invalid.',
							'args': {
								'call_id': request['call_id'],
								'code': 'CORE_REQ_INVALID_PATH',
							},
						}
					)
				)
				return

			module = request['path'][0].lower()

			if module == 'watch' and request['path'][1].lower() == 'delete':
				logger.debug(
					'Received watch task delete request for: %s',
					request['query'][0]['watch'],
				)
				try:
					if request['query'][0]['watch'] == '__all':
						for watch_task in env['watch_tasks'].values():
							watch_task['stream'].close()
							watch_task['task'].cancel()
						await env['ws'].send_str(
							JSONEncoder().encode(
								{
									'status': 200,
									'msg': 'All watch tasks deleted.',
									'args': {
										'call_id': request['call_id'],
										'watch': list(env['watch_tasks'].keys()),
									},
								}
							)
						)
						env['watch_tasks'] = {}
					else:
						env['watch_tasks'][request['query'][0]['watch']][
							'stream'
						].close()
						env['watch_tasks'][request['query'][0]['watch']][
							'task'
						].cancel()
						await env['ws'].send_str(
							JSONEncoder().encode(
								{
									'status': 200,
									'msg': 'Watch task deleted.',
									'args': {
										'call_id': request['call_id'],
										'watch': [request['query'][0]['watch']],
									},
								}
							)
						)
						del env['watch_tasks'][request['query'][0]['watch']]
				except:
					await env['ws'].send_str(
						JSONEncoder().encode(
							{
								'status': 400,
								'msg': 'Watch is invalid.',
								'args': {
									'call_id': request['call_id'],
									'code': 'CORE_WATCH_INVALID_WATCH',
								},
							}
						)
					)
				return

			if module not in Config.modules.keys():
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 400,
							'msg': 'Endpoint module is invalid.',
							'args': {
								'call_id': request['call_id'],
								'code': 'CORE_REQ_INVALID_MODULE',
							},
						}
					)
				)
				return

			if request['path'][1].lower() not in Config.modules[module].methods.keys():
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 400,
							'msg': 'Endpoint method is invalid.',
							'args': {
								'call_id': request['call_id'],
								'code': 'CORE_REQ_INVALID_METHOD',
							},
						}
					)
				)
				return

			if Config.modules[module].methods[request['path'][1].lower()].get_method:
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 400,
							'msg': 'Endpoint method is a GET method.',
							'args': {
								'call_id': request['call_id'],
								'code': 'CORE_REQ_GET_METHOD',
							},
						}
					)
				)
				return

			if not request['sid']:
				request['sid'] = 'f00000000000000000000012'

			method = Config.modules[module].methods[request['path'][1].lower()]
			query = request['query']
			doc = request['doc']
			await process_file_obj(doc=doc, modules=Config.modules, env=env)
			asyncio.create_task(
				method(
					skip_events=[],
					env=env,
					query=query,
					doc=doc,
					call_id=request['call_id'],
				)
			)

		except Exception as e:
			logger.error(f'An error occurred. Details: {traceback.format_exc()}.')
			if Config.debug:
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 500,
							'msg': f'Unexpected error has occurred [{str(e)}].',
							'args': {'code': 'CORE_SERVER_ERROR', 'err': str(e)},
						}
					)
				)
			else:
				await env['ws'].send_str(
					JSONEncoder().encode(
						{
							'status': 500,
							'msg': 'Unexpected error has occurred.',
							'args': {'code': 'CORE_SERVER_ERROR'},
						}
					)
				)

	async def close_session(id):
		if sessions[id].keys():
			logger.debug(
				f'Cleaning up watch tasks before connection for session #\'{sessions[id]["id"]}\' close.'
			)
			for watch_task in sessions[id]['watch_tasks'].values():
				try:
					await watch_task['stream'].close()
				except Exception as e:
					logger.error(f'stream close error: {e}')
				try:
					watch_task['task'].cancel()
				except Exception as e:
					logger.error(f'task close error: {e}')

			logger.debug(
				f'Closing data connection for session #\'{sessions[id]["id"]}\''
			)
			sessions[id]['conn'].close()

			logger.debug('Done closing data connection.')
			logger.debug(
				f'Websocket connection status: {not sessions[id]["ws"].closed}'
			)

			if not sessions[id]['ws'].closed:
				await sessions[id]['ws'].close()
			logger.debug(f'Websocket connection for session #\'{id}\' closed.')

			sessions[id] = {}
		else:
			logger.debug(f'Skipped closing session #\'{id}\'.')

	async def jobs_loop():
		while True:
			await asyncio.sleep(60)
			try:
				# [DOC] Connection Timeout Workflow
				logger.debug('Time to check for sessions!')
				logger.debug(f'Current sessions: {sessions}')
				for i in range(len(sessions)):
					session = sessions[i]
					if 'last_call' not in session.keys():
						continue
					if datetime.datetime.utcnow() > (
						session['last_call']
						+ datetime.timedelta(seconds=Config.conn_timeout)
					):
						logger.debug(
							f'Session #\'{session["id"]}\' with REMOTE_ADDR \'{session["REMOTE_ADDR"]}\' HTTP_USER_AGENT: \'{session["HTTP_USER_AGENT"]}\' is idle. Closing.'
						)
						await close_session(i)
			except Exception:
				logger.error(f'An error occurred. Details: {traceback.format_exc()}.')

			try:
				# [DOC] Calls Quota Workflow - Clean-up Sequence
				logger.debug('Time to check for IPs quotas!')
				del_ip_quota = []
				for ip in ip_quota.keys():
					if (
						datetime.datetime.utcnow() - ip_quota[ip]['last_check']
					).seconds > 59:
						logger.debug(
							f'IP \'{ip}\' with quota \'{ip_quota[ip]["counter"]}\' is idle. Cleaning-up.'
						)
						del_ip_quota.append(ip)
				for ip in del_ip_quota:
					del ip_quota[ip]
			except Exception:
				logger.error(f'An error occurred. Details: {traceback.format_exc()}.')

			try:
				# [DOC] Jobs Workflow
				current_time = datetime.datetime.utcnow().isoformat()[:16]
				logger.debug('Time to check for jobs!')
				for job in Config.jobs:
					logger.debug(f'Checking: {job}')
					if 'disabled' in job.keys() and job['disabled']:
						logger.debug('-Job is disabled. Skipping..')
						continue
					# [DOC] Check if job is scheduled for current_time
					if current_time == job['next_time']:
						logger.debug('-Job is due, running!')
						# [DOC] Update job next_time
						job['next_time'] = datetime.datetime.fromtimestamp(
							job['schedule'].get_next(), datetime.timezone.utc
						).isoformat()[:16]
						if job['type'] == 'job':
							logger.debug('-Type of job: job.')
							job['job'](
								env=Config._sys_env, session=Config._sys_env,
							)
						elif job['type'] == 'call':
							logger.debug('-Type of job: call.')
							if 'auth' in job.keys():
								logger.debug(f'-Detected job auth: {job["auth"]}')
								session_results = Config.modules['session'].auth(
									env=Config._sys_env,
									query=[
										{
											job['auth']['var']: job['auth']['val'],
											'hash': job['auth']['hash'],
										}
									],
								)
								if session_results.status != 200:
									logger.warning('-Job auth failed. Skipping..')
									continue
								session = session_results.args.docs[0]
							else:
								session = Config._sys_env
							job_results = Config.modules[job['module']].methods[
								job['method']
							](
								skip_events=job['skip_events'],
								env=Config._sys_env,
								query=job['query'],
								doc=job['doc'],
							)
							results_accepted = True
							for measure in job['acceptance'].keys():
								if job_results[measure] != job['acceptance'][measure]:
									# [DOC] Job results are not accepted
									results_accepted = False
									break
							if not results_accepted:
								logger.warning(f'Job has failed: {job}.')
								logger.warning(f'-Job results: {job_results}.')
								if (
									'prevent_disable' not in job.keys()
									or job['prevent_disable'] != True
								):
									logger.warning('-Disabling job.')
									job['disabled'] = True
								else:
									logger.warning(
										'-Detected job prevent_disable. Skipping disabling job..'
									)
					else:
						logger.debug('-Not yet due.')
			except Exception:
				logger.error(f'An error occurred. Details: {traceback.format_exc()}.')

			try:
				logger.debug('Time to check for files timeout!')
				files_results = await Config.modules['file'].delete(
					skip_events=[Event.PERM],
					env=Config._sys_env,
					query=[
						{
							'create_time': {
								'$lt': (
									datetime.datetime.utcnow()
									- datetime.timedelta(
										seconds=Config.file_upload_timeout
									)
								).isoformat()
							}
						}
					],
				)
				logger.debug('Files timeout results:')
				logger.debug(f'-status: {files_results.status}')
				logger.debug(f'-msg: {files_results.msg}')
				logger.debug(f'-args.docs: {files_results.args.docs}')
			except Exception:
				logger.error(f'An error occurred. Details: {traceback.format_exc()}.')

	def create_error_middleware(overrides):
		@aiohttp.web.middleware
		async def error_middleware(request, handler):
			try:
				response = await handler(request)
				override = overrides.get(response.status)
				if override:
					return await override(request)
				return response
			except aiohttp.web.HTTPException as ex:
				override = overrides.get(ex.status)
				if override:
					return await override(request)
				raise

		return error_middleware

	async def web_loop():
		app = aiohttp.web.Application()
		app.middlewares.append(
			create_error_middleware({404: not_found_handler, 405: not_allowed_handler,})
		)
		app.router.add_route('GET', '/', root_handler)
		if Config.realm:
			app.router.add_route('*', '/ws/{realm}', websocket_handler)
		else:
			app.router.add_route('*', '/ws', websocket_handler)
		for route in get_routes:
			app.router.add_route('GET', route, http_handler)
		for route in post_routes:
			app.router.add_route('POST', route, http_handler)
			app.router.add_route('OPTIONS', route, http_handler)
		logger.info('Welcome to LIMPd.')
		await aiohttp.web.run_app(app, host='0.0.0.0', port=Config.port)

	async def loop_gather():
		await asyncio.gather(jobs_loop(), web_loop())

	asyncio.run(loop_gather())
