from limp.enums import Event
from limp.classes import ATTR, JSONEncoder, Query, LIMP_QUERY, LIMP_DOC
from limp.utils import extract_attr, validate_attr

from bson import ObjectId
from typing import List, Dict, Union, Tuple, Literal, Any

import logging, traceback, datetime, os, json, copy

logger = logging.getLogger('test')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [TEST] [%(levelname)s]  %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.setLevel(logging.DEBUG)


class InvalidTestStepException(Exception):
	def __init__(self, *, msg: str):
		self.msg = msg

	def __str__(self):
		return self.msg


class TEST(list):
	pass


class STEP:
	_step: Literal['AUTH', 'SIGNOUT', 'CALL', 'TEST']
	_args: Dict[str, Any]

	def __init__(self, *, step: str, **kwargs: Dict[str, Any]):
		self._step = step
		self._args = kwargs

	@classmethod
	def AUTH(cls, *, var: str, val: str, hash: str):
		return STEP(step='AUTH', var=var, val=val, hash=hash)

	@classmethod
	def SIGNOUT(cls):
		return STEP(step='SIGNOUT')

	@classmethod
	def CALL(
		cls,
		*,
		module: str,
		method: str,
		skip_events: List[str] = None,
		query: LIMP_QUERY = None,
		doc: LIMP_DOC = None,
		acceptance: Dict[str, Any] = {'status': 200},
	):
		if not skip_events:
			skip_events = []
		if not query:
			query = []
		if not doc:
			doc = {}
		return STEP(
			step='CALL',
			module=module,
			method=method,
			skip_events=skip_events,
			query=query,
			doc=doc,
			acceptance=acceptance,
		)

	@classmethod
	def TEST(cls, *, test: str, steps: List[int] = None):
		return STEP(step='TEST', test=test, steps=steps)

	@classmethod
	def SET_REALM(cls, *, realm: str):
		return STEP(step='SET_REALM')

	@classmethod
	def validate_step(cls, *, step: 'STEP'):
		from .config import Config

		logger.debug(f'Attempting to validate test step: {step}')
		if step._step == 'AUTH':
			logger.debug(f'Validating test step \'AUTH\' with args: {step._args}')
			if step._args['var'] not in Config.user_auth_attrs:
				raise InvalidTestStepException(
					msg=f'Test step arg \'var\' is invalid. Found \'{step._args["var"]}\', but expecting one of: {Config.user_auth_attrs}.'
				)
			if step._args['val'].startswith('$__'):
				logger.debug(
					'Detected test step \'AUTH\' with Test Variable \'val\' arg. Skipping validating test arg \'val\'.'
				)
			else:
				try:
					validate_attr(
						attr_name='val',
						attr_type=Config.user_attrs[step._args['var']],
						attr_val=step._args['val'],
					)
				except InvalidTestStepException:
					raise InvalidTestStepException(
						msg=f'Test step arg \'val\' of type \'{type(step._args["val"])}\' is invalid with required type \'{Config.user_attrs[step._args["var"]]._type}\'.'
					)
		elif step._step == 'SIGNOUT':
			logger.debug('Skipping validating test step \'SIGNOUT\'.')
		elif step._step == 'CALL':
			logger.debug(f'Validating test step \'CALL\' with args: {step._args}')
			if step._args['module'] not in Config.modules.keys():
				raise InvalidTestStepException(
					msg=f'Test step arg \'module\' is invalid. Unknown LIMP module \'{step._args["module"]}\'.'
				)
			if (
				step._args['method']
				not in Config.modules[step._args['module']].methods.keys()
			):
				raise InvalidTestStepException(
					msg=f'Test step arg \'method\' is invalid. Unknown method \'{step._args["method"]}\'.'
				)
		elif step._step == 'TEST':
			logger.debug(f'Validating test step \'TEST\' with args: {step._args}')
			if step._args['test'] not in Config.tests.keys():
				raise InvalidTestStepException(
					msg=f'Test step arg \'test\' is invalid. Unknown test \'{step._args["test"]}\'.'
				)
			if step._args['steps'] != None and (
				type(step._args['steps']) != list
				or sum(step for step in step._args['steps'] if type(step) != int)
			):
				raise InvalidTestStepException(
					msg='Test step arg \'steps\' is invalid. Either value is not of type \'list\' or at least on item in the list is not of type \'int\'.'
				)
		else:
			raise InvalidTestStepException(
				msg=f'Unknown test step \'{step._step}\' with args: {step._args}.'
			)


