from classes import (
	LIMP_DOC,
	ATTR,
	ATTR_MOD,
	EXTN,
	DictObj,
	BaseModel,
	Query,
	LIMP_QUERY,
	L10N,
)
from enums import LIMP_VALUES

from typing import Dict, Union, Literal, List, Any
from bson import ObjectId, binary

import logging, pkgutil, inspect, re, datetime, time, math, random, copy

logger = logging.getLogger('limp')


def import_modules(*, packages=None):
	import modules as package
	from base_module import BaseModule
	from config import Config
	from test import TEST

	# [DOC] Assign required variables
	modules: Dict[str, BaseModule] = {}
	modules_packages: Dict[str, List[str]] = {}
	user_config = {'user_attrs': {}, 'user_auth_attrs': [], 'user_attrs_defaults': {}}

	# [DOC] Iterate over packages in modules folder
	package_prefix = package.__name__ + '.'
	for _, pkgname, _ in pkgutil.iter_modules(
		package.__path__, package_prefix
	):  # pylint: disable=unused-variable
		# [DOC] Check if package should be skipped
		if packages and pkgname.replace('modules.', '') not in packages:
			logger.debug(f'Skipping package: {pkgname}')
			continue
		logger.debug(f'Importing package: {pkgname}')

		# [DOC] Load package and attempt to load config
		child_package = __import__(pkgname, fromlist='*')
		for k, v in child_package.config().items():
			if k == 'packages_versions':
				Config.packages_versions[pkgname.replace('modules.', '')] = v
			elif k in ['tests', 'l10n']:
				logger.warning(
					f'Defining \'{k}\' in package config is not recommended. define your values in separate Python module with the name \'__{k}__\'. Refer to LIMP Docs for more.'
				)
			elif k == 'envs':
				if Config.env:
					if Config.env in v.keys():
						for kk, vv in v[Config.env].items():
							setattr(Config, kk, vv)
					else:
						logger.warning(
							f'Package \'{pkgname.replace("modules.", "")}\' has \'envs\' Config Attr defined, but \'env\' defintion \'{Config.env}\' not found.'
						)
			elif k in ['user_attrs', 'user_auth_attrs', 'user_attrs_defaults']:
				user_config[k] = v
				setattr(Config, k, v)
			elif type(v) == dict:
				if not getattr(Config, k):
					setattr(Config, k, {})
				getattr(Config, k).update(v)
			else:
				setattr(Config, k, v)

		# [DOC] Iterate over python modules in package
		child_prefix = child_package.__name__ + '.'
		for importer, modname, ispkg in pkgutil.iter_modules(
			child_package.__path__, child_prefix
		):
			# [DOC] Iterate over python classes in module
			module = __import__(modname, fromlist='*')
			if modname.endswith('__tests__'):
				for test_name in dir(module):
					if type(getattr(module, test_name)) == TEST:
						Config.tests[test_name] = getattr(module, test_name)
				continue
			elif modname.endswith('__l10n__'):
				for l10n_name in dir(module):
					if type(getattr(module, l10n_name)) == L10N:
						Config.l10n[l10n_name] = getattr(module, l10n_name)
				continue
			for clsname in dir(module):
				# [DOC] Confirm class is subclass of BaseModule
				if (
					clsname != 'BaseModule'
					and inspect.isclass(getattr(module, clsname))
					and issubclass(getattr(module, clsname), BaseModule)
				):
					# [DOC] Deny loading LIMPd-reserved named LIMP modules
					if clsname.lower() in ['conn', 'heart', 'file', 'watch']:
						logger.error(
							f'Module with LIMPd-reserved name \'{clsname.lower()}\' was found. Exiting.'
						)
						exit()
					# [DOC] Load LIMP module and assign module_name attr
					cls = getattr(module, clsname)
					module_name = re.sub(
						r'([A-Z])', r'_\1', clsname[0].lower() + clsname[1:]
					).lower()
					# [DOC] Deny duplicat LIMP modules names
					if module_name in modules.keys():
						logger.error(
							f'Duplicate module name \'{module_name}\'. Exiting.'
						)
						exit()
					# [DOC] Add module to loaded modules dict
					modules[module_name] = cls()
					if pkgname not in modules_packages.keys():
						modules_packages[pkgname] = []
					modules_packages[pkgname].append(module_name)
	# [DOC] Update User, Session modules with populated attrs
	modules['user'].attrs.update(user_config['user_attrs'])
	modules['user'].defaults['locale'] = Config.locale
	for attr in user_config['user_auth_attrs']:
		modules['user'].unique_attrs.append(attr)
		modules['user'].attrs[f'{attr}_hash'] = ATTR.STR()
		modules['session'].methods['auth']['doc_args'].append(
			{
				'hash': ATTR.STR(),
				attr: user_config['user_attrs'][attr],
				'groups': ATTR.LIST(list=[ATTR.ID()]),
			}
		)
		modules['session'].methods['auth']['doc_args'].append(
			{'hash': ATTR.STR(), attr: user_config['user_attrs'][attr]}
		)
	modules['user'].defaults.update(user_config['user_attrs_defaults'])
	# [DOC] Call update_modules, effectively finalise initlising modules
	Config.modules = modules
	for module in modules.values():
		module._initialise()
	# [DOC] Write api_ref if generate_ref mode
	if Config.generate_ref:
		generate_ref(modules_packages=modules_packages, modules=modules)


