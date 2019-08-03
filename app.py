def run_app(packages, port):
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
	Config.config_data(modules=modules)
	# [DOC] Populate GET routes:
	routes = []
	for module in modules.values():
		for method in module.methods.values():
			if method.get_method:
				for get_args_set in method.get_args:
					if Config.realm:
						routes.append(f'/{{realm}}/{module.module_name}/{method.method}/{{{"}/{".join(list(get_args_set.keys()))}}}')
					else:
						routes.append(f'/{module.module_name}/{method.method}/{{{"}/{".join(list(get_args_set.keys()))}}}')

	logger.debug('Loaded modules: %s', {module:modules[module].attrs for module in modules.keys()})
	logger.debug('Config has attrs: %s', {k:str(v) for k,v in Config.__dict__.items() if not type(v) == classmethod and not k.startswith('_')})

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
			try:
				realm = request.match_info['realm'].lower()
				if realm not in Config._realms.keys():
					headers.append(('Content-Type', 'application/json; charset=utf-8'))
					return aiohttp.web.Response(status=400, headers=headers, body=JSONEncoder().encode({
						'status':400,
						'msg':'Unknown realm.',
						'args':{'code':'CORE_CONN_INVALID_REALM'}
					}).encode('utf-8'))
			except Exception:
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				return aiohttp.web.Response(status=400, headers=headers, body=JSONEncoder().encode({
					'status':400,
					'msg':'Realm mode is enabled. You have to access API via realm.',
					'args':{'code':'CORE_CONN_REALM'}
				}).encode('utf-8'))

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
		env = {'conn':conn}
		if Config.realm:
			env['realm'] = realm
		anon_user = Config.compile_anon_user()
		anon_session = Config.compile_anon_session()
		anon_session['user'] = DictObj(anon_user)
		session = DictObj(anon_session)

		results = modules[module].methods[method](skip_events=[Event.__PERM__], env=env, session=session, query=[get_args])

		if results.args['return'] == 'json':
			del results.args['return']
			headers.append(('Content-Type', 'application/json; charset=utf-8'))
			if results.status == 400:
				return aiohttp.web.Response(status=results.status, headers=headers, body=JSONEncoder().encode({
					'status':404,
					'msg':'Requested content not found.'
				}).encode('utf-8'))
			else:
				return aiohttp.web.Response(status=results.status, headers=headers, body=JSONEncoder().encode(results))
		elif results.args['return'] == 'file':
			del results.args['return']
			expiry_time = datetime.datetime.utcnow() + datetime.timedelta(days=30)
			headers.append(('Content-Type', results.args.type))
			headers.append(('Cache-Control', 'public, max-age=31536000'))
			headers.append(('Expires', expiry_time.strftime('%a, %d %b %Y %H:%M:%S GMT')))
			return aiohttp.web.Response(status=results.status, headers=headers, body=results.msg)
		elif results.args['return'] == 'msg':
			del results.args['return']
			headers.append(('Content-Type', 'application/json; charset=utf-8'))
			return aiohttp.web.Response(status=results.status, headers=headers, body=results.msg)

		headers.append(('Content-Type', 'application/json; charset=utf-8'))
		return aiohttp.web.Response(status=405, headers=headers, body=JSONEncoder().encode({'status':405, 'msg':'METHOD NOT ALLOWED'}))
	
	async def websocket_handler(request):
		files = {}
		conn = Data.create_conn() #pylint: disable=no-value-for-parameter
		try:
			env = {
				'conn':conn,
				'REMOTE_ADDR':request.remote,
				'HTTP_USER_AGENT':request.headers['User-Agent']
			}
		except:
			env = {
				'conn':conn,
				'REMOTE_ADDR':request.remote,
				'HTTP_USER_AGENT':''
			}
		logger.debug('Websocket connection starting with client at \'%s\'', env['REMOTE_ADDR'])
		ws = aiohttp.web.WebSocketResponse()
		await ws.prepare(request)
		logger.debug('Websocket connection ready with client at \'%s\'', env['REMOTE_ADDR'])

		if Config.realm:
			try:
				env['realm'] = request.match_info['realm'].lower()
				if env['realm'] not in Config._realms.keys():
					await ws.send_str(JSONEncoder().encode({
						'status':400,
						'msg':'Unknown realm.',
						'args':{'code':'CORE_CONN_INVALID_REALM'}
					}))
					return ws
			except Exception:
				await ws.send_str(JSONEncoder().encode({
					'status':400,
					'msg':'Realm mode is enabled. You have to access API via realm.',
					'args':{'code':'CORE_CONN_REALM'}
				}))
				return ws

		await ws.send_str(JSONEncoder().encode({
			'status':200,
			'msg':'Connection establised',
			'args':{'code':'CORE_CONN_OK'}
		}))

		async for msg in ws:
			logger.debug('Received new message from client at \'%s\': %s', env['REMOTE_ADDR'], msg.data[:256])
			if msg.type == aiohttp.WSMsgType.TEXT:
				try:
					try:
						session.token
					except Exception:
						anon_user = Config.compile_anon_user()
						anon_session = Config.compile_anon_session()
						anon_session['user'] = DictObj(anon_user)
						session = DictObj(anon_session)
					res = json.loads(msg.data)
					try:
						res = jwt.decode(res['token'], session.token, algorithms=['HS256'])
					except Exception:
						await ws.send_str(JSONEncoder().encode({'status':403, 'msg':'Request token is not accepted.', 'args':{
							'call_id':res['call_id'] if 'call_id' in res.keys() else None,
							'code':'CORE_REQ_INVALID_TOKEN'
						}}))
						continue

					if 'query' not in res.keys(): res['query'] = {}
					if 'doc' not in res.keys(): res['doc'] = {}
					if 'endpoint' not in res.keys(): res['endpoint'] = ''
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
					results = method(skip_events=[], env=env, session=session, query=query, doc=doc)

					logger.debug('Call results: %s', str(results)[:512])
					if results.status == 204:
						await ws.send_str(JSONEncoder().encode({
							'status':204,
							'args':{
								'call_id':request['call_id']
							}
						}))
					else:
						if '/'.join(request['path']) in ['session/auth', 'session/reauth'] and results.status == 200:
							session = results.args.docs[0]
						if '/'.join(request['path']) == 'session/signout' and results.status == 200:
							session = None
						results.args['call_id'] = request['call_id']
						await ws.send_str(JSONEncoder().encode(results))

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
		while True:
			await asyncio.sleep(60)
			try:
				current_time = datetime.datetime.utcnow().isoformat()[:16]
				logger.debug('Time to check for jobs!')
				logger.debug('Checking %s, %s', Config.jobs, current_time)
				for job in Config.jobs:
					# [DOC] Check if job is scheduled for current_time
					if current_time == job['next_time']:
						# [DOC] Update job next_time
						job['next_time'] = datetime.datetime.fromtimestamp(job['schedule'].get_next(), datetime.timezone.utc).isoformat()[:16]
						# Run the job
						logger.debug('Running job!')
						if job['type'] == 'job':
							print(job['job'](modules))
						elif job['type'] == 'call':
							pass
			except Exception as e:
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