class CALC:
	_opers: Dict[str, str] = {
		'+': '__add__',
		'-': '__sub__',
		'*': '__mul__',
		'/': '__truediv__',
		'**': '__pow__',
	}
	_oper: Literal['+', '-', '*', '/', '**']
	_attrs: List[Any]

	def __init__(self, *, oper: Literal['+', '-', '*', '/', '**'], attrs: List[Any]):
		self._oper = oper
		self._attrs = attrs

	def execute(self, *, scope: Dict[str, Any]):
		results = None
		for i in range(len(self._attrs)):
			# [DOC] Attempt to extract attr, execute oper
			if type(self._attrs[i]) == str and self._attrs[i].startswith('$__'):
				self._attrs[i] = extract_attr(scope=scope, attr_path=self._attrs[i])
			elif type(self._attrs[i]) in [CALC, CAST, JOIN]:
				self._attrs[i] = self._attrs[i].execute(scope=scope)
			# [DOC] Calculate results per _oper
			if i == 0:
				results = self._attrs[i]
			else:
				results = getattr((results if results else 0), self._opers[self._oper])(
					self._attrs[i]
				)
		return results


class CAST:
	_type: Literal['int', 'str']
	_attr: Any

	def __init__(self, *, type: Literal['int', 'float', 'str'], attr: Any):
		self._type = type
		self._attr = attr

	def execute(self, *, scope: Dict[str, Any]):
		# [DOC] Attempt to extract attr, execute oper
		if type(self._attr) == str and self._attr.startswith('$__'):
			self._attr = extract_attr(scope=scope, attr_path=self._attr)
		elif type(self._attr) in [CALC, CAST, JOIN]:
			self._attr = self._attr.execute(scope=scope)
		# [DOC] Casr per _type
		if self._type == 'int':
			return int(self._attr)
		elif self._type == 'float':
			return float(self._attr)
		elif self._type == 'str':
			return str(self._attr)


class JOIN:
	_separator: str
	_attrs: List[Any]

	def __init__(self, *, separator: str, attrs: List[Any]):
		self._separator = separator
		self._attrs = attrs

	def execute(self, *, scope: Dict[str, Any]):
		for i in range(len(self._attrs)):
			# [DOC] Attempt to extract attr, execute oper
			if type(self._attrs[i]) == str and self._attrs[i].startswith('$__'):
				self._attrs[i] = extract_attr(scope=scope, attr_path=self._attrs[i])
			elif type(self._attrs[i]) in [CALC, CAST, JOIN]:
				self._attrs[i] = self._attrs[i].execute(scope=scope)
		# [DOC] Join using _separator
		return self._separator.join(self._attrs)