def extract_lambda_body(lambda_func):
	lambda_body = re.sub(
		r'^[a-z]+\s*=\s*lambda\s', '', inspect.getsource(lambda_func).strip()
	)
	if lambda_body.endswith(','):
		lambda_body = lambda_body[:-1]
	return lambda_body


def generate_ref(
	*, modules_packages: Dict[str, List[str]], modules: List['BaseModule']
):
	from config import Config
	from base_module import BaseModule

	modules: List[BaseModule]
	# [DOC] Initialise _api_ref Config Attr
	Config._api_ref = '# API Reference\n- - -\n'
	# [DOC] Iterate over packages in ascending order
	for package in sorted(modules_packages.keys()):
		# [DOC] Add package header
		Config._api_ref += f'## Package: {package.replace("modules.", "")}\n'
		# [DOC] Iterate over package modules in ascending order
		for module in sorted(modules_packages[package]):
			# [DOC] Add module header
			Config._api_ref += f'### Module: {module}\n'
			# [DOC] Add module description
			Config._api_ref += f'{modules[module].__doc__}\n'
			# [DOC] Add module attrs header
			Config._api_ref += '#### Attrs\n'
			# [DOC] Iterate over module attrs to add attrs types, defaults (if any)
			for attr in modules[module].attrs.keys():
				attr_ref = f'* {attr}:\n'
				if modules[module].attrs[attr]._desc:
					attr_ref += f'  * {modules[module].attrs[attr]._desc}\n'
				attr_ref += f'  * Type: `{modules[module].attrs[attr]}`\n'
				for default_attr in modules[module].defaults.keys():
					if (
						default_attr == attr
						or default_attr.startswith(f'{attr}.')
						or default_attr.startswith(f'{attr}:')
					):
						if type(modules[module].defaults[default_attr]) == ATTR_MOD:
							attr_ref += f'  * Default [{default_attr}]:\n'
							attr_ref += f'	* ATTR_MOD condition: `{extract_lambda_body(modules[module].defaults[default_attr].condition)}`\n'
							if callable(modules[module].defaults[default_attr].default):
								attr_ref += f'	* ATTR_MOD default: `{extract_lambda_body(modules[module].defaults[default_attr].default)}`\n'
							else:
								attr_ref += f'	* ATTR_MOD default: {modules[module].defaults[default_attr].default}\n'
						else:
							attr_ref += f'  * Default [{default_attr}]: {modules[module].defaults[default_attr]}\n'
				Config._api_ref += attr_ref
			if modules[module].diff:
				Config._api_ref += f'#### Attrs Diff: {modules[module].diff}\n'
			# [DOC] Add module methods
			Config._api_ref += '#### Methods\n'
			for method in modules[module].methods.keys():
				Config._api_ref += f'##### Method: {method}\n'
				Config._api_ref += f'* Permissions Sets:\n'
				for permission in modules[module].methods[method].permissions:
					Config._api_ref += f'  * {permission.privilege}\n'
					# [DOC] Add Query Modifier
					if permission.query_mod:
						Config._api_ref += f'	* Query Modifier:\n'
						if type(permission.query_mod) == dict:
							permission.query_mod = [permission.query_mod]
						for i in range(len(permission.query_mod)):
							Config._api_ref += f'	  * Set {i}:\n'
							for attr in permission.query_mod[i].keys():
								if type(permission.query_mod[i][attr]) == ATTR_MOD:
									Config._api_ref += f'		* {attr}:\n'
									Config._api_ref += f'		  * ATTR_MOD condition: {extract_lambda_body(permission.query_mod[i][attr].condition)}\n'
									if callable(permission.query_mod[i][attr].default):
										Config._api_ref += f'		  * ATTR_MOD default: {extract_lambda_body(permission.query_mod[i][attr].default)}\n'
									else:
										Config._api_ref += f'		  * ATTR_MOD default: {permission.query_mod[i][attr].default}\n'
								else:
									Config._api_ref += f'		* {attr}: {permission.query_mod[i][attr]}\n'
					else:
						Config._api_ref += f'	* Query Modifier: None\n'
					# [DOC] Add Doc Modifier
					if permission.doc_mod:
						Config._api_ref += f'	* Doc Modifier:\n'
						if type(permission.doc_mod) == dict:
							permission.doc_mod = [permission.doc_mod]
						for i in range(len(permission.doc_mod)):
							Config._api_ref += f'	  * Set {i}:\n'
							for attr in permission.doc_mod[i].keys():
								if type(permission.doc_mod[i][attr]) == ATTR_MOD:
									Config._api_ref += f'		* {attr}:\n'
									Config._api_ref += f'		  * ATTR_MOD condition: `{extract_lambda_body(permission.doc_mod[i][attr].condition)}`\n'
									if callable(permission.doc_mod[i][attr].default):
										Config._api_ref += f'		  * ATTR_MOD default: {extract_lambda_body(permission.doc_mod[i][attr].default)}\n'
									else:
										Config._api_ref += f'		  * ATTR_MOD default: {permission.doc_mod[i][attr].default}\n'
								else:
									Config._api_ref += f'		* {attr}: {permission.doc_mod[i][attr]}\n'
					else:
						Config._api_ref += f'	* Doc Modifier: None\n'
				# [DOC] Add Query Args
				if modules[module].methods[method].query_args:
					Config._api_ref += f'* Query Args Sets:\n'
					for query_args_set in modules[module].methods[method].query_args:
						Config._api_ref += f'  * `{query_args_set}`\n'
				else:
					Config._api_ref += f'* Query Args Sets: None\n'
				# [DOC] Add Doc Args
				if modules[module].methods[method].doc_args:
					Config._api_ref += f'* DOC Args Sets:\n'
					for doc_args_set in modules[module].methods[method].doc_args:
						Config._api_ref += f'  * `{doc_args_set}`\n'
				else:
					Config._api_ref += f'* Doc Args Sets: None\n'
			# [DOC] Add module extns
			if modules[module].extns.keys():
				Config._api_ref += '#### Extended Attrs\n'
				for attr in modules[module].extns.keys():
					Config._api_ref += f'* {attr}:\n'
					if type(modules[module].extns[attr]) == EXTN:
						Config._api_ref += (
							f'  * Module: \'{modules[module].extns[attr].module}\'\n'
						)
						Config._api_ref += f'  * Extend Attrs: \'{modules[module].extns[attr].attrs}\'\n'
						Config._api_ref += (
							f'  * Force: \'{modules[module].extns[attr].force}\'\n'
						)
					elif type(modules[module].extns[attr]) == ATTR_MOD:
						Config._api_ref += f'  * ATTR_MOD condition: `{extract_lambda_body(modules[module].extns[attr].condition)}`\n'
						Config._api_ref += f'  * ATTR_MOD default: `{extract_lambda_body(modules[module].extns[attr].default)}`\n'
			else:
				Config._api_ref += '#### Extended Attrs: None\n'
			# [DOC] Add module cache sets
			if modules[module].cache:
				Config._api_ref += '#### Cache Sets\n'
				for i in range(len(modules[module].cache)):
					Config._api_ref += f'* Set {i}:\n'
					Config._api_ref += f'  * CACHE condition: `{extract_lambda_body(modules[module].cache[i].condition)}`\n'
					Config._api_ref += (
						f'  * CACHE period: {modules[module].cache[i].period}\n'
					)
			else:
				Config._api_ref += '#### Cache Sets: None\n'
			# [DOC] Add module anayltics sets
			if modules[module].analytics:
				Config._api_ref += '#### Analytics Sets\n'
				for i in range(len(modules[module].analytics)):
					Config._api_ref += f'* Set {i}:\n'
					Config._api_ref += f'  * ANALYTIC condition: `{extract_lambda_body(modules[module].analytics[i].condition)}`\n'
					Config._api_ref += f'  * ANALYTIC doc: `{extract_lambda_body(modules[module].analytics[i].doc)}`\n'
			else:
				Config._api_ref += '#### Analytics Sets: None\n'
	import os

	ref_file = os.path.join(
		Config._limp_location,
		'refs',
		f'LIMP_API_REF_{datetime.datetime.utcnow().strftime("%d-%b-%Y")}.md',
	)
	with open(ref_file, 'w') as f:
		f.write(Config._api_ref)
		logger.info(f'API reference generated and saved to: \'{ref_file}\'. Exiting.')
		exit()


