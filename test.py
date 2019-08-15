from bson import ObjectId

import logging, traceback, math, random, datetime, os, json, copy, pdb
logger = logging.getLogger('limp')

calc_opers = {
	'+':'__add__',
	'-':'__sub__',
	'*':'__mul__',
	'/':'__truediv__',
	'**':'__pow__'
}

class Test():
	
	@classmethod
	def run_test(self, test_name, steps, modules, env, session):
		from config import Config
		from utils import DictObj
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
			'steps':[],
			'session':session
		}

		for i in range(0, test.__len__()):
			if test[i]['step'] == 'auth':
				test[i] = {
					'step':'call',
					'module':'session',
					'method':'auth',
					'query':[],
					'doc':{
						test[i]['var']:test[i]['val'],
						'hash':test[i]['hash']
					},
					'acceptance':{
						'status':200
					}
				}
			elif test[i]['step'] == 'signout':
				test[i] = {
					'step':'call',
					'module':'session',
					'method':'signout',
					'query':[{'_id':'$__session'}],
					'doc':{},
					'acceptance':{
						'status':200
					}
				}

		step_failed = False
		for i in range(0, test.__len__()):
			results['stats']['total'] += 1
			step = copy.deepcopy(test[i])

			if steps and i not in steps:
				results['stats']['total'] -= 1
				results['stats']['skipped'] += 1
				continue

			if step_failed and not Config.test_force:
				results['stats']['skipped'] += 1
				continue

			if step['step'] == 'call':
				logger.debug('Starting to test \'call\' step: %s', step)
				call_results = self.run_call(modules=modules, env=env, session=results['session'], results=results, module=step['module'], method=step['method'], query=step['query'], doc=step['doc'], acceptance=step['acceptance'])
				
				if 'session' in call_results.keys():
					logger.debug('Updating session after detecting \'session\' in call results.')
					if str(call_results['session']._id) == 'f00000000000000000000012':
						results['session'] = DictObj({**Config.compile_anon_session(), 'user':DictObj(Config.compile_anon_user())})
					else:
						results['session'] = call_results['session']

				results['steps'].append(call_results)
			elif step['step'] == 'test':
				logger.debug('Starting to test \'test\' step: %s', step)
				if 'steps' in step.keys():
					test_steps = step['steps']
				else:
					test_steps = False
				test_results, results['session'] = self.run_test(test_name=step['test'], steps=test_steps, modules=modules, env=env, session=results['session'])
				if test_results['status'] == 'PASSED':
					test_results['status'] = True
				else:
					test_results['status'] = False
				results['steps'].append(test_results)
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
			logger.error('No steps tested. Exiting.')
			exit()
		results['success_rate'] = int((results['stats']['passed'] / results['stats']['total']) * 100)
		if results['success_rate'] == 0:
			results['status'] = 'FAILED'
		elif results['success_rate'] == 100:
			results['status'] = 'PASSED'
		else:
			results['status'] = 'PARTIAL'

		if test_name == Config.test:
			logger.debug('Finished testing %s steps [Passed: %s, Failed: %s, Skipped: %s] with success rate of: %s%%', results['stats']['total'], results['stats']['passed'], results['stats']['failed'], results['stats']['skipped'], results['success_rate'])
			__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
			tests_log = os.path.join(__location__, 'tests', 'LIMP-TEST_{}_{}'.format(test_name, datetime.datetime.utcnow().strftime('%d-%b-%Y')))
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
			return (results, results['session'])

	@classmethod
	def run_call(self, modules, env, session, results, module, method, query, doc, acceptance):
		from utils import Query, extract_attr
		call_results = {
			'step':'call',
			'module':module,
			'method':method,
			'query':query,
			'doc':doc,
			'status':True
		}
		query = Query(self.parse_obj(results=results, obj=query))
		doc = self.parse_obj(results=results, obj=doc)
		try:
			call_results['results'] = modules[module].methods[method](env=env, session=session, query=query, doc=doc)
			call_results['acceptance'] = self.parse_obj(results=results, obj=copy.deepcopy(acceptance))
			for measure in acceptance.keys():
				results_measure = extract_attr(scope=call_results['results'], attr_path='$__{}'.format(measure))
				if results_measure != call_results['acceptance'][measure]:
					call_results['status'] = False
					self.break_debugger()
					break
			if call_results['status'] == False:
				logger.debug('Test step \'call\' failed at measure \'%s\'. Required value is \'%s\', but test results is \'%s\'', measure, call_results['acceptance'][measure], results_measure)
				call_results['measure'] = measure
		except Exception as e:
			tb = traceback.format_exc()
			logger.error('Exception occured: %s', tb)
			self.break_debugger()
			call_results.update({
				'measure':measure,
				'results':{
					'status':500,
					'msg':str(e),
					'args':{'tb':tb, 'code':'SERVER_ERROR'}
				}
			})
			call_results['status'] = False
			call_results['measure'] = measure
		if call_results['status'] == True and 'session' in call_results['results'].args:
			call_results['session'] = call_results['results'].args.session
		return call_results
	
	@classmethod
	def parse_obj(self, results, obj):
		from utils import extract_attr
		if type(obj) == dict:
			obj_iter = obj.keys()
		elif type(obj) == list:
			obj_iter = range(0, obj.__len__())

		for i in obj_iter:
			if type(obj[i]) == dict:
				if '__attr' in obj[i].keys():
					obj[i] = self.generate_attr(attr_type=obj[i]['__attr'], **obj[i])
				elif '__join' in obj[i].keys():
					for ii in range(0, obj[i]['__join'].__len__()):
						# [DOC] Checking for any test variables, attr generators in join attrs
						if type(obj[i]['__join'][ii]) == str and obj[i]['__join'][ii].startswith('$__'):
							obj[i]['__join'][ii] = str(extract_attr(scope=results, attr_path=obj[i]['__join'][ii]))
						elif type(obj[i]['__join'][ii]) == dict and '__attr' in obj[i]['__join'][ii].keys():
							obj[i]['__join'][ii] = str(self.generate_attr(obj[i]['__join'][ii]['__attr'], **obj[i]['__join'][ii]))
					obj[i] = obj[i]['separator'].join(obj[i]['__join'])
				elif '__calc' in obj[i].keys():
					if obj[i]['__calc'][1] not in calc_opers.keys():
						logger.error('Unknown calc oper \'%s\'. Exiting.', obj[i]['__calc'][1])
						exit()
					# [DOC] Checking for test variables
					for ii in [0, 2]:
						if type(obj[i]['__calc'][ii]) == str and obj[i]['__calc'][ii].startswith('$__'):
							obj[i]['__calc'][ii] = extract_attr(scope=results, attr_path=obj[i]['__calc'][ii])
					# [DOC] Running calc oper
					obj[i] = getattr(obj[i]['__calc'][0], calc_opers[obj[i]['__calc'][1]])(obj[i]['__calc'][2])
				else:
					obj[i] = self.parse_obj(results=results, obj=obj[i])
			elif type(obj[i]) == list:
				if obj[i].__len__() and type(obj[i][0]) == dict and '__attr' in obj[i][0].keys():
					if 'count' not in obj[i][0].keys():
						obj[i][0]['count'] = 1
					obj[i] = [self.generate_attr(attr_type=obj[i][0]['__attr'], **obj[i][0]) for ii in range(0, obj[i][0]['count'])]
				else:
					obj[i] = self.parse_obj(results=results, obj=obj[i])
			elif type(obj[i]) == str and obj[i].startswith('$__'):
				obj[i] = extract_attr(scope=results, attr_path=obj[i])

		return obj
	
	@classmethod
	def generate_attr(self, attr_type, **attr_args):
		if attr_type == 'any':
			return '__any'
		elif attr_type == 'id':
			return ObjectId()
		elif attr_type == 'str':
			return '__str-{}'.format(math.ceil(random.random() * 10000))
		elif attr_type == 'int':
			if 'range' in attr_args.keys():
				attr_val = random.choice([i for i in range(*attr_args['range'])])
			else:
				attr_val = math.ceil(random.random() * 10000)
			return attr_val
		elif attr_type == 'float':
			if 'range' in attr_args.keys():
				attr_val = random.choice([i for i in range(*attr_args['range'])])
			else:
				attr_val = random.random() * 10000
			return attr_val
		elif type(attr_type) == tuple:
			attr_val = random.choice(attr_type)
			return attr_val
		elif attr_type == 'bool':
			attr_val = random.choice([True, False])
			return attr_val
		elif attr_type == 'email':
			return 'some-{}@email.com'.format(math.ceil(random.random() * 10000))
		elif attr_type == 'phone':
			return '+97150{}'.format(math.ceil(random.random() * 10000))
		elif attr_type == 'uri:web':
			return 'https://some.uri-{}.com'.format(math.ceil(random.random() * 10000))
		elif attr_type == 'datetime':
			attr_val = datetime.datetime.utcnow()
			if 'future' in attr_args.keys():
				if type(attr_args['future']) == int:
					seconds = attr_args['future']
				elif type(attr_args['future']) == list:
					seconds = random.randint(attr_args['future'][0], attr_args['future'][1])
				else:
					seconds = 0
				attr_val += datetime.timedelta(seconds=seconds)
			return attr_val.isoformat()
		elif attr_type == 'date':
			attr_val = datetime.datetime.utcnow()
			if 'future' in attr_args.keys():
				if type(attr_args['future']) == int:
					seconds = attr_args['future']
				elif type(attr_args['future']) == list:
					seconds = random.randint(attr_args['future'][0], attr_args['future'][1])
				else:
					seconds = 0
				attr_val += datetime.timedelta(seconds=seconds)
			return attr_val.isoformat().split('T')[0]
		elif attr_type == 'time':
			attr_val = datetime.datetime.utcnow()
			if 'future' in attr_args.keys():
				if type(attr_args['future']) == int:
					seconds = attr_args['future']
				elif type(attr_args['future']) == list:
					seconds = random.randint(attr_args['future'][0], attr_args['future'][1])
				else:
					seconds = 0
				attr_val += datetime.timedelta(seconds=seconds)
			return attr_val.isoformat().split('T')[1]
		elif attr_type == 'file':
			if 'extension' not in attr_args.keys():
				attr_args['extension'] = 'txt'
			file_name = '__file-{}.{}'.format(math.ceil(random.random() * 10000), attr_args['extension'])
			if 'type' not in attr_args.keys():
				attr_args['type'] = 'text/plain'
			return {
				'name':file_name,
				'lastModified':100000,
				'type':attr_args['type'],
				'size':6,
				'content':b'__file'
			}
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
			return {locale:'__locale-{}'.format(math.ceil(random.random() * 10000)) for locale in Config.locales}
		elif attr_type == 'locales':
			from config import Config
			return Config.locale
		
		raise Exception('Unkown generator attr \'{}\''.format(attr_type))
	
	@classmethod
	def break_debugger(self):
		from config import Config
		if Config.test_breakpoint:
			logger.debug('Creating a breakpoint to allow you to investigate step failure. Type \'c\' after finishing to continue.')
			logger.debug('All variables are available under \'locals()\' function.')
			breakpoint()