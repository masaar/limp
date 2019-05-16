from bson import ObjectId

import logging, traceback, math, random, datetime, os, json
logger = logging.getLogger('limp')

class Test():
	
	@classmethod
	def run_test(self, modules, env, session):
		tests = {}
		from config import Config

		test_type, test_target = Config.test.split(':') #pylint: disable=no-member
		if test_type == 'unit':
			if test_target in Config.tests['unit'].keys():
				tests[test_target] = {}
				for call in Config.tests['unit'][test_target]['calls']:
					i = 1
					while True:
						if '{}#{}'.format(call['method'], i) in tests[test_target]:
							i += 1
						else:
							tests[test_target]['{}#{}'.format(call['method'], i)] = {
								'query':call['query'],
								'doc':call['doc']
							}
							break
					query = tests[test_target]['{}#{}'.format(call['method'], i)]['query']
					for attr in query.keys():
						if type(query[attr]) == dict and type(query[attr]['val']) == str and query[attr]['val'].startswith('$__'):
							query[attr]['val'] = self.extract_attrs(tests=tests, attr=query[attr]['val'])
					doc = tests[test_target]['{}#{}'.format(call['method'], i)]['doc']
					for attr in doc.keys():
						if type(doc[attr]) == str and doc[attr].startswith('$__'):
							doc[attr] = self.extract_attrs(tests=tests, attr=doc[attr])
						elif type(doc[attr]) == dict and '__attr' in doc[attr].keys():
							doc[attr] = self.generate_attr(doc[attr]['__attr'])
					try:
						results = modules[test_target].methods[call['method']](env=env, session=session, query=call['query'], doc=call['doc'])
						acceptance = True
						for measure in call['acceptance'].keys():
							if measure == 'status':
								if results.status != call['acceptance'][measure]:
									acceptance = False
									break
							elif measure == 'args.count':
								try:
									if results.args.count != call['acceptance'][measure]:
										acceptance = False
										break
								except:
									acceptance = False
									break
						if acceptance == False:
							tests[test_target]['{}#{}'.format(call['method'], i)] = {
								'status':False,
								'measure':measure,
								'query':call['query'],
								'doc':call['doc'],
								'results':results,
								'acceptance':call['acceptance']
							}
						else:
							tests[test_target]['{}#{}'.format(call['method'], i)] = {
								'status':True,
								'query':call['query'],
								'doc':call['doc'],
								'results':results,
								'acceptance':call['acceptance']
							}
					except Exception as e:
						tb = traceback.format_exc()
						tests[test_target]['{}#{}'.format(call['method'], i)] = {
							'status':False,
							'measure':False,
							'query':call['query'],
							'doc':call['doc'],
							'results':{
								'status':500,
								'msg':str(e),
								'args':{'tb':tb, 'code':'SERVER_ERROR'}
							},
							'acceptance':call['acceptance']
						}
		tests_count = 0
		modules_count = 0
		success_rate = 100
		for module in tests.keys():
			modules_count += 1
			for test in tests[module].keys():
				tests_count += 1
				if tests[module][test]['status']:
					test_rate = 100
				else:
					test_rate = 0
				success_rate = (((tests_count-1) * success_rate) + test_rate) / tests_count
		if int(success_rate) == 0:
			tests_status = 'FAILED'
		elif int(success_rate) == 100:
			tests_status = 'PASSED'
		else:
			tests_status = 'PARTIAL'
		logger.debug('Finished testing %s tests in %s modules with success rate of: %s%%', tests_count, modules_count, int(success_rate))
		__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
		tests_log = os.path.join(__location__, 'tests', '[{}] test-{}'.format(tests_status, datetime.date.today().strftime('%d-%b-%Y')))
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
			f.write(json.dumps(json.loads(JSONEncoder().encode(tests)), indent=4))
			logger.debug('Full tests log available at: %s', tests_log)
		exit()
	
	@classmethod
	def extract_attrs(self, tests, attr):
		attr = attr[3:].split('.')
		return tests[attr[0]][attr[1]][attr[2]][attr[3]]

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
			return {
				'name':'__name',
				'lastModified':100000,
				'type':'text/plain',
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
			return {locale:'__locale' for locale in Config.locales}
		elif attr_type == 'locales':
			from config import Config
			return Config.locale