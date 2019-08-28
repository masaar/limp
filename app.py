async def run_app(packages, port):
	from utils import JSONEncoder, DictObj, import_modules, signal_handler, parse_file_obj, validate_doc, InvalidAttrException, ConvertAttrException
	from base_module import Event
	from config import Config
	from data import Data
	from test import Test

	from bson import ObjectId
	import aiohttp.web, asyncio, nest_asyncio, traceback, jwt, argparse, json, re, signal, urllib.parse, os, datetime, logging

	nest_asyncio.apply()

	signal.signal(signal.SIGINT, signal_handler)

	logger = logging.getLogger('limp')

	modules = import_modules(packages=packages)
	# [DOC] If realm mode is not enabled drop realm module.
	if not Config.realm:
		del modules['realm']
	await Config.config_data(modules=modules)
	# [DOC] Populate GET routes:
	routes = []
	for module in modules.values():
		for method in module.methods.values():
			if method.get_method:
				for get_args_set in method.get_args:
					if get_args_set:
						get_args = f'/{{{"}/{".join(list(get_args_set.keys()))}}}'
					else:
						get_args = ''
					if Config.realm:
						routes.append(f'/{{realm}}/{module.module_name}/{method.method}{get_args}')
					else:
						routes.append(f'/{module.module_name}/{method.method}{get_args}')

	logger.debug('Loaded modules: %s', {module:modules[module].attrs for module in modules.keys()})
	logger.debug('Config has attrs: %s', {k:str(v) for k,v in Config.__dict__.items() if not type(v) == classmethod and not k.startswith('_')})
	logger.debug('Generated routes: %s', routes)

	async def root_handler(request):
		headers = [
			('Server', 'limpd'),
			('Powered-By', 'Masaar, https://masaar.com'),
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Methods', 'GET'),
			('Access-Control-Allow-Headers', 'Content-Type'),
			('Access-Control-Expose-Headers', 'Content-Disposition')
		]
		if Config.debug:
			return aiohttp.web.Response(status=200, headers=headers, body=JSONEncoder().encode({'status':200, 'msg':'Welcome to LIMP!'}))
		else:
			return aiohttp.web.Response(status=200, headers=headers, body=JSONEncoder().encode({'status':200, 'msg':'Welcome to LIMP!'}))

	async def http_handler(request):
		headers = [
			('Server', 'limpd'),
			('Powered-By', 'Masaar, https://masaar.com'),
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Methods', 'GET'),
			('Access-Control-Allow-Headers', 'Content-Type'),
			('Access-Control-Expose-Headers', 'Content-Disposition')
		]

		logger.debug('Received new GET request: %s', request.match_info)

		if Config.realm:
			module = request.url.parts[2].lower()
			method = request.url.parts[3].lower()
		else:
			module = request.url.parts[1].lower()
			method = request.url.parts[2].lower()
		get_args = dict(request.match_info.items())
		
		# [DOC] Attempt to validate query as doc
		for get_args_set in modules[module].methods[method].get_args:
			if len(get_args_set.keys()) == len(get_args.keys()) and \
			sum([1 if get_arg in get_args.keys() else 0 for get_arg in get_args_set.keys()]) == len(get_args_set.keys()):
				# [DOC] Check presence and validate all attrs in doc args
				try:
					validate_doc(get_args, get_args_set)
				except InvalidAttrException as e:
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(status=400, headers=headers, body=JSONEncoder().encode({
						'status':400,
						'msg':f'{str(e)} for \'GET\' request on module \'{modules[module].package_name.upper()}_{module.upper()}\'.',
						'args':{'code':f'{modules[module].package_name.upper()}_{module.upper()}_INVALID_ATTR'}
					}).encode('utf-8'))
				except ConvertAttrException as e:
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(status=400, headers=headers, body=JSONEncoder().encode({
						'status':400,
						'msg':f'{str(e)} for \'GET\' request on module \'{modules[module].package_name.upper()}_{module.upper()}\'.',
						'args':{'code':f'{modules[module].package_name.upper()}_{module.upper()}_CONVERT_INVALID_ATTR'}
					}).encode('utf-8'))
				break

		conn = Data.create_conn() #pylint: disable=no-value-for-parameter
		try:
			env = {
				'conn':conn,
				'REMOTE_ADDR':request.remote,
				'HTTP_USER_AGENT':request.headers['user-agent']
			}
		except:
			env = {
				'conn':conn,
				'REMOTE_ADDR':request.remote,
				'HTTP_USER_AGENT':''
			}
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
				session_results = modules['session'].read(skip_events=[Event.__PERM__], env=env, query=[{
					'user':request.headers['x-auth-bearer'],
					'token':request.headers['x-auth-token']
				}, {'$limit':1}])
			except:
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				if Config.debug:
					return aiohttp.web.Response(status=500, headers=headers, body=JSONEncoder().encode({
						'status':500,
						'msg':'Unexpected error has occured [{}].'.format(str(e)),
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
				session_results = modules['session'].reauth(skip_events=[Event.__PERM__], env=env, query=[{
					'_id':session._id,
					'hash':jwt.encode({'token':session.token}, session.token).decode('utf-8').split('.')[1]
				}])
				if session_results.status != 200:
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(status=403, headers=headers, body=JSONEncoder().encode(session_results).encode('utf-8'))
				else:
					session = session_results.args.docs[0]
		else:
			anon_user = Config.compile_anon_user()
			anon_session = Config.compile_anon_session()
			anon_session['user'] = DictObj(anon_user)
			session = DictObj(anon_session)

		env['session'] = session
		results = await modules[module].methods[method](env=env, query=[get_args])

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
	
	async def websocket_handler(request):
		files = {}
		conn = Data.create_conn() #pylint: disable=no-value-for-parameter
		logger.debug('Websocket connection starting with client at \'%s\'', request.remote)
		ws = aiohttp.web.WebSocketResponse()
		await ws.prepare(request)

		env = {
			'conn':conn,
			'REMOTE_ADDR':request.remote,
			'ws':ws,
			'session':None,
			'watch_tasks':{}
		}
		try:
			env['HTTP_USER_AGENT'] = request.headers['user-agent']
		except:
			env['HTTP_USER_AGENT'] = ''
		
		if Config.realm:
			env['realm'] = request.match_info['realm'].lower()

		await ws.send_str(JSONEncoder().encode({
			'status':200,
			'msg':'Connection establised',
			'args':{'code':'CORE_CONN_OK'}
		}))

		logger.debug('Websocket connection ready with client at \'%s\'', env['REMOTE_ADDR'])

		async for msg in ws:
			logger.debug('Received new message from client at \'%s\': %s', env['REMOTE_ADDR'], msg.data[:256])
			if msg.type == aiohttp.WSMsgType.TEXT:
				try:
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
						await ws.send_str(JSONEncoder().encode({'status':403, 'msg':'Request token is not accepted.', 'args':{
							'call_id':res['call_id'] if 'call_id' in res.keys() else None,
							'code':'CORE_REQ_INVALID_TOKEN'
						}}))
						continue

					if 'endpoint' not in res.keys():
						await ws.send_str(JSONEncoder().encode({'status':400, 'msg':'Request token is not accepted.', 'args':{
							'call_id':res['call_id'] if 'call_id' in res.keys() else None,
							'code':'CORE_REQ_NO_ENDPOINT'
						}}))
						continue
					
					res['endpoint'] = res['endpoint'].lower()
					if res['endpoint'] in ['session/auth', 'session/reauth'] and str(env['session']._id) != 'f00000000000000000000012':
						await ws.send_str(JSONEncoder().encode({'status':400, 'msg':'You are already authed.', 'args':{
							'call_id':res['call_id'] if 'call_id' in res.keys() else None,
							'code':'CORE_SESSION_ALREADY_AUTHED'
						}}))
						continue
					elif res['endpoint'] == 'session/signout' and str(env['session']._id) == 'f00000000000000000000012':
						await ws.send_str(JSONEncoder().encode({'status':400, 'msg':'Singout is not allowed for \'__ANON\' user.', 'args':{
							'call_id':res['call_id'] if 'call_id' in res.keys() else None,
							'code':'CORE_SESSION_ANON_SIGNOUT'
						}}))
						continue

					if 'query' not in res.keys(): res['query'] = []
					if 'doc' not in res.keys(): res['doc'] = {}
					if 'call_id' not in res.keys(): res['call_id'] = ''

					request = {'call_id':res['call_id'], 'sid':res['sid'] or False, 'query':res['query'], 'doc':res['doc'], 'path':res['endpoint'].split('/')}

					if request['path'].__len__() != 2:
						await ws.send_str(JSONEncoder().encode({'status':400, 'msg':'Endpoint path is invalid.', 'args':{'call_id':request['call_id'], 'code':'CORE_REQ_INVALID_PATH'}}))
						continue

					module = request['path'][0].lower()
					if module == 'file' and request['path'][1].lower() == 'upload':
						logger.debug('Received file chunk for %s, index %s, %s out of %s', request['doc']['attr'], request['doc']['index'], request['doc']['chunk'], request['doc']['total'])
						if request['doc']['attr'] not in files.keys():
							# [DOC] File attr first file, prepare files dict.
							files[request['doc']['attr']] = {}
						if request['doc']['chunk'] == 1:
							# [DOC] First Chunk received, prepare files dict to accept it.
							files[request['doc']['attr']][request['doc']['index']] = request['doc']['file']
						else:
							# [DOC] Past-first chunk received, append more bytes to it.
							files[request['doc']['attr']][request['doc']['index']]['content'] += ',' + request['doc']['file']['content']
						if request['doc']['chunk'] == request['doc']['total']:
							# [DOC] Last chunk received, convert file to bytes and update the client.
							await ws.send_str(JSONEncoder().encode({'status':200, 'msg':'Last chunk accepted', 'args':{'call_id':request['call_id']}}))
						else:
							# [DOC] More chunks expeceted, update the client
							await ws.send_str(JSONEncoder().encode({'status':200, 'msg':'Chunk accepted', 'args':{'call_id':request['call_id']}}))
						continue
					
					if module == 'watch' and request['path'][1].lower() == 'delete':
						logger.debug('Received watch task delete request for: %s', request['query'][0]['watch'])
						try:
							env['watch_tasks'][request['query'][0]['watch']].cancel()
							await ws.send_str(JSONEncoder().encode({'status':200, 'msg':'Watch task deleted.', 'args':{'call_id':request['call_id']}}))
						except:
							await ws.send_str(JSONEncoder().encode({'status':400, 'msg':'Watch is invalid.', 'args':{'call_id':request['call_id'], 'code':'CORE_WATCH_INVALID_WATCH'}}))
						continue

					if module not in modules.keys():
						await ws.send_str(JSONEncoder().encode({'status':400, 'msg':'Endpoint module is invalid.', 'args':{'call_id':request['call_id'], 'code':'CORE_REQ_INVALID_MODULE'}}))
						continue

					if request['path'][1].lower() not in modules[module].methods.keys():
						await ws.send_str(JSONEncoder().encode({'status':400, 'msg':'Endpoint method is invalid.', 'args':{'call_id':request['call_id'], 'code':'CORE_REQ_INVALID_METHOD'}}))
						continue

					if modules[module].methods[request['path'][1].lower()].get_method:
						await ws.send_str(JSONEncoder().encode({'status':400, 'msg':'Endpoint method is a GET method.', 'args':{'call_id':request['call_id'], 'code':'CORE_REQ_GET_METHOD'}}))
						continue

					if not request['sid']:
						request['sid'] = 'f00000000000000000000012'

					method = modules[module].methods[request['path'][1].lower()]
					query = request['query']
					doc = parse_file_obj(request['doc'], files)
					await method(skip_events=[], env=env, query=query, doc=doc, call_id=request['call_id'])

					# logger.debug('Call results: %s', str(results)[:512])
					# if results.status == 204:
					# 	await ws.send_str(JSONEncoder().encode({
					# 		'status':204,
					# 		'args':{
					# 			'call_id':request['call_id']
					# 		}
					# 	}))
					# else:
					# 	# [DOC] Check for session in results
					# 	if 'session' in results.args:
					# 		if results.args.session._id == 'f00000000000000000000012':
					# 			# [DOC] Updating session to __ANON
					# 			env['session'] = None
					# 		else:
					# 			# [DOC] Updating session to user
					# 			env['session'] = results.args.session
					# 	results.args['call_id'] = request['call_id']
					# 	await ws.send_str(JSONEncoder().encode(results))

				except Exception as e:
					logger.error('An error occured. Details: %s.', traceback.format_exc())
					if Config.debug:
						await ws.send_str(JSONEncoder().encode({
							'status':500,
							'msg':'Unexpected error has occured [{}].'.format(str(e)),
							'args':{'code':'CORE_SERVER_ERROR', 'err':str(e)}
						}))
					else:
						await ws.send_str(JSONEncoder().encode({
							'status':500,
							'msg':'Unexpected error has occured.',
							'args':{'code':'CORE_SERVER_ERROR'}
						}))

		logger.debug('Websocket connection closed with client at \'%s\'', env['REMOTE_ADDR'])
		return ws

	async def jobs_loop():
		if not Config.jobs:
			return
		while True:
			await asyncio.sleep(60)
			try:
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
		for route in routes:
			app.router.add_route('GET', route, http_handler)
		logger.info('Welcome to LIMPd.')
		await aiohttp.web.run_app(app, host='0.0.0.0', port=port)
	
	async def loop_gather():
		await asyncio.gather(jobs_loop(), web_loop())
	
	asyncio.run(loop_gather())