class Test:
	session: 'BaseModule'
	env: Dict[str, Any]

	@classmethod
	async def run_test(
		cls, test_name: str, steps: List[STEP] = None
	) -> Union[None, Dict[str, Any]]:
		from .config import Config
		from .utils import DictObj

		if test_name not in Config.tests.keys():
			logger.error('Specified test is not defined in loaded config.')
			logger.debug(f'Loaded tests: {list(Config.tests.keys())}')
			exit(1)
		test: List[STEP] = Config.tests[test_name]
		results = {
			'test': Config.tests[test_name],
			'status': 'PASSED',
			'success_rate': 100,
			'stats': {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0},
			'steps': [],
		}

		step_failed = False
		for i in range(len(test)):
			results['stats']['total'] += 1
			step = copy.deepcopy(test[i])

			if steps and i not in steps:
				results['stats']['total'] -= 1
				results['stats']['skipped'] += 1
				continue

			if step_failed and not Config.test_force:
				results['stats']['skipped'] += 1
				continue

			if step._step == 'AUTH':
				try:
					STEP.validate_step(step=step)
					step = STEP.CALL(
						module='session',
						method='auth',
						doc={
							step._args['var']: step._args['val'],
							'hash': step._args['hash'],
						},
					)
				except InvalidTestStepException as e:
					logger.error(
						f'Can\'t process test step \'AUTH\' with error: {e} Exiting.'
					)
					exit(1)
			elif step._step == 'SIGNOUT':
				step = STEP.CALL(
					module='session', method='signout', query=[{'_id': '$__session'}]
				)
			else:
				try:
					STEP.validate_step(step=step)
				except InvalidTestStepException as e:
					logger.error(f'{e} Exiting.')
					exit(1)

			if step._step == 'CALL':
				call_results = await cls.run_call(results=results, **step._args)
				if 'session' in call_results.keys():
					logger.debug(
						'Updating session after detecting \'session\' in call results.'
					)
					if str(call_results['session']._id) == 'f00000000000000000000012':
						cls.session = DictObj(
							{
								**Config.compile_anon_session(),
								'user': DictObj(Config.compile_anon_user()),
							}
						)
					else:
						cls.session = call_results['session']
				results['steps'].append(call_results)

			elif step._step == 'TEST':
				test_results = await cls.run_test(
					test_name=step._args['test'], steps=step._args['steps']
				)
				if test_results['status'] == 'PASSED':
					test_results['status'] = True
				else:
					test_results['status'] = False
				results['steps'].append(test_results)

			elif step._step == 'SET_REALM':
				try:
					if step._args['realm'].startswith('$__'):
						step._args['realm'] = extract_attr(
							scope=results, attr_path=step._args['realm']
						)
					logger.debug(f'Updating realm to \'{step._args["realm"]}\'.')
					cls.env['realm'] = step._args['realm']
					results['steps'].append(
						{
							'step': 'set_realm',
							'realm': step._args['realm'],
							'status': True,
						}
					)
				except Exception as e:
					logger.error(e)
					results['steps'].append(
						{
							'step': 'set_realm',
							'realm': step._args['realm'],
							'status': False,
						}
					)

			if not results['steps'][-1]['status']:
				results['stats']['failed'] += 1
				if not Config.test_force:
					step_failed = True
			else:
				results['stats']['passed'] += 1

		if len(results['steps']) == 0:
			logger.error('No steps tested. Exiting.')
			exit(1)

		results['success_rate'] = int(
			(results['stats']['passed'] / results['stats']['total']) * 100
		)
		if results['success_rate'] == 0:
			results['status'] = 'FAILED'
		elif results['success_rate'] == 100:
			results['status'] = 'PASSED'
		else:
			results['status'] = 'PARTIAL'

		if test_name == Config.test:
			logger.debug(
				'Finished testing %s steps [Passed: %s, Failed: %s, Skipped: %s] with success rate of: %s%%',
				results['stats']['total'],
				results['stats']['passed'],
				results['stats']['failed'],
				results['stats']['skipped'],
				results['success_rate'],
			)
			tests_log = os.path.join(
				Config._app_path,
				'tests',
				f'LIMP-TEST_{test_name}_{datetime.datetime.utcnow().strftime("%d-%b-%Y")}',
			)
			if os.path.exists(f'{tests_log}.json'):
				i = 1
				while True:
					if os.path.exists(f'{tests_log}.{i}.json'):
						i += 1
					else:
						tests_log = f'{tests_log}.{i}'
						break
			tests_log += '.json'
			with open(tests_log, 'w') as f:
				f.write(json.dumps(json.loads(JSONEncoder().encode(results)), indent=4))
				logger.debug(f'Full tests log available at: {tests_log}')
			if results['success_rate'] == 100:
				exit(0)
			else:
				exit(1)
		else:
			return results

	@classmethod
	async def run_call(
		cls,
		results: Dict[str, Any],
		module: str,
		method: str,
		skip_events: List[Event],
		query: List[Any],
		doc: LIMP_DOC,
		acceptance: Dict[str, Any],
	):
		from .config import Config

		call_results = {
			'step': 'call',
			'module': module,
			'method': method,
			'query': query,
			'doc': doc,
			'status': True,
		}
		query = Query(cls.process_obj(results=results, obj=query))
		doc = cls.process_obj(results=results, obj=doc)
		try:
			call_results['results'] = await Config.modules[module].methods[method](
				skip_events=skip_events,
				env={**cls.env, 'session': cls.session},
				query=query,
				doc=doc,
				call_id='__TEST__',
			)
			call_results['acceptance'] = cls.process_obj(
				results=results,
				obj=copy.deepcopy(acceptance),
				call_results=call_results,
			)
			for measure in acceptance.keys():
				if measure.startswith('session.'):
					results_measure = extract_attr(
						scope=cls.session, attr_path=f'$__{measure.replace("session.", "")}'
					)
				else:
					results_measure = extract_attr(
						scope=call_results['results'], attr_path=f'$__{measure}'
					)
				if results_measure != call_results['acceptance'][measure]:
					call_results['status'] = False
					cls.break_debugger(locals(), call_results)
					break
			if call_results['status'] == False:
				logger.debug(
					f'Test step \'call\' failed at measure \'{measure}\'. Required value is \'{call_results["acceptance"][measure]}\', but test results is \'{results_measure}\''
				)
				call_results['measure'] = measure
		except Exception as e:
			tb = traceback.format_exc()
			logger.error(f'Exception occured: {tb}')
			cls.break_debugger(locals(), call_results)
			call_results.update(
				{
					'measure': measure,
					'results': {
						'status': 500,
						'msg': str(e),
						'args': {'tb': tb, 'code': 'SERVER_ERROR'},
					},
				}
			)
			call_results['status'] = False
			call_results['measure'] = measure
		if call_results['status'] == True and 'session' in call_results['results'].args:
			call_results['session'] = call_results['results'].args.session
		return call_results

	@classmethod
	def process_obj(
		cls,
		results: Dict[str, Any],
		obj: Union[Dict[str, Any], List[Any]],
		call_results: 'DictObj' = None,
	) -> Union[Dict[str, Any], List[Any]]:
		logger.debug(f'Attempting to process object: {obj}')
		from .utils import extract_attr, generate_attr

		if type(obj) == dict:
			obj_iter = obj.keys()
		elif type(obj) == list:
			obj_iter = range(len(obj))

		for j in obj_iter:
			if type(obj[j]) == ATTR:
				obj[j] = generate_attr(attr_type=obj[j])
			elif type(obj[j]) in [CALC, CAST, JOIN]:
				obj[j] = obj[j].execute(scope=results)
			elif type(obj[j]) == dict:
				obj[j] = cls.process_obj(
					results=results, obj=obj[j], call_results=call_results
				)
			elif type(obj[j]) == list:
				if (
					len(obj[j])
					and type(obj[j][0]) == dict
					and '__attr' in obj[j][0].keys()
				):
					if 'count' not in obj[j][0].keys():
						obj[j][0]['count'] = 1
					obj[j] = [
						generate_attr(attr_type=obj[j][0]['__attr'], **obj[j][0])
						for ii in range(obj[j][0]['count'])
					]
				else:
					obj[j] = cls.process_obj(
						results=results, obj=obj[j], call_results=call_results
					)
			elif type(obj[j]) == str and obj[j].startswith('$__'):
				if obj[j] == '$__session':
					obj[j] = cls.session
				elif obj[j].startswith('$__session.'):
					obj[j] = extract_attr(scope=cls.session, attr_path=obj[j].replace('session.', ''))
				else:
					obj[j] = extract_attr(scope=results, attr_path=obj[j])
			elif callable(obj[j]):
				obj[j] = obj[j](results=results, call_results=call_results)

		logger.debug(f'Processed object: {obj}')
		return obj

	@classmethod
	def break_debugger(
		cls, scope: Dict[str, Any], call_results: Dict[str, Any]
	) -> None:
		from .config import Config

		if Config.test_breakpoint:
			logger.debug(
				'Creating a breakpoint to allow you to investigate step failure. Type \'c\' after finishing to continue.'
			)
			logger.debug('All variables are available under \'scope\' dict.')
			if call_results:
				logger.debug(
					'Call test raised exception available under \'call_results\' dict'
				)
			breakpoint()
