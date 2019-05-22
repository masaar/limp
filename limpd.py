#!/usr/bin/python3

import aiohttp.web

from bson import ObjectId

from utils import JSONEncoder, DictObj, import_modules, signal_handler, parse_file_obj
from base_module import Event
from config import Config
from data import Data
from test import Test

import traceback, jwt, argparse, json, re, signal, urllib.parse, os, datetime

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, 'version.txt')) as f:
	__version__ = f.read()

parser = argparse.ArgumentParser()
parser.add_argument('--version', help='Show LIMP version and exit', action='version', version='LIMPd v{}'.format(__version__))
parser.add_argument('--install-deps', help='Install dependencies for LIMP and packages.', action='store_true')
parser.add_argument('--env', help='Choose specific env')
parser.add_argument('--debug', help='Enable debug mode', action='store_true')
parser.add_argument('--packages', help='List of packages separated by commas to be loaded')
parser.add_argument('-p', '--port', help='Set custom port [default 8081]')
parser.add_argument('--test', help='Run specified test.')
parser.add_argument('--test-flush', help='Flush previous test data collections', action='store_true')
parser.add_argument('--test-force', help='Force running all test steps even if one is failed', action='store_true')
args = parser.parse_args()

signal.signal(signal.SIGINT, signal_handler)

import logging
logger = logging.getLogger('limp')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s  [%(levelname)s]  %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# [DOC] Parse runtime args
if args.install_deps:
	logger.setLevel(logging.DEBUG)
	logger.debug('Detected install_deps flag.')
	import subprocess, sys, os.path
	logger.debug('Attempting to install dependencies of LIMP.')
	# subprocess.call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
	__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	dirs = [d for d in os.listdir(os.path.join(__location__, 'modules')) if os.path.isdir(os.path.join(__location__, 'modules', d))]
	for package in dirs:
		logger.debug('Checking package \'%s\' for \'requirements.txt\' file.', package)
		if os.path.exists(os.path.join(__location__, 'modules', package, 'requirements.txt')):
			logger.debug('File \'requirements.txt\' found! Attempting to install package dependencies.')
			subprocess.call([sys.executable, '-m', 'pip', 'install', '-r', os.path.join(__location__, 'modules', package, 'requirements.txt')])
	exit()
Config.test = args.test
Config.test_flush = args.test_flush
Config.test_force = args.test_force
env = args.env or os.getenv('ENV') or None
if args.debug or args.test:
	Config.debug = True
	logger.setLevel(logging.DEBUG)
packages = args.packages
if packages:
	packages = args.packages.split(',') + ['core']

modules = import_modules(env=env, packages=packages)
# [DOC] If realm mode is not enabled drop realm module.
if not Config.realm:
	del modules['realm']
Config.config_data(modules=modules)

logger.debug('Loaded modules: %s', {module:modules[module].attrs for module in modules.keys()})
logger.debug('Config has attrs: %s', Config.__dict__)

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
		except Exception:
			headers.append(('Content-Type', 'application/json; charset=utf-8'))
			return aiohttp.web.Response(status=200, headers=headers, body=JSONEncoder().encode({
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
		conn = Data.create_conn()
		env = {'conn':conn}
		if Config.realm:
			env['realm'] = realm
		session_results = modules['session'].methods['read'](skip_events=[Event.__PERM__], env=env, query={'_id':{'val':ObjectId('f00000000000000000000012')}})
		results = modules[module].methods[method](skip_events=[Event.__PERM__], env=env, session=session_results.args.docs[0], query={'_id':{'val':_id}, 'var':{'val':var}})
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
		elif results['status'] == 200:
			headers.append(('Content-Type', 'application/json; charset=utf-8'))
			return aiohttp.web.Response(status=200, headers=headers, body=results['msg'])

	headers.append(('Content-Type', 'application/json; charset=utf-8'))
	return aiohttp.web.Response(status=405, headers=headers, body=JSONEncoder().encode({'status':405, 'msg':'METHOD NOT ALLOWED'}))

async def websocket_handler(request):
	files = {}
	conn = Data.create_conn()
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
	logger.info('Websocket connection starting')
	ws = aiohttp.web.WebSocketResponse()
	await ws.prepare(request)
	logger.info('Websocket connection ready')

	if Config.realm:
		try:
			env['realm'] = request.match_info['realm'].lower()
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
		logger.info('Received new message: %s', msg.data[:256])
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
				# logger.debug('attempting to decode JWT: %s, %s', res['token'], session.token)
				try:
					res = jwt.decode(res['token'], session.token, algorithms=['HS256'])
				except Exception:
					await ws.send_str(JSONEncoder().encode({'status':403, 'msg':'Request token is not accepted.', 'args':{'call_id':res['call_id'], 'code':'CORE_REQ_INVALID_TOKEN'}}))
					continue

				# logger.debug('received: %s', res)
				if 'query' not in res.keys(): res['query'] = {}
				if 'doc' not in res.keys(): res['doc'] = {}
				if 'endpoint' not in res.keys(): res['endpoint'] = ''
				if 'call_id' not in res.keys(): res['call_id'] = ''

				request = {'call_id':res['call_id'], 'sid':res['sid'] or False, 'query':res['query'], 'doc':res['doc'], 'path':res['endpoint'].split('/')}
				# logger.debug('request: %s', request)

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
					# logger.debug('files: %s', {attr:{index:{'content_type':type()} for index in files[attr].keys()} for attr in files.keys()})
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

				logger.debug('files: %s', files)

				# logger.debug('call results: %s', results)

				if results['status'] == 291:
					byte_array = []
					for byte in results['msg']:
						byte_array.append(byte)
					results['msg'] = byte_array
					await ws.send_str(JSONEncoder().encode(results))
				else:
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
							# print('updated session!', self.session._attrs())
						results.args['call_id'] = request['call_id']
						await ws.send_str(JSONEncoder().encode(results))
						# return self.send(JSONEncoder().encode(results).encode('utf-8'))
				# await ws.send_str(msg.data + '/answer')
			except Exception:
				logger.error('Error occured: %s', traceback.format_exc())
				await ws.send_str(JSONEncoder().encode({
					'status':500,
					'msg':'Server Error',
					'args':{'code':'SERVER_ERROR'}
				}))

	logger.info('Websocket connection closed')
	return ws

if __name__ == '__main__':
	port = os.getenv('PORT') or 8081
	if args.port:
		try:
			port = int(args.port)
		except Exception as e:
			logger.warning('Port should be in integer format. Defaulting to %s.', port)
	app = aiohttp.web.Application()
	app.router.add_route('GET', '/', root_handler)
	app.router.add_route('GET', '/{module}/{method}/{_id}/{var}', http_handler)
	app.router.add_route('GET', '/{realm}/{module}/{method}/{_id}/{var}', http_handler)
	app.router.add_route('*', '/ws', websocket_handler)
	app.router.add_route('*', '/ws/{realm}', websocket_handler)
	aiohttp.web.run_app(app, host='0.0.0.0', port=port)
	logger.info('Welcome to LIMPd.')
	logger.info('Serving on {}...'.format(port))