def update_attr_values(
	*, attr: ATTR, value: Literal['default', 'extn'], value_path: str, value_val: Any
):
	value_path = value_path.split('.')
	for child_default_path in value_path:
		if ':' in child_default_path:
			attr = attr._args['dict'][child_default_path.split(':')[0]]._args['list'][
				int(child_default_path.split(':')[1])
			]
		else:
			attr = attr._args['dict'][child_default_path]
	setattr(attr, f'_{value}', value_val)


def process_file_obj(*, doc, files):
	for attr in doc.keys():
		if attr in files.keys():
			doc[attr] = []
			for file in files[attr].values():
				doc[attr].append(
					{
						'name': file['name'],
						'lastModified': file['lastModified'],
						'type': file['type'],
						'size': file['size'],
						'content': binary.Binary(
							bytes([int(byte) for byte in file['content'].split(',')])
						),
					}
				)
			del files[attr]
	return doc


def sigtime():
	sigtime.time = 0


sigtime()


def signal_handler(signum, frame):
	if time.time() - sigtime.time > 3:
		sigtime.time = time.time()
		logger.warn('Interrupt again within 3 seconds to exit.')
	else:
		if time.localtime().tm_hour >= 21 or time.localtime().tm_hour <= 4:
			msg = 'night'
		elif time.localtime().tm_hour >= 18:
			msg = 'evening'
		elif time.localtime().tm_hour >= 12:
			msg = 'afternoon'
		elif time.localtime().tm_hour >= 5:
			msg = 'morning'
		logger.info(f'Have a great {msg}!')
		import os

		if os.name == 'nt':
			os.kill(os.getpid(), 9)
		else:
			exit()


