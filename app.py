def run_app(packages, port):
	import aiohttp.web

	from bson import ObjectId

	from utils import JSONEncoder, DictObj, import_modules, signal_handler, parse_file_obj
	from base_module import Event
	from config import Config
	from data import Data
	from test import Test

	import traceback, jwt, argparse, json, re, signal, urllib.parse, os, datetime, logging

	signal.signal(signal.SIGINT, signal_handler)

	logger = logging.getLogger('limp')

	modules = import_modules(packages=packages)
	# [DOC] If realm mode is not enabled drop realm module.
	if not Config.realm:
		del modules['realm']
	Config.config_data(modules=modules)

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

		module = request.match_info['module'].lower()
		method = request.match_info['method'].lower()
		_id = request.match_info['_id']
		var = request.match_info['var']

		if module in modules.keys() and \
		method in modules[module].methods.keys() and \
		modules[module].methods[method].get_method:
			conn = Data.create_conn() #pylint: disable=no-value-for-parameter
			env = {'conn':conn}
			if Config.realm:
				env['realm'] = realm
			anon_user = Config.compile_anon_user()
			anon_session = Config.compile_anon_session()
			anon_session['user'] = DictObj(anon_user)
			session = DictObj(anon_session)
			results = modules[module].methods[method](skip_events=[Event.__PERM__], env=env, session=session, query=[[{'_id':_id, 'var':var}]])
			if results['status'] == 404:
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				return aiohttp.web.Response(status=200, headers=headers, body=JSONEncoder().encode({
					'status':404,
					'msg':'Requested content not found.'
				}).encode('utf-8'))
			elif results['status'] == 291:
				expiry_time = datetime.datetime.utcnow() + datetime.timedelta(days=30)
				headers.append(('Content-Type', results['args']['type']))
				headers.append(('Cache-Control', 'public, max-age=31536000'))
				headers.append(('Expires', expiry_time.strftime('%a, %d %b %Y %H:%M:%S GMT')))
				# headers.append(('Content-Disposition', 'attachment; filename={}'.format(results['args']['name'].encode('utf-8').decode('latin-1'))))
				return aiohttp.web.Response(status=200, headers=headers, body=results['msg'])
			elif results['status'] == 292:
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				results['status'] = results['args']['status']
				del results['args']['status']
				return aiohttp.web.Response(status=results['status'], headers=headers, body=JSONEncoder().encode(results))
			elif results['status'] == 200:
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				return aiohttp.web.Response(status=200, headers=headers, body=results['msg'])
			else:
				headers.append(('Content-Type', 'application/json; charset=utf-8'))
				return aiohttp.web.Response(status=results['status'], headers=headers, body=JSONEncoder().encode(results))

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
					if results['status'] == 204:
						await ws.send_str(JSONEncoder().encode({
							'status':204,
							'args':{
								'call_id':request['call_id']
							}
						}))
					else:
						if '/'.join(request['path']) in ['session/auth', 'session/reauth'] and results['status'] == 200:
							session = results.args.docs[0]
						if '/'.join(request['path']) == 'session/signout' and results['status'] == 200:
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

	app = aiohttp.web.Application()
	app.router.add_route('GET', '/', root_handler)
	app.router.add_route('GET', '/{module}/{method}/{_id}/{var}', http_handler)
	app.router.add_route('GET', '/{realm}/{module}/{method}/{_id}/{var}', http_handler)
	app.router.add_route('*', '/ws', websocket_handler)
	app.router.add_route('*', '/ws/{realm}', websocket_handler)
	logger.info('Welcome to LIMPd.')
	aiohttp.web.run_app(app, host='0.0.0.0', port=port)