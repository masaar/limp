from bson import ObjectId

import logging, traceback, math, random, datetime, os, json
logger = logging.getLogger('limp')

class Test():
	
	@classmethod
	def run_test(self, test_name, modules, env, session):
		from config import Config
		if test_name not in Config.tests.keys():
			logger.error('Specified test is not defined in loaded config.')
			exit()
		test = Config.tests[test_name]
		results = {
			'test':Config.tests[test_name],
			'status':'PASSED',
			'success_rate':100,
			'stats':{
				'passed':0,
				'failed':0,
				'skipped':0,
				'total':0
			},
			'steps':[]
		}
		step_failed = False
		for step in test:
			results['stats']['total'] += 1

			if step_failed and not Config.test_force:
				results['stats']['skipped'] += 1
				continue

			if step['step'] == 'call':
				logger.debug('Starting to test \'call\' step: %s', step)
				call_results = self.run_call(modules=modules, env=env, session=session, results=results, module=step['module'], method=step['method'], query=step['query'], doc=step['doc'], acceptance=step['acceptance'])
				results['steps'].append(call_results)
			elif step['step'] == 'test':
				logger.debug('Starting to test \'test\' step: %s', step)
				test_results = self.run_test(test_name=step['test'], modules=modules, env=env, session=session)
				if test_results['status'] == 'PASSED':
					test_results['status'] = True
				else:
					test_results['status'] = False
				results['steps'].append(test_results)
			elif step['step'] == 'auth':
				logger.debug('Starting to test \'auth\' step: %s', step)
				auth_results = self.run_auth(modules=modules, env=env, session=session, results=results, var=step['var'], val=step['val'], hash=step['hash'])
				if auth_results['status']:
					logger.debug('Changing session after successful auth step.')
					session = auth_results['results'].args.docs[0]
				results['steps'].append(auth_results)
			else:
				logger.error('Unknown step \'%s\'. Exiting.', step['step'])
				exit()
			
			if not results['steps'][-1]['status']:
				results['stats']['failed'] += 1
				if not Config.test_force:
					step_failed = True
			else:
				results['stats']['passed'] += 1

		if results['steps'].__len__() == 0:
			logger.debug('No steps tested. Exiting')
			exit()
		if test_name == Config.test:
			results['success_rate'] = int((results['stats']['passed'] / results['stats']['total']) * 100)
			if results['success_rate'] == 0:
				results['status'] = 'FAILED'
			elif results['success_rate'] == 100:
				results['status'] = 'PASSED'
			else:
				results['status'] = 'PARTIAL'
			logger.debug('Finished testing %s steps [Passed: %s, Failed: %s, Skipped: %s] with success rate of: %s%%', results['stats']['total'], results['stats']['passed'], results['stats']['failed'], results['stats']['skipped'], results['success_rate'])
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			tests_log = os.path.join(__location__, 'tests', 'LIMP-TEST_{}_{}'.format(test_name, datetime.date.today().strftime('%d-%b-%Y')))
			if os.path.exists('{}.json'.format(tests_log)):
				i = 1
				while True:
					if os.path.exists('{}.{}.json'.format(tests_log, i)):
						i += 1
					else:
						tests_log = '{}.{}'.format(tests_log, i)
						break
			tests_log += '.json'
			from utils import JSONEncoder
			with open(tests_log, 'w') as f:
				f.write(json.dumps(json.loads(JSONEncoder().encode(results)), indent=4))
				logger.debug('Full tests log available at: %s', tests_log)
		else:
			return results

	@classmethod
	def run_call(self, modules, env, session, results, module, method, query, doc, acceptance):
		call_results = {
			'step':'call',
			'module':module,
			'method':method,
			'query':query,
			'doc':doc,
			'acceptance':acceptance,
			'status':True
		}
		for attr in query.keys():
			if type(query[attr]) == dict and type(query[attr]['val']) == str and query[attr]['val'].startswith('$__'):
				query[attr]['val'] = self.extract_attr(results=results, attr_path=query[attr]['val'])
		for attr in doc.keys():
			if type(doc[attr]) == str and doc[attr].startswith('$__'):
				doc[attr] = self.extract_attr(results=results, attr_path=doc[attr])
			elif type(doc[attr]) == dict and '__attr' in doc[attr].keys():
				doc[attr] = self.generate_attr(doc[attr]['__attr'])
		try:
			results = modules[module].methods[method](env=env, session=session, query=query, doc=doc)
			for measure in acceptance.keys():
				# [TODO] Add handler for session.user measure
				if measure == 'status':
					if results.status != acceptance[measure]:
						call_results['status'] = False
						break
				elif measure == 'args.count':
					try:
						if results.args.count != acceptance[measure]:
							call_results['status'] = False
							break
					except:
						call_results['status'] = False
						break
			if call_results['status'] == False:
				call_results.update({
					'measure':measure,
					'results':results
				})
			else:
				call_results.update({
					'results':results
				})
		except Exception as e:
			tb = traceback.format_exc()
			call_results.update({
				'measure':measure,
				'results':{
					'status':500,
					'msg':str(e),
					'args':{'tb':tb, 'code':'SERVER_ERROR'}
				}
			})
		return call_results
	
	@classmethod
	def run_auth(self, modules, env, session, results, var, val, hash):
		if val.startswith('$__'):
			val = self.extract_attr(results, val)
		if hash.startswith('$__'):
			hash = self.extract_attr(results, hash)
		auth_results = {
			'step':'auth',
			'var':var,
			'val':val,
			'hash':hash,
			'status':True
		}
		try:
			results = modules['session'].methods['auth'](env={'REMOTE_ADDR':'127.0.0.1', 'HTTP_USER_AGENT':'LIMPd Test', **env}, session=session, doc={var:val, 'hash':hash})
			if results.status != 200:
				auth_results['status'] = False
			auth_results.update({'results':results})
		except Exception as e:
			tb = traceback.format_exc()
			auth_results.update({
				'results':{
					'status':500,
					'msg':str(e),
					'args':{'tb':tb, 'code':'SERVER_ERROR'}
				}
			})
		return auth_results
	
	@classmethod
	def extract_attr(self, results, attr_path):
		attr_path = attr_path[3:].split('.')
		attr = results
		for child_attr in attr_path:
			logger.debug('Attempting to extract %s from %s', child_attr, attr)
			if child_attr.startswith('steps:'):
				attr = attr['steps'][int(child_attr[6:])]
			elif child_attr.startswith('docs:'):
				attr = attr['docs'][int(child_attr[5:])]
			else:
				attr = attr[child_attr]
		return attr

	@classmethod
	def generate_doc(self, _id, attrs, doc={}):
		doc['_id'] = ObjectId(_id)
		for attr in attrs.keys():
			if attr in doc.keys():
				continue		
	
	@classmethod
	def generate_attr(self, attr_type):
		if attr_type == 'any':
			return '__any'
		elif attr_type == 'id':
			return ObjectId()
		elif attr_type == 'str':
			return '__str-{}'.format(math.ceil(random.random() * 100))
		elif attr_type == 'int':
			return math.ceil(random.random() * 100)
		elif type(attr_type) == tuple:
			return attr_type[0]
		elif attr_type == 'bool':
			return True
		elif attr_type == 'email':
			return 'some-{}@email.com'.format(math.ceil(random.random() * 1000))
		elif attr_type == 'phone':
			return '+97150{}'.format(math.ceil(random.random() * 100))
		elif attr_type == 'uri:web':
			return 'https://some.uri.com'
		elif attr_type == 'time':
			return datetime.datetime.today()
		elif attr_type == 'file':
			return [{
				'name':'__name',
				'lastModified':100000,
				'type':'text/plain',
				'size':6,
				'content':b'__file'
			}]
		elif attr_type == 'geo':
			return {
				'type':'Point',
				'coordinates':[math.ceil(random.random() * 100000)/1000, math.ceil(random.random() * 100000)/1000]
			}
		elif attr_type == 'privileges':
			return {}
		elif attr_type == 'attrs':
			return {}
		elif attr_type == 'access':
			return {
				'anon':True,
				'users':[],
				'groups':[]
			}
		elif type(attr_type) == list:
			return [self.generate_attr(attr_type[0])]
		elif attr_type == 'locale':
			from config import Config
			return {locale:'__locale' for locale in Config.locales}
		elif attr_type == 'locales':
			from config import Config
			return Config.locale