def extract_attr(*, scope: Dict[str, Any], attr_path: str):
	attr_path = attr_path[3:].split('.')
	attr = scope
	for i in range(len(attr_path)):
		child_attr = attr_path[i]
		try:
			if ':' in child_attr:
				child_attr = child_attr.split(':')
				attr = attr[child_attr[0]][int(child_attr[1])]
			else:
				attr = attr[child_attr]
		except Exception as e:
			logger.error(f'Failed to extract {child_attr} from {attr}.')
			raise e
	return attr


def set_attr(*, scope: Dict[str, Any], attr_path: str, value: Any):
	attr_path = attr_path[3:].split('.')
	attr = scope
	for i in range(len(attr_path) - 1):
		child_attr = attr_path[i]
		try:
			if ':' in child_attr:
				child_attr = child_attr.split(':')
				attr = attr[child_attr[0]][int(child_attr[1])]
			else:
				attr = attr[child_attr]
		except Exception as e:
			logger.error(f'Failed to extract {child_attr} from {attr}.')
			raise e
	if ':' in attr_path[-1]:
		attr_path[-1] = attr_path[-1].split(':')
		attr[attr_path[-1][0]][int(attr_path[-1][1])] = value
	else:
		attr[attr_path[-1]] = value


class MissingAttrException(Exception):
	def __init__(self, *, attr_name):
		self.attr_name = attr_name
		logger.debug(f'MissingAttrException: {str(self)}')

	def __str__(self):
		return f'Missing attr \'{self.attr_name}\''


class InvalidAttrException(Exception):
	def __init__(self, *, attr_name, attr_type, val_type):
		self.attr_name = attr_name
		self.attr_type = attr_type
		self.val_type = val_type
		logger.debug(f'InvalidAttrException: {str(self)}')

	def __str__(self):
		return f'Invalid attr \'{self.attr_name}\' of type \'{self.val_type}\' with required type \'{self.attr_type._type}\''


