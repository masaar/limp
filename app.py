from typing import Dict, Any, Union, List

async def run_app(packages, port):
	from utils import JSONEncoder, DictObj, import_modules, signal_handler, parse_file_obj, validate_doc, InvalidAttrException, ConvertAttrException
	from base_module import BaseModule
	from enums import Event
	from config import Config
	from data import Data
	from test import Test

	from bson import ObjectId
	import aiohttp.web, asyncio, nest_asyncio, traceback, jwt, argparse, json, re, signal, urllib.parse, os, datetime, logging

	nest_asyncio.apply()

	signal.signal(signal.SIGINT, signal_handler)

	logger = logging.getLogger('limp')

	modules: Dict[str, BaseModule] = import_modules(packages=packages)
	# [DOC] If realm mode is not enabled drop realm module.
	if not Config.realm:
		del modules['realm']
	await Config.config_data(modules=modules)
	# [DOC] Populate get_routes, post_routes
	get_routes = []
	post_routes = []
	for module in modules.values():
		for method in module.methods.values():
			if method.get_method:
				for get_args_set in method.get_args:
					if get_args_set:
						get_args = f'/{{{"}/{".join(list(get_args_set.keys()))}}}'
					else:
						get_args = ''
					if Config.realm:
						get_routes.append(f'/{{realm}}/{module.module_name}/{method.method}{get_args}')
					else:
						get_routes.append(f'/{module.module_name}/{method.method}{get_args}')
			elif method.post_method:
				for post_args_set in method.post_args:
					if post_args_set:
						post_args = f'/{{{"}/{".join(list(post_args_set.keys()))}}}'
					else:
						post_args = ''
					if Config.realm:
						post_routes.append(f'/{{realm}}/{module.module_name}/{method.method}{post_args}')
					else:
						post_routes.append(f'/{module.module_name}/{method.method}{post_args}')

	logger.debug('Loaded modules: %s', {module:modules[module].attrs for module in modules.keys()})
	logger.debug('Config has attrs: %s', {k:str(v) for k,v in Config.__dict__.items() if not type(v) == classmethod and not k.startswith('_')})
	logger.debug('Generated get_routes: %s', get_routes)
	logger.debug('Generated post_routes: %s', post_routes)

	sessions: List[Dict[int, Any]] = []
	ip_quota: Dict[str, Dict[str, Union[int, datetime.datetime]]] = {}

	async def root_handler(request: aiohttp.web.Request):
		headers = [
			('Server', 'limpd'),
			('Powered-By', 'Masaar, https://masaar.com'),
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Methods', 'GET'),
			('Access-Control-Allow-Headers', 'Content-Type'),
			('Access-Control-Expose-Headers', 'Content-Disposition')
		]
		return aiohttp.web.Response(status=200, headers=headers, body=JSONEncoder().encode({'status':200, 'msg':'Welcome to LIMP!'}))

	async def http_handler(request: aiohttp.web.Request):
		headers = [
			('Server', 'limpd'),
			('Powered-By', 'Masaar, https://masaar.com'),
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Methods', 'GET,POST'),
			('Access-Control-Allow-Headers', 'Content-Type'),
			('Access-Control-Expose-Headers', 'Content-Disposition')
		]
		
		logger.debug('Received new %s request: %s', request.method, request.match_info)

		# [DOC] Check for IP quota
		if str(request.remote) not in ip_quota:
			ip_quota[str(request.remote)] = {
				'counter':Config.quota_ip_min,
				'last_check':datetime.datetime.utcnow()
			}
		else:
			if (datetime.datetime.utcnow() - ip_quota[str(request.remote)]['last_check']).seconds > 259:
				ip_quota[str(request.remote)]['last_check'] = datetime.datetime.utcnow()
				ip_quota[str(request.remote)]['counter'] = Config.quota_ip_min
			else:
				if ip_quota[str(request.remote)]['counter'] - 1 <= 0:
					logger.warning('Denying \'%s\' request from \'%s\' for hitting IP quota.', request.method, request.remote)
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(status=429, headers=headers, body=JSONEncoder().encode({
						'status':429,
						'msg':'You have hit calls quota from this IP.',
						'args':{
							'code':'CORE_REQ_IP_QUOTA_HIT'
						}
					}))
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
		if request.method == 'GET':
			args_sets = modules[module].methods[method].get_args
		elif request.method == 'POST':
			args_sets = modules[module].methods[method].post_args
		
		# [DOC] Attempt to validate query as doc
		for args_set in args_sets:
			if len(args_set.keys()) == len(args_set.keys()) and \
			sum(1 for arg in args_set.keys() if arg in args_set.keys()) == len(args_set.keys()):
				# [DOC] Check presence and validate all attrs in doc args
				try:
					validate_doc(request_args, args_set)
				except InvalidAttrException as e:
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(status=400, headers=headers, body=JSONEncoder().encode({
						'status':400,
						'msg':f'{str(e)} for \'{request.method}\' request on module \'{modules[module].package_name.upper()}_{module.upper()}\'.',
						'args':{'code':f'{modules[module].package_name.upper()}_{module.upper()}_INVALID_ATTR'}
					}).encode('utf-8'))
				except ConvertAttrException as e:
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(status=400, headers=headers, body=JSONEncoder().encode({
						'status':400,
						'msg':f'{str(e)} for \'{request.method}\' request on module \'{modules[module].package_name.upper()}_{module.upper()}\'.',
						'args':{'code':f'{modules[module].package_name.upper()}_{module.upper()}_CONVERT_INVALID_ATTR'}
					}).encode('utf-8'))
				break

		conn = Data.create_conn() #pylint: disable=no-value-for-parameter
		env = {
			'conn':conn,
			'REMOTE_ADDR':request.remote,
			'ws':None
		}
		try:
			env['HTTP_USER_AGENT'] = request.headers['user-agent']
		except:
			env['HTTP_USER_AGENT'] = ''
		if Config.realm:
			env['realm'] = request.url.parts[1].lower()
		
		if 'x-auth-bearer' in request.headers or 'x-auth-token' in request.headers:
			if 'x-auth-bearer' not in request.headers or 'x-auth-token' not in request.headers:
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				return aiohttp.web.Response(status=400, headers=headers, body=JSONEncoder().encode({
					'status':400,
					'msg':'One \'X-Auth\' headers was set but not the other.'
				}).encode('utf-8'))
			try:
				session_results = await modules['session'].read(skip_events=[Event.__PERM__], env=env, query=[{
					'user':request.headers['x-auth-bearer'],
					'token':request.headers['x-auth-token']
				}, {'$limit':1}])
			except:
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				if Config.debug:
					return aiohttp.web.Response(status=500, headers=headers, body=JSONEncoder().encode({
						'status':500,
						'msg':f'Unexpected error has occured [{str(e)}].',
						'args':{'code':'CORE_SERVER_ERROR', 'err':str(e)}
					}).encode('utf-8'))
				else:
					return aiohttp.web.Response(status=500, headers=headers, body=JSONEncoder().encode({
						'status':500,
						'msg':'Unexpected error has occured.',
						'args':{'code':'CORE_SERVER_ERROR'}
					}).encode('utf-8'))
			
			if not session_results.args.count:
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				return aiohttp.web.Response(status=403, headers=headers, body=JSONEncoder().encode({
					'status':403,
					'msg':'X-Auth headers could not be verified.',
					'args':{'code':'CORE_SESSION_INVALID_XAUTH'}
				}).encode('utf-8'))
			else:
				session = session_results.args.docs[0]
				session_results = await modules['session'].reauth(skip_events=[Event.__PERM__], env=env, query=[{
					'_id':session._id,
					'hash':jwt.encode({'token':session.token}, session.token).decode('utf-8').split('.')[1]
				}])
				if session_results.status != 200:
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(status=403, headers=headers, body=JSONEncoder().encode(session_results).encode('utf-8'))
				else:
					session = session_results.args.session
		else:
			anon_user = Config.compile_anon_user()
			anon_session = Config.compile_anon_session()
			anon_session['user'] = DictObj(anon_user)
			session = DictObj(anon_session)

		env['session'] = session

		if request.method == 'GET':
			doc = {}
		elif request.method == 'POST':
			try:
				doc = json.loads(await request.content.read())
			except:
				doc = {}

		results = await modules[module].methods[method](env=env, query=[request_args], doc=doc)

		logger.debug('Closing connection.')
		env['conn'].close()

		if 'return' not in results.args or results.args['return'] == 'json':
			if 'return' in results.args:
				del results.args['return']
			headers.append(('Content-Type', 'application/json; charset=utf-8'))
			if results.status == 404:
				return aiohttp.web.Response(status=results.status, headers=headers, body=JSONEncoder().encode({
					'status':404,
					'msg':'Requested content not found.'
				}).encode('utf-8'))
			else:
				return aiohttp.web.Response(status=results.status, headers=headers, body=JSONEncoder().encode(results))
		elif results.args['return'] == 'file':
			del results.args['return']
			expiry_time = datetime.datetime.utcnow() + datetime.timedelta(days=30)
			headers.append(('lastModified', str(results.args.docs[0].lastModified)))
			headers.append(('Content-Type', results.args.docs[0].type))
			headers.append(('Cache-Control', 'public, max-age=31536000'))
			headers.append(('Expires', expiry_time.strftime('%a, %d %b %Y %H:%M:%S GMT')))
			return aiohttp.web.Response(status=results.status, headers=headers, body=results.args.docs[0].content)
		elif results.args['return'] == 'msg':
			del results.args['return']
			headers.append(('Content-Type', 'application/json; charset=utf-8'))
			return aiohttp.web.Response(status=results.status, headers=headers, body=results.msg)

		headers.append(('Content-Type', 'application/json; charset=utf-8'))
		return aiohttp.web.Response(status=405, headers=headers, body=JSONEncoder().encode({'status':405, 'msg':'METHOD NOT ALLOWED'}))
	
	async def websocket_handler(request: aiohttp.web.Request):
		conn = Data.create_conn() #pylint: disable=no-value-for-parameter
		logger.debug('Websocket connection starting with client at \'%s\'', request.remote)
		ws = aiohttp.web.WebSocketResponse()
		await ws.prepare(request)

		env = {
			'id':len(sessions),
			'conn':conn,
			'REMOTE_ADDR':request.remote,
			'ws':ws,
			'session':None,
			'watch_tasks':{},
			'init':False,
			'last_call':datetime.datetime.utcnow(),
			'files':{},
			'quota':{
				'counter':Config.quota_anon_min,
				'last_check':datetime.datetime.utcnow()
			}
		}
		sessions.append(env)
		try:
			env['HTTP_USER_AGENT'] = request.headers['user-agent']
		except:
			env['HTTP_USER_AGENT'] = ''
		
		if Config.realm:
			env['realm'] = request.match_info['realm'].lower()

			realm_detected = False
			for realm in Config._realms.keys():
				if Config._realms[realm].name == env['realm']:
					realm_detected = True
					break
			if not realm_detected:
				await ws.send_str(JSONEncoder().encode({
					'status':1008,
					'msg':'Connection closed',
					'args':{'code':'CORE_CONN_CLOSED'}
				}))
				await ws.close()

		logger.debug('Websocket connection #\'%s\' ready with client at \'%s\'', env['id'], env['REMOTE_ADDR'])

		await ws.send_str(JSONEncoder().encode({
			'status':200,
			'msg':'Connection ready',
			'args':{'code':'CORE_CONN_READY'}
		}))

		async for msg in ws:
			if 'conn' not in env:
				await ws.close()
				break
			logger.debug('Received new message from session #\'%s\': %s', env['id'], msg.data[:256])
			if msg.type == aiohttp.WSMsgType.TEXT:
				logger.debug('ip_quota on session #\'%s\': %s', env['id'], ip_quota)
				logger.debug('session_quota: on session #\'%s\': %s', env['id'], env['quota'])
				# [DOC] Check for IP quota
				if str(request.remote) not in ip_quota:
					ip_quota[str(request.remote)] = {
						'counter':Config.quota_ip_min,
						'last_check':datetime.datetime.utcnow()
					}
				else:
					if (datetime.datetime.utcnow() - ip_quota[str(request.remote)]['last_check']).seconds > 59:
						ip_quota[str(request.remote)]['last_check'] = datetime.datetime.utcnow()
						ip_quota[str(request.remote)]['counter'] = Config.quota_ip_min
					else:
						if ip_quota[str(request.remote)]['counter'] - 1 <= 0:
							logger.warning('Denying Websocket request from \'%s\' for hitting IP quota.', request.remote)
							asyncio.create_task(handle_msg(env=env, modules=modules, msg=msg, decline_quota='ip'))
							continue
						else:
							ip_quota[str(request.remote)]['counter'] -= 1
				# [DOC] Check for session quota
				if (datetime.datetime.utcnow() - env['quota']['last_check']).seconds > 59:
					env['quota']['last_check'] = datetime.datetime.utcnow()
					env['quota']['counter'] = (Config.quota_anon_min-1) if not env['session'] or env['session'].token == Config.anon_token else (Config.quota_auth_min-1)
					asyncio.create_task(handle_msg(env=env, modules=modules, msg=msg))
				else:
					if env['quota']['counter'] - 1 <= 0:
						asyncio.create_task(handle_msg(env=env, modules=modules, msg=msg, decline_quota='session'))
						continue
					else:
						env['quota']['counter'] -= 1
						asyncio.create_task(handle_msg(env=env, modules=modules, msg=msg))

		if 'id' in env.keys():
			await close_session(env['id'])

		return ws
	
	async def handle_msg(env: Dict[str, Any], modules: Dict[str, BaseModule], msg: aiohttp.WSMessage, decline_quota: str=None):
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
				res = jwt.decode(res['token'], env['session'].token, algorithms=['HS256'])
			except Exception:
				await env['ws'].send_str(JSONEncoder().encode({
					'status':403,
					'msg':'Request token is not accepted.',
					'args':{
						'call_id':res['call_id'] if 'call_id' in res.keys() else None,
						'code':'CORE_REQ_INVALID_TOKEN'
					}
				}))
				if env['init'] == False:
					await env['ws'].close()
					return
				else:
					return
			
			# [DOC] Check if msg should be denied for quota hit
			if decline_quota == 'ip':
				await env['ws'].send_str(JSONEncoder().encode({
					'status':429,
					'msg':'You have hit calls quota from this IP.',
					'args':{
						'call_id':res['call_id'] if 'call_id' in res.keys() else None,
						'code':'CORE_REQ_IP_QUOTA_HIT'
					}
				}))
				return
			elif decline_quota == 'session':
				await env['ws'].send_str(JSONEncoder().encode({
					'status':429,
					'msg':'You have hit calls quota.',
					'args':{
						'call_id':res['call_id'] if 'call_id' in res.keys() else None,
						'code':'CORE_REQ_SESSION_QUOTA_HIT'
					}
				}))
				return
			
			logger.debug('Decoded request: %s', JSONEncoder().encode(res))

			if 'endpoint' not in res.keys():
				await env['ws'].send_str(JSONEncoder().encode({
					'status':400,
					'msg':'Request missing endpoint.',
					'args':{
						'call_id':res['call_id'] if 'call_id' in res.keys() else None,
						'code':'CORE_REQ_NO_ENDPOINT'
					}
				}))
				return
			
			if env['init'] == False:
				if res['endpoint'] != 'conn/verify':
					await env['ws'].send_str(JSONEncoder().encode({
						'status':1008,
						'msg':'Request token is not accepted.',
						'args':{
							'call_id':res['call_id'] if 'call_id' in res.keys() else None,
							'code':'CORE_REQ_NO_VERIFY'
						}
					}))
					await env['ws'].close()
					return
				else:
					env['init'] = True
					logger.debug('Connection on session #\'%s\' is verified.', env['id'])
					await env['ws'].send_str(JSONEncoder().encode({
						'status':200,
						'msg':'Connection establised',
						'args':{
							'call_id':res['call_id'] if 'call_id' in res.keys() else None,
							'code':'CORE_CONN_OK'
						}
					}))
					return
			
			if res['endpoint'] == 'conn/close':
				logger.debug('Received connection close instructions on session #\'%s\'.', env['id'])
				await env['ws'].close()
				return
			
			if res['endpoint'] == 'heart/beat':
				logger.debug('Received connection heartbeat on session #\'%s\'.', env['id'])
				await env['ws'].send_str(JSONEncoder().encode({
					'status':200,
					'msg':'Heartbeat received.',
					'args':{
						'call_id':res['call_id'] if 'call_id' in res.keys() else None,
						'code':'CORE_HEARTBEAT_OK'
					}
				}))
				return

			
			res['endpoint'] = res['endpoint'].lower()
			if res['endpoint'] in ['session/auth', 'session/reauth'] and str(env['session']._id) != 'f00000000000000000000012':
				await env['ws'].send_str(JSONEncoder().encode({
					'status':400,
					'msg':'You are already authed.',
					'args':{
						'call_id':res['call_id'] if 'call_id' in res.keys() else None,
						'code':'CORE_SESSION_ALREADY_AUTHED'
					}
				}))
				return
			elif res['endpoint'] == 'session/signout' and str(env['session']._id) == 'f00000000000000000000012':
				await env['ws'].send_str(JSONEncoder().encode({
					'status':400,
					'msg':'Singout is not allowed for \'__ANON\' user.',
					'args':{
						'call_id':res['call_id'] if 'call_id' in res.keys() else None,
						'code':'CORE_SESSION_ANON_SIGNOUT'
					}
				}))
				return

			if 'query' not in res.keys(): res['query'] = []
			if 'doc' not in res.keys(): res['doc'] = {}
			if 'call_id' not in res.keys(): res['call_id'] = ''

			request = {'call_id':res['call_id'], 'sid':res['sid'] or False, 'query':res['query'], 'doc':res['doc'], 'path':res['endpoint'].split('/')}

			if request['path'].__len__() != 2:
				await env['ws'].send_str(JSONEncoder().encode({
					'status':400,
					'msg':'Endpoint path is invalid.',
					'args':{
						'call_id':request['call_id'],
						'code':'CORE_REQ_INVALID_PATH'
					}
				}))
				return

			module = request['path'][0].lower()
			if module == 'file' and request['path'][1].lower() == 'upload':
				logger.debug('Received file chunk for %s, index %s, %s out of %s', request['doc']['attr'], request['doc']['index'], request['doc']['chunk'], request['doc']['total'])
				if request['doc']['attr'] not in env['files'].keys():
					# [DOC] File attr first file, prepare files dict.
					env['files'][request['doc']['attr']] = {}
				if request['doc']['chunk'] == 1:
					# [DOC] First Chunk received, prepare files dict to accept it.
					env['files'][request['doc']['attr']][request['doc']['index']] = request['doc']['file']
				else:
					# [DOC] Past-first chunk received, append more bytes to it.
					env['files'][request['doc']['attr']][request['doc']['index']]['content'] += ',' + request['doc']['file']['content']
				if request['doc']['chunk'] == request['doc']['total']:
					# [DOC] Last chunk received, convert file to bytes and update the client.
					await env['ws'].send_str(JSONEncoder().encode({'status':200, 'msg':'Last chunk accepted', 'args':{'call_id':request['call_id']}}))
				else:
					# [DOC] More chunks expeceted, update the client
					await env['ws'].send_str(JSONEncoder().encode({'status':200, 'msg':'Chunk accepted', 'args':{'call_id':request['call_id']}}))
				return
			
			if module == 'watch' and request['path'][1].lower() == 'delete':
				logger.debug('Received watch task delete request for: %s', request['query'][0]['watch'])
				try:
					if request['query'][0]['watch'] == '__all':
						for watch_task in env['watch_tasks'].values():
							watch_task['stream'].close()
							watch_task['task'].cancel()
						await env['ws'].send_str(JSONEncoder().encode({
							'status':200,
							'msg':'All watch tasks deleted.',
							'args':{
								'call_id':request['call_id'],
								'watch':list(env['watch_tasks'].keys())
							}
						}))
						env['watch_tasks'] = {}
					else:
						env['watch_tasks'][request['query'][0]['watch']]['stream'].close()
						env['watch_tasks'][request['query'][0]['watch']]['task'].cancel()
						await env['ws'].send_str(JSONEncoder().encode({
							'status':200,
							'msg':'Watch task deleted.',
							'args':{
								'call_id':request['call_id'],
								'watch':[request['query'][0]['watch']]
							}
						}))
						del env['watch_tasks'][request['query'][0]['watch']]
				except:
					await env['ws'].send_str(JSONEncoder().encode({'status':400, 'msg':'Watch is invalid.', 'args':{'call_id':request['call_id'], 'code':'CORE_WATCH_INVALID_WATCH'}}))
				return

			if module not in modules.keys():
				await env['ws'].send_str(JSONEncoder().encode({
					'status':400,
					'msg':'Endpoint module is invalid.',
					'args':{
						'call_id':request['call_id'],
						'code':'CORE_REQ_INVALID_MODULE'
					}
				}))
				return

			if request['path'][1].lower() not in modules[module].methods.keys():
				await env['ws'].send_str(JSONEncoder().encode({
					'status':400,
					'msg':'Endpoint method is invalid.',
					'args':{
						'call_id':request['call_id'],
						'code':'CORE_REQ_INVALID_METHOD'
					}
				}))
				return

			if modules[module].methods[request['path'][1].lower()].get_method:
				await env['ws'].send_str(JSONEncoder().encode({
					'status':400,
					'msg':'Endpoint method is a GET method.',
					'args':{
						'call_id':request['call_id'],
						'code':'CORE_REQ_GET_METHOD'
					}
				}))
				return

			if not request['sid']:
				request['sid'] = 'f00000000000000000000012'

			method = modules[module].methods[request['path'][1].lower()]
			query = request['query']
			doc = parse_file_obj(request['doc'], env['files'])
			asyncio.create_task(method(skip_events=[], env=env, query=query, doc=doc, call_id=request['call_id']))

		except Exception as e:
			logger.error('An error occured. Details: %s.', traceback.format_exc())
			if Config.debug:
				await env['ws'].send_str(JSONEncoder().encode({
					'status':500,
					'msg':f'Unexpected error has occured [{str(e)}].',
					'args':{'code':'CORE_SERVER_ERROR', 'err':str(e)}
				}))
			else:
				await env['ws'].send_str(JSONEncoder().encode({
					'status':500,
					'msg':'Unexpected error has occured.',
					'args':{'code':'CORE_SERVER_ERROR'}
				}))

	async def close_session(id):
		if sessions[id].keys():
			logger.debug('Cleaning up watch tasks before connection for session #\'%s\' close.', sessions[id]['id'])
			for watch_task in sessions[id]['watch_tasks'].values():
				try:
					await watch_task['stream'].close()
				except Exception as e: logger.error('stream close error: %s', e)
				try:
					watch_task['task'].cancel()
				except Exception as e: logger.error('task close error: %s',e)

			logger.debug('Closing data connection for session #\'%s\'', sessions[id]['id'])
			sessions[id]['conn'].close()

			logger.debug('Done closing data connection.')
			logger.debug('Websocket connection status: %s', not sessions[id]['ws'].closed)

			if not sessions[id]['ws'].closed:
				await sessions[id]['ws'].close()
			logger.debug('Websocket connection for session #\'%s\' closed.', id)

			sessions[id] = {}
		else:
			logger.debug('Skipped closing session #\'%s\'.', id)

	async def jobs_loop():
		while True:
			await asyncio.sleep(60)
			try:
				# [DOC] Connection Timeout Workflow
				logger.debug('Time to check for sessions!')
				logger.debug('Current sessions: %s', sessions)
				for i in range(0, len(sessions)):
					session = sessions[i]
					if 'last_call' not in session.keys():
						continue
					if datetime.datetime.utcnow() > (session['last_call'] + datetime.timedelta(seconds=Config.conn_timeout)):
						logger.debug('Session #\'%s\' with REMOTE_ADDR \'%s\' HTTP_USER_AGENT: \'%s\' is idle. Closing.', session['id'], session['REMOTE_ADDR'], session['HTTP_USER_AGENT'])
						await close_session(i)

				# [DOC] Calls Quota Workflow - Cleanup Sequence
				logger.debug('Time to check for IPs quotas!')
				del_ip_quota = []
				for ip in ip_quota.keys():
					if (datetime.datetime.utcnow() - ip_quota[ip]['last_check']).seconds > 59:
						logger.debug('IP \'%s\' with quota \'%s\' is idle. Cleaning-up.', ip, ip_quota[ip]['counter'])
						del_ip_quota.append(ip)
				for ip in del_ip_quota:
					del ip_quota[ip]
					
				# [DOC] Jobs Workflow
				current_time = datetime.datetime.utcnow().isoformat()[:16]
				logger.debug('Time to check for jobs!')
				for job in Config.jobs:
					logger.debug('Checking: %s', job)
					if 'disabled' in job.keys() and job['disabled']:
						logger.debug('-Job is disabled. Skipping..')
						continue
					# [DOC] Check if job is scheduled for current_time
					if current_time == job['next_time']:
						logger.debug('-Job is due, running!')
						# [DOC] Update job next_time
						job['next_time'] = datetime.datetime.fromtimestamp(job['schedule'].get_next(), datetime.timezone.utc).isoformat()[:16] # pylint: disable=no-member
						if job['type'] == 'job':
							logger.debug('-Type of job: job.')
							job['job'](modules=modules, env=Config._sys_env, session=Config._jobs_session)
						elif job['type'] == 'call':
							logger.debug('-Type of job: call.')
							if 'auth' in job.keys():
								logger.debug('-Detected job auth: %s', job['auth'])
								session_results = modules['session'].auth(env=Config._sys_env, query=[{
									job['auth']['var']:job['auth']['val'],
									'hash':job['auth']['hash']
								}])
								if session_results.status != 200:
									logger.warning('-Job auth failed. Skipping..')
									continue
								session = session_results.args.docs[0]
							else:
								session = Config._jobs_session
							job_resuls = modules[job['module']].methods[job['method']](env=Config._sys_env, session=session, query=job['query'], doc=job['doc'])
							results_accepted = True
							for measure in job['acceptance'].keys():
								if job_resuls[measure] != job['acceptance'][measure]:
									# [DOC] Job results are not accepted
									results_accepted = False
									break
							if not results_accepted:
								logger.warning('Job has failed: %s.', job)
								logger.warning('-Job results: %s.', job_resuls)
								if 'prevent_disable' not in job.keys() or job['prevent_disable'] != True:
									logger.warning('-Disabling job.')
									job['disabled'] = True
								else:
									logger.warning('-Detected job prevent_disable. Skipping disabling job..')
					else:
						logger.debug('-Not yet due.')
			except Exception:
				logger.error('An error occured. Details: %s.', traceback.format_exc())				
	
	async def web_loop():
		app = aiohttp.web.Application()
		app.router.add_route('GET', '/', root_handler)
		if Config.realm:
			app.router.add_route('*', '/ws/{realm}', websocket_handler)
		else:
			app.router.add_route('*', '/ws', websocket_handler)
		for route in get_routes:
			app.router.add_route('GET', route, http_handler)
		for route in post_routes:
			app.router.add_route('POST', route, http_handler)
		logger.info('Welcome to LIMPd.')
		await aiohttp.web.run_app(app, host='0.0.0.0', port=port)
	
	async def loop_gather():
		await asyncio.gather(jobs_loop(), web_loop())
	
	asyncio.run(loop_gather())