class ConvertAttrException(Exception):
	def __init__(self, *, attr_name, attr_type, val_type):
		self.attr_name = attr_name
		self.attr_type = attr_type
		self.val_type = val_type
		logger.debug(f'ConvertAttrException: {str(self)}')

	def __str__(self):
		return f'Can\'t convert attr \'{self.attr_name}\' of type \'{self.val_type}\' to type \'{self.attr_type._type}\''


def validate_doc(
	*,
	doc: LIMP_DOC,
	attrs: Dict[str, ATTR],
	allow_opers: bool = False,
	allow_none: bool = False,
	skip_events: List[str] = None,
	env: Dict[str, Any] = None,
	query: Union[LIMP_QUERY, Query] = None,
):
	for attr in attrs.keys():
		if attr not in doc.keys():
			doc[attr] = None
		try:
			doc[attr] = validate_attr(
				attr_name=attr,
				attr_type=attrs[attr],
				attr_val=doc[attr],
				allow_opers=allow_opers,
				allow_none=allow_none,
				skip_events=skip_events,
				env=env,
				query=query,
				doc=doc,
			)
		except Exception as e:
			if type(e) in [InvalidAttrException, ConvertAttrException]:
				if doc[attr] == None:
					raise MissingAttrException(attr_name=attr)
				else:
					raise e
			else:
				raise e


def validate_default(
	*,
	attr_type: ATTR,
	attr_val: Any,
	skip_events: List[str] = None,
	env: Dict[str, Any] = None,
	query: Union[LIMP_QUERY, Query] = None,
	doc: LIMP_DOC = None,
	scope: LIMP_DOC = None,
	allow_none: bool,
):
	if not allow_none and type(attr_type._default) == ATTR_MOD:
		if attr_type._default.condition(
			skip_events=skip_events, env=env, query=query, doc=doc, scope=scope
		):
			if callable(attr_type._default.default):
				attr_val = attr_type._default.default(
					skip_events=skip_events, env=env, query=query, doc=doc, scope=scope
				)
			else:
				attr_val = attr_type._default.default
			return copy.deepcopy(attr_val)

	elif attr_val == None:
		if allow_none:
			return attr_val
		elif attr_type._default != LIMP_VALUES.NONE_VALUE:
			return copy.deepcopy(attr_type._default)

	raise Exception('No default set to validate.')


def validate_attr(
	*,
	attr_name: str,
	attr_type: ATTR,
	attr_val: Any,
	allow_opers: bool = False,
	allow_none: bool = False,
	skip_events: List[str] = None,
	env: Dict[str, Any] = None,
	query: Union[LIMP_QUERY, Query] = None,
	doc: LIMP_DOC = None,
	scope: LIMP_DOC = None,
):
	from config import Config

	try:
		return validate_default(
			attr_type=attr_type,
			attr_val=attr_val,
			skip_events=skip_events,
			env=env,
			query=query,
			doc=doc,
			scope=scope if scope else doc,
			allow_none=allow_none,
		)
	except:
		pass

	attr_oper = False
	if allow_opers and type(attr_val) == dict:
		if '$add' in attr_val.keys():
			attr_oper = '$add'
			attr_val = attr_val['$add']
		elif '$multiply' in attr_val.keys():
			attr_oper = '$multiply'
			attr_val = attr_val['$multiply']
		elif '$append' in attr_val.keys():
			attr_oper = '$append'
			if '$unique' in attr_val.keys() and attr_val['$unique'] == True:
				attr_oper = '$append__unique'
			attr_val = [attr_val['$append']]
		elif '$remove' in attr_val.keys():
			attr_oper = '$remove'
			attr_val = attr_val['$remove']

	try:
		if attr_type._type == 'ANY':
			return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'ACCESS':
			if (
				type(attr_val) == dict
				and set(attr_val.keys()) == {'anon', 'users', 'groups'}
				and type(attr_val['anon']) == bool
				and type(attr_val['users']) == list
				and type(attr_val['groups']) == list
			):
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'BOOL':
			if type(attr_val) == bool:
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'DATE':
			if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', attr_val):
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'DATETIME':
			if re.match(
				r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]{6})?)?$',
				attr_val,
			):
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'DICT':
			if type(attr_val) == dict:
				if '__key' in attr_type._args['dict'].keys():
					if '__min' in attr_type._args['dict'].keys():
						if len(attr_val.keys()) < attr_type._args['dict']['__min']:
							raise InvalidAttrException(
								attr_name=attr_name,
								attr_type=attr_type,
								val_type=type(attr_val),
							)
					if '__max' in attr_type._args['dict'].keys():
						if len(attr_val.keys()) > attr_type._args['dict']['__max']:
							raise InvalidAttrException(
								attr_name=attr_name,
								attr_type=attr_type,
								val_type=type(attr_val),
							)
					shadow_attr_val = {}
					for child_attr_val in attr_val.keys():
						shadow_attr_val[
							validate_attr(
								attr_name=f'{attr_name}.{child_attr_val}',
								attr_type=attr_type._args['dict']['__key'],
								attr_val=child_attr_val,
								allow_opers=allow_opers,
								allow_none=allow_none,
								skip_events=skip_events,
								env=env,
								query=query,
								doc=doc,
								scope=attr_val,
							)
						] = validate_attr(
							attr_name=f'{attr_name}.{child_attr_val}',
							attr_type=attr_type._args['dict']['__val'],
							attr_val=attr_val[child_attr_val],
							allow_opers=allow_opers,
							allow_none=allow_none,
							skip_events=skip_events,
							env=env,
							query=query,
							doc=doc,
							scope=attr_val,
						)
					if '__req' in attr_type._args['dict'].keys():
						for req_key in attr_type._args['dict']['__req']:
							if req_key not in shadow_attr_val.keys():
								raise InvalidAttrException(
									attr_name=attr_name,
									attr_type=attr_type,
									val_type=type(attr_val),
								)
					return return_valid_attr(
						attr_val=shadow_attr_val, attr_oper=attr_oper
					)
				else:
					for child_attr_type in attr_type._args['dict'].keys():
						if child_attr_type not in attr_val.keys():
							attr_val[child_attr_type] = None
						attr_val[child_attr_type] = validate_attr(
							attr_name=f'{attr_name}.{child_attr_type}',
							attr_type=attr_type._args['dict'][child_attr_type],
							attr_val=attr_val[child_attr_type],
							allow_opers=allow_opers,
							allow_none=allow_none,
							skip_events=skip_events,
							env=env,
							query=query,
							doc=doc,
							scope=attr_val,
						)
					return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'EMAIL':
			if re.match(r'^[^@]+@[^@]+\.[^@]+$', attr_val):
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'FILE':
			if type(attr_val) == list and len(attr_val):
				try:
					validate_attr(
						attr_name=attr_name,
						attr_type=attr_type,
						attr_val=attr_val[0],
						allow_opers=allow_opers,
						allow_none=allow_none,
						skip_events=skip_events,
						env=env,
						query=query,
						doc=doc,
						scope=attr_val,
					)
					attr_val = attr_val[0]
				except:
					raise InvalidAttrException(
						attr_name=attr_name,
						attr_type=attr_type,
						val_type=type(attr_val),
					)
			file_type = (
				type(attr_val) == dict
				and set(attr_val.keys())
				== {'name', 'lastModified', 'type', 'size', 'content'}
				and type(attr_val['name']) == str
				and type(attr_val['lastModified']) == int
				and type(attr_val['size']) == int
				and type(attr_val['content']) in [binary.Binary, bytes]
			)
			if not file_type:
				raise InvalidAttrException(
					attr_name=attr_name, attr_type=attr_type, val_type=type(attr_val)
				)
			if attr_type._args['types']:
				for file_type in attr_type._args['types']:
					if attr_val['type'].split('/')[0] == file_type.split('/')[0]:
						if (
							file_type.split('/')[1] == '*'
							or attr_val['type'].split('/')[1] == file_type.split('/')[1]
						):
							return return_valid_attr(
								attr_val=attr_val, attr_oper=attr_oper
							)
			else:
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'FLOAT':
			if type(attr_val) == str and re.match(r'^[0-9]+(\.[0-9]+)?$', attr_val):
				attr_val = float(attr_val)
			elif type(attr_val) == int:
				attr_val = float(attr_val)

			if type(attr_val) == float:
				if attr_type._args['range']:
					if int(attr_val) in attr_type._args['range']:
						return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)
				else:
					return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'GEO':
			if (
				type(attr_val) == dict
				and list(attr_val.keys()) == ['type', 'coordinates']
				and attr_val['type'] in ['Point']
				and type(attr_val['coordinates']) == list
				and len(attr_val['coordinates']) == 2
				and type(attr_val['coordinates'][0]) in [int, float]
				and type(attr_val['coordinates'][1]) in [int, float]
			):
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'ID':
			if type(attr_val) == BaseModel or type(attr_val) == DictObj:
				return return_valid_attr(attr_val=attr_val._id, attr_oper=attr_oper)
			elif type(attr_val) == ObjectId:
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)
			elif type(attr_val) == str:
				try:
					return return_valid_attr(
						attr_val=ObjectId(attr_val), attr_oper=attr_oper
					)
				except:
					raise ConvertAttrException(
						attr_name=attr_name,
						attr_type=attr_type,
						val_type=type(attr_val),
					)

		elif attr_type._type == 'INT':
			if type(attr_val) == str and re.match(r'^[0-9]+$', attr_val):
				attr_val = int(attr_val)

			if type(attr_val) == int:
				if attr_type._args['range']:
					if attr_val in attr_type._args['range']:
						return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)
				else:
					return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'IP':
			if re.match(
				r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
				attr_val,
			):
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'LIST':
			if type(attr_val) == list:
				for i in range(len(attr_val)):
					child_attr_val = attr_val[i]
					child_attr_check = False
					for child_attr_type in attr_type._args['list']:
						try:
							attr_val[i] = validate_attr(
								attr_name=attr_name,
								attr_type=child_attr_type,
								attr_val=child_attr_val,
								allow_opers=allow_opers,
								allow_none=allow_none,
								skip_events=skip_events,
								env=env,
								query=query,
								doc=doc,
								scope=attr_val,
							)
							child_attr_check = True
							break
						except:
							pass
					if not child_attr_check:
						raise InvalidAttrException(
							attr_name=attr_name,
							attr_type=attr_type,
							val_type=type(attr_val),
						)
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'LOCALE':
			attr_val = validate_attr(
				attr_name=attr_name,
				attr_type=ATTR.DICT(
					dict={
						'__key': ATTR.LITERAL(
							literal=[locale for locale in Config.locales]
						),
						'__val': ATTR.STR(),
						'__min': 1,
						'__req': [Config.locale],
					}
				),
				attr_val=attr_val,
				allow_opers=allow_opers,
				allow_none=allow_none,
				skip_events=skip_events,
				env=env,
				query=query,
				doc=doc,
				scope=attr_val,
			)
			attr_val = {
				locale: attr_val[locale]
				if locale in attr_val.keys()
				else attr_val[Config.locale]
				for locale in Config.locales
			}
			return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'LOCALES':
			if attr_val in Config.locales:
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'PHONE':
			if attr_type._args['codes']:
				for phone_code in attr_type._args['codes']:
					if re.match(fr'^\+{phone_code}[0-9]+$', attr_val):
						return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)
			else:
				if re.match(r'^\+[0-9]+$', attr_val):
					return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'STR':
			if type(attr_val) == str:
				if attr_type._args['pattern']:
					if re.match(f'^{attr_type._args["pattern"]}$', attr_val):
						return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)
				else:
					return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'TIME':
			if re.match(r'^[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]{6})?)?$', attr_val):
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'URI_WEB':
			if re.match(
				r'^https?:\/\/(?:[\w\-\_]+\.)(?:\.?[\w]{2,})+([\?\/].*)?$', attr_val
			):
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'LITERAL':
			if attr_val in attr_type._args['literal']:
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'UNION':
			for child_attr in attr_type._args['union']:
				try:
					validate_attr(
						attr_name=attr_name,
						attr_type=child_attr,
						attr_val=attr_val,
						allow_opers=allow_opers,
						allow_none=allow_none,
						skip_events=skip_events,
						env=env,
						query=query,
						doc=doc,
						scope=attr_val,
					)
				except:
					continue
				return return_valid_attr(attr_val=attr_val, attr_oper=attr_oper)

		elif attr_type._type == 'TYPE':
			return return_valid_attr(
				attr_val=Config.types[attr_type._args['type']](
					attr_name=attr_name, attr_type=attr_type, attr_val=attr_val
				),
				attr_oper=attr_oper,
			)

	except Exception as e:
		if type(e) in [InvalidAttrException, ConvertAttrException]:
			if allow_none:
				return None
			elif attr_type._default != LIMP_VALUES.NONE_VALUE:
				return attr_type._default
			else:
				raise e

	raise InvalidAttrException(
		attr_name=attr_name, attr_type=attr_type, val_type=type(attr_val)
	)


def return_valid_attr(
	*,
	attr_val: Any,
	attr_oper: Literal[
		False, '$add', '$multiply', '$append', '$append__unique', '$remove'
	],
):
	if not attr_oper:
		return attr_val
	elif attr_oper in ['$add', '$multiply', '$remove']:
		return {attr_oper: attr_val}
	elif attr_oper == '$append':
		return {'$append': attr_val[0], '$unique': False}
	elif attr_oper == '$append__unique':
		return {'$append': attr_val[0], '$unique': True}


def generate_attr(*, attr_type: ATTR) -> Any:
	from config import Config

	if attr_type._type == 'ANY':
		return '__any'
	elif attr_type._type == 'ACCESS':
		return {'anon': True, 'users': [], 'groups': []}
	elif attr_type._type == 'BOOL':
		attr_val = random.choice([True, False])
		return attr_val

	elif attr_type._type == 'DATE':
		attr_val = datetime.datetime.utcnow()
		return attr_val.isoformat().split('T')[0]

	elif attr_type._type == 'DATETIME':
		attr_val = datetime.datetime.utcnow()
		return attr_val.isoformat()

	elif attr_type._type == 'DICT':
		attr_val = {
			child_attr: generate_attr(attr_type=attr_type._args['dict'][child_attr])
			for child_attr in attr_type._args['dict'].keys()
		}
		return attr_val

	elif attr_type._type == 'EMAIL':
		return f'some-{math.ceil(random.random() * 10000)}@email.com'

	elif attr_type._type == 'FILE':
		attr_file_type = 'text/plain'
		attr_file_extension = 'txt'
		if attr_type._args['types']:
			for file_type in attr_type._args['types']:
				if '/' in file_type:
					attr_file_type = file_type
				if '*.' in file_type:
					attr_file_extension = file_type.replace('*.', '')
		file_name = f'__file-{math.ceil(random.random() * 10000)}.{attr_file_extension}'
		return {
			'name': file_name,
			'lastModified': 100000,
			'type': attr_file_type,
			'size': 6,
			'content': b'__file',
		}

	elif attr_type._type == 'FLOAT':
		if attr_type._args['range']:
			attr_val = random.choice([i for i in range(*attr_type._args['range'])])
		else:
			attr_val = math.ceil(random.random() * 10000)
		return attr_val

	elif attr_type._type == 'GEO':
		return {
			'type': 'Point',
			'coordinates': [
				math.ceil(random.random() * 100000) / 1000,
				math.ceil(random.random() * 100000) / 1000,
			],
		}

	elif attr_type._type == 'ID':
		return ObjectId()

	elif attr_type._type == 'INT':
		if attr_type._args['range']:
			attr_val = random.choice([i for i in range(*attr_type._args['range'])])
		else:
			attr_val = math.ceil(random.random() * 10000)
		return attr_val

	elif attr_type._type == 'IP':
		return '127.0.0.1'

	elif attr_type._type == 'LIST':
		return [generate_attr(attr_type=random.choice(attr_type._args['list']))]

	elif attr_type._type == 'LOCALE':
		return {
			locale: f'__locale-{math.ceil(random.random() * 10000)}'
			for locale in Config.locales
		}

	elif attr_type._type == 'LOCALES':
		from config import Config

		return Config.locale

	elif attr_type._type == 'PHONE':
		attr_phone_code = '000'
		if attr_type._args['codes']:
			attr_phone_code = random.choice(attr_type._args['codes'])
		return f'+{attr_phone_code}{math.ceil(random.random() * 10000)}'

	elif attr_type._type == 'STR':
		return f'__str-{math.ceil(random.random() * 10000)}'

	elif attr_type._type == 'TIME':
		attr_val = datetime.datetime.utcnow()
		return attr_val.isoformat().split('T')[1]

	elif attr_type._type == 'URI_WEB':
		return f'https://some.uri-{math.ceil(random.random() * 10000)}.com'

	elif attr_type._type == 'LITERAL':
		attr_val = random.choice(attr_type._args['literal'])
		return attr_val

	elif attr_type._type == 'UNION':
		attr_val = generate_attr(attr_type=random.choice(attr_type._args['union']))

	raise Exception(f'Unkown generator attr \'{attr_type}\'')
