from config import Config
from event import Event

from bson import ObjectId, binary

import logging, json, pkgutil, inspect, re, datetime, time, json, copy
logger = logging.getLogger('limp')

NONE_VALUE = 'NONE_VALUE'

class JSONEncoder(json.JSONEncoder):
	def default(self, o): # pylint: disable=E0202
		from base_model import BaseModel
		if isinstance(o, ObjectId):
			return str(o)
		elif isinstance(o, BaseModel) or isinstance(o, DictObj):
			return o._attrs()
		elif type(o) == datetime.datetime:
			return o.isoformat()
		elif type(o) == bytes:
			return True
		try:
			return json.JSONEncoder.default(self, o)
		except TypeError:
			return str(o)

class DictObj:
	__attrs = {}
	def __init__(self, attrs):
		if type(attrs) == DictObj:
			attrs = attrs._attrs()
		elif type(attrs) != dict:
			raise TypeError
		self.__attrs = attrs
	def __deepcopy__(self, memo):
		return DictObj(copy.deepcopy(self.__attrs))
	def __repr__(self):
		return '<DictObj:{}>'.format(self.__attrs)
	def __getattr__(self, attr):
		return self.__attrs[attr]
	def __setattr__(self, attr, val):
		if not attr.endswith('__attrs'):
			raise AttributeError
		object.__setattr__(self, attr, val)
	def __getitem__(self, attr):
		try:
			return self.__attrs[attr]
		except Exception as e:
			logger.debug('Unable to __getitem__ %s of %s.', attr, self.__attrs.keys())
			raise e
	def __setitem__(self, attr, val):
		self.__attrs[attr] = val
	def __delitem__(self, attr):
		del self.__attrs[attr]
	def __contains__(self, attr):
		return attr in self.__attrs.keys()
	def _attrs(self):
		return copy.deepcopy(self.__attrs)

class Query(list):
	def __init__(self, query):
		self._query = query
		self._special = {}
		self._index = {}
		self._create_index(self._query)
		super().__init__(self._query)
	def _create_index(self, query, path=[]):
		if not path:
			self._index = {}
		for i in range(0, query.__len__()):
			if type(query[i]) == dict:
				del_attrs = []
				for attr in query[i].keys():
					if attr[0] == '$':
						self._special[attr] = query[i][attr]
						del_attrs.append(attr)
					elif attr.startswith('__or'):
						self._create_index(query[i][attr], path=path + [i, attr])
					else:
						if type(query[i][attr]) == dict and query[i][attr].keys().__len__() == 1 and list(query[i][attr].keys())[0][0] == '$':
							attr_oper = list(query[i][attr].keys())[0]
						else:
							attr_oper = '$eq'
						if attr not in self._index.keys():
							self._index[attr] = []
						if isinstance(query[i][attr], DictObj):
							query[i][attr] = query[i][attr]._id
						self._index[attr].append({
							'oper':attr_oper,
							'path':path + [i],
							'val':query[i][attr]
						})
				for attr in del_attrs:
					del query[i][attr]
			elif type(query[i]) == list:
				self._create_index(query[i], path=path + [i])
		if not path:
			self._query = self._sanitise_query()
	def _sanitise_query(self, query=None):
		if query == None:
			query = self._query
		query_shadow = []
		for step in query:
			if type(step) == dict:
				for attr in step.keys():
					if attr.startswith('__or'):
						step[attr] = self._sanitise_query(step[attr])
						if len(step[attr]):
							query_shadow.append(step)
							break
					elif attr[0] != '$':
						query_shadow.append(step)
						break
			elif type(step) == list:
				step = self._sanitise_query(step)
				if len(step):
					query_shadow.append(step)
		return query_shadow
	def __deepcopy__(self, memo):
		try:
			return self._query.__deepcopy__(memo)
		except:
			return self._query
	def append(self, obj):
		self._query.append(obj)
		self._create_index(self._query)
		super().__init__(self._query)
	def __contains__(self, attr):
		if attr[0] == '$':
			return attr in self._special.keys()
		else:
			if ':' in attr:
				attr_index, attr_oper = attr.split(':')
			else:
				attr_index = attr
				attr += ':$eq'
				attr_oper = '$eq'

			if attr_index in self._index.keys():
				for val in self._index[attr_index]:
					if val['oper'] == attr_oper:
						return True
			return False
	def __getitem__(self, attr):
		if attr[0] == '$':
			return self._special[attr]
		else:
			attrs = []
			vals = []
			paths = []
			indexes = []
			attr_filter = False
			oper_filter = False

			if attr.split(':')[0] != '*':
				attr_filter = attr.split(':')[0]

			if ':' not in attr:
				oper_filter = '$eq'
				attr += ':$eq'
			elif ':*' not in attr:
				oper_filter = attr.split(':')[1]

			for index_attr in self._index.keys():
				if attr_filter and index_attr != attr_filter: continue
				# if oper_filter and index_attr.split(':')[1] != oper_filter: continue
				
				attrs += [index_attr for val in self._index[index_attr] if not oper_filter or (oper_filter and val['oper'] == oper_filter)]
				vals += [val['val'] for val in self._index[index_attr] if not oper_filter or (oper_filter and val['oper'] == oper_filter)]
				paths += [val['path'] for val in self._index[index_attr] if not oper_filter or (oper_filter and val['oper'] == oper_filter)]
				indexes += [i for i in range(0, self._index[index_attr].__len__()) if not oper_filter or (oper_filter and self._index[index_attr][i]['oper'] == oper_filter)]
			return QueryAttrList(self, attrs, paths, indexes, vals)
	def __setitem__(self, attr, val):
		if attr[0] != '$':
			raise Exception('Non-special attrs can only be updated by attr index.')
		self._special[attr] = val
	def __delitem__(self, attr):
		if attr[0] != '$':
			raise Exception('Non-special attrs can only be deleted by attr index.')
		del self._special[attr]

class QueryAttrList(list):
	def __init__(self, query, attrs, paths, indexes, vals):
		self._query = query
		self._attrs = attrs
		self._paths = paths
		self._indexes = indexes
		self._vals = vals
		super().__init__(vals)
	def __setitem__(self, item, val):
		if item == '*':
			for i in range(0, self._vals.__len__()):
				self.__setitem__(i, val)
		else:
			instance_attr = self._query._query
			for path_part in self._paths[item]:
				instance_attr = instance_attr[path_part]
			instance_attr[self._attrs[item].split(':')[0]] = val
			self._query._create_index(self._query._query)
	def __delitem__(self, item):
		if item == '*':
			for i in range(0, self._vals.__len__()):
				self.__delitem__(i)
		else:
			instance_attr = self._query._query
			for path_part in self._paths[item]:
				instance_attr = instance_attr[path_part]
			del instance_attr[self._attrs[item].split(':')[0]]
			self._query._create_index(self._query._query)
	def replace_attr(self, item, new_attr):
		if item == '*':
			for i in range(0, self._vals.__len__()):
				self.replace_attr(i, new_attr)
		else:
			instance_attr = self._query._query
			for path_part in self._paths[item]:
				instance_attr = instance_attr[path_part]
			# [DOC] Set new attr
			instance_attr[new_attr] = instance_attr[self._attrs[item].split(':')[0]]
			# [DOC] Delete old attr
			del instance_attr[self._attrs[item].split(':')[0]]
			# [DOC] Update index
			self._query._create_index(self._query._query)
	
def import_modules(packages=None):
	import modules as package
	from base_module import BaseModule
	from config import Config # pylint: disable=W0612
	# package = modules
	modules = {}
	package_prefix = package.__name__ + '.'
	for importer, pkgname, ispkg in pkgutil.iter_modules(package.__path__, package_prefix): # pylint: disable=unused-variable
		if packages and pkgname.replace('modules.', '') not in packages:
			logger.debug('Skipping package: %s', pkgname)
			continue
		child_package = __import__(pkgname, fromlist='*')
		for k, v in child_package.config().items():
			if k == 'envs':
				if Config.env and Config.env in v.keys():
					for kk, vv in v[Config.env].items():
						setattr(Config, kk, vv)
			elif type(v) == dict:
				getattr(Config, k).update(v)
			else:
				setattr(Config, k, v)
		child_prefix = child_package.__name__ + '.'
		for importer, modname, ispkg in pkgutil.iter_modules(child_package.__path__, child_prefix):
			module = __import__(modname, fromlist='*')
			for clsname in dir(module):
				if clsname != 'BaseModule' and inspect.isclass(getattr(module, clsname)) and issubclass(getattr(module, clsname), BaseModule):
					cls = getattr(module, clsname)
					module_name = re.sub(r'([A-Z])', r'_\1', clsname[0].lower() + clsname[1:]).lower()
					if module_name in modules.keys():
						logger.error('Duplicate module name \'%s\'. Exiting.', module_name)
						exit()
					modules[module_name] = cls()
	for module in modules.values():
		module.update_modules(modules)
	return modules

def parse_file_obj(doc, files):
	for attr in doc.keys():
		if attr in files.keys():
			doc[attr] = []
			for file in files[attr].values():
				doc[attr].append({
					'name':file['name'],
					'lastModified':file['lastModified'],
					'type':file['type'],
					'size':file['size'],
					'content':binary.Binary(bytes([int(byte) for byte in file['content'].split(',')]))
				})
			del files[attr]
	return doc

def sigtime():
	sigtime.time = 0
sigtime()
def signal_handler(signum, frame):
	if time.time() - sigtime.time > 3:
		sigtime.time = time.time()
		logger.warn(' Interrupt again within 3 seconds to exit.')
	else:
		if time.localtime().tm_hour >= 21 or time.localtime().tm_hour <= 4:
			msg = 'night'
		elif time.localtime().tm_hour >= 18:
			msg = 'evening'
		elif time.localtime().tm_hour >= 12:
			msg = 'afternoon'
		elif time.localtime().tm_hour >= 5:
			msg = 'morning'
		logger.info(' Have a great {}!'.format(msg))
		exit()

class MissingAttrException(Exception):
	def __init__(self, attr_name):
		self.attr_name = attr_name
	def __str__(self):
		return 'Missing attr \'{}\''.format(self.attr_name)

class InvalidAttrException(Exception):
	def __init__(self, attr_name, attr_type, val_type):
		self.attr_name = attr_name
		self.attr_type = attr_type
		self.val_type = val_type
	def __str__(self):
		return 'Invalid attr \'{}\' of type \'{}\' with required type \'{}\''.format(self.attr_name, self.val_type, self.attr_type)

class ConvertAttrException(Exception):
	def __init__(self, attr_name, attr_type, val_type):
		self.attr_name = attr_name
		self.attr_type = attr_type
		self.val_type = val_type
	def __str__(self):
		return 'Can\'t convert attr \'{}\' of type \'{}\' to type \'{}\''.format(self.attr_name, self.val_type, self.attr_type)

def validate_doc(doc, attrs, defaults={}, allow_opers=False, allow_none=False):
	for attr in attrs:
		if attr not in doc.keys():
			if not allow_none:
				if attr not in defaults.keys():
					raise MissingAttrException(attr)
				else:
					doc[attr] = defaults[attr]
					continue
		else:
			try:
				if allow_opers:
					if type(doc[attr]) == dict:
						if '$add' in doc[attr].keys():
							doc[attr] = {'$add':validate_attr(attr_name=attr, attr_type=attrs[attr], attr_val=doc[attr]['$add'])}
						elif '$push' in doc[attr].keys():
							doc[attr] = {'$push':validate_attr(attr_name=attr, attr_type=attrs[attr], attr_val=[doc[attr]['$push']])[0]}
						elif '$push_unique' in doc[attr].keys():
							doc[attr] = {'$push_unique':validate_attr(attr_name=attr, attr_type=attrs[attr], attr_val=[doc[attr]['$push_unique']])[0]}
						elif '$pull' in doc[attr].keys():
							doc[attr] = {'$pull':validate_attr(attr_name=attr, attr_type=attrs[attr], attr_val=doc[attr]['$pull'])}
						else:
							doc[attr] = validate_attr(attr_name=attr, attr_type=attrs[attr], attr_val=doc[attr])
					else:
						doc[attr] = validate_attr(attr_name=attr, attr_type=attrs[attr], attr_val=doc[attr])
				else:
					doc[attr] = validate_attr(attr_name=attr, attr_type=attrs[attr], attr_val=doc[attr])
			except Exception as e:
				if type(e) in [MissingAttrException, InvalidAttrException, ConvertAttrException]:
					if allow_none:
						doc[attr] = None
					else:
						if attr in defaults.keys():
							doc[attr] = defaults[attr]
						else:
							raise e
				else:
					raise e

def validate_attr(attr_name, attr_type, attr_val):
	from base_model import BaseModel
	try:
		if attr_type == 'any':
			return attr_val
		elif type(attr_type) == str and attr_type == 'id':
			if type(attr_val) == BaseModel:
				return attr_val._id
			elif type(attr_val) == ObjectId:
				return attr_val
			elif type(attr_val) == str:
				try:
					return ObjectId(attr_val)
				except:
					raise ConvertAttrException(attr_name=attr_name, attr_type=attr_type, val_type=type(attr_val))
		elif attr_type == 'locale':
			return validate_attr(attr_name=attr_name, attr_type={locale:'str' for locale in Config.locales}, attr_val=attr_val)
		elif type(attr_type) == str and attr_type.startswith('str'):
			if type(attr_val) == str:
				if attr_type != 'str':
					if re.match(f'^{attr_type[4:-1]}$', attr_val):
						return attr_val
				else:
					return attr_val
		elif type(attr_type) == str and attr_type.startswith('int'):
			if type(attr_val) == str and re.match(r'^[0-9]+$', attr_val):
				attr_val = int(attr_val)

			if type(attr_val) == int:
				if attr_type != 'int':
					vals_range = range(*[int(val) for val in attr_type[4:-1].split(':')])
					if attr_val in vals_range:
						return attr_val
				else:
					return attr_val
		elif type(attr_type) == str and attr_type.startswith('float'):
			if type(attr_val) == str and re.match(r'^[0-9]+(\.[0-9]+)?$', attr_val):
				attr_val = float(attr_val)
			elif type(attr_val) == int:
				attr_val = float(attr_val)

			if type(attr_val) == float:
				if attr_type != 'float':
					vals_range = range(*[int(val) for val in attr_type[6:-1].split(':')])
					if int(attr_val) in vals_range:
						return attr_val
				else:
					return attr_val
		elif type(attr_type) == tuple:
			if attr_val in attr_type:
				return attr_val
		elif attr_type == 'bool':
			if type(attr_val) == bool:
				return attr_val
		elif type(attr_type) == str and attr_type == 'ip':
			if re.match(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', attr_val):
				return attr_val
		elif type(attr_type) == str and attr_type == 'email':
			if re.match(r'^[^@]+@[^@]+\.[^@]+$', attr_val):
				return attr_val
		elif type(attr_type) == str and attr_type.startswith('phone'):
			if attr_type != 'phone':
				for phone_code in attr_type[6:-1].split(','):
					if re.match(fr'^\+{phone_code}[0-9]+$', attr_val):
						return attr_val
			else:
				if re.match(r'^\+[0-9]+$', attr_val):
					return attr_val
		elif type(attr_type) == str and attr_type == 'uri:web':
			if re.match(r'^https?:\/\/(?:[\w\-\_]+\.)(?:\.?[\w]{2,})+$', attr_val):
				return attr_val
		elif type(attr_type) == str and attr_type == 'datetime':
			if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]{6})?)?$', attr_val):
				return attr_val
		elif type(attr_type) == str and attr_type == 'date':
			if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', attr_val):
				return attr_val
		elif type(attr_type) == str and attr_type == 'time':
			if re.match(r'^[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]{6})?)?$', attr_val):
				return attr_val
		elif type(attr_type) == str and attr_type.startswith('file'):
			if type(attr_val) == list and attr_val.__len__():
				try:
					validate_attr(attr_name=attr_name, attr_type='file', attr_val=attr_val[0])
					attr_val = attr_val[0]
				except:
					raise InvalidAttrException(attr_name=attr_name, attr_type=attr_type, val_type=type(attr_val))
			file_type = type(attr_val) == dict and 'name' in attr_val.keys() and 'lastModified' in attr_val.keys() and 'type' in attr_val.keys() and 'size' in attr_val.keys() and 'content' in attr_val.keys()
			if not file_type: raise InvalidAttrException(attr_name=attr_name, attr_type=attr_type, val_type=type(attr_val))
			if attr_type != 'file':
				for file_type in attr_type[5:-1].split(','):
					if attr_val['type'].split('/')[0] == file_type.split('/')[0]:
						if attr_val['type'].split('/')[1] == file_type.split('/')[1] or file_type.split('/')[1] == '*':
							return attr_val
			else:
				return attr_val
		elif type(attr_type) == str and attr_type == 'bin':
			if type(attr_val) == binary.Binary:
				return attr_val
		elif type(attr_type) == str and attr_type == 'geo':
			if type(attr_val) == dict and 'type' in attr_val.keys() and 'coordinates' in attr_val.keys() and attr_val['type'] in ['Point'] and type(attr_val['coordinates']) == list and attr_val['coordinates'].__len__() == 2 and type(attr_val['coordinates'][0]) in [int, float] and type(attr_val['coordinates'][1]) in [int, float]:
				return attr_val
		elif attr_type == 'privileges':
			if type(attr_val) == dict:
				return attr_val
		elif attr_type == 'attrs':
			if type(attr_val) == dict:
				return attr_val
		elif type(attr_type) == dict:
			if type(attr_val) == dict:
				for child_attr_type in attr_type.keys():
					if child_attr_type not in attr_val.keys(): raise InvalidAttrException(attr_name=attr_name, attr_type=attr_type, val_type=type(attr_val))
					attr_val[child_attr_type] = validate_attr(attr_name='{}.{}'.format(attr_name, child_attr_type), attr_type=attr_type[child_attr_type], attr_val=attr_val[child_attr_type])
				return attr_val
		elif type(attr_type) == str and attr_type == 'access':
			if type(attr_val) == dict and 'anon' in attr_val.keys() and type(attr_val['anon']) == bool and 'users' in attr_val.keys() and type(attr_val['users']) == list and 'groups' in attr_val.keys() and type(attr_val['groups']) == list:
				return attr_val
		elif type(attr_type) == list:
			if type(attr_val) == list:
				for child_attr_val in attr_val:
					child_attr_check = False
					for child_attr_type in attr_type:
						try:
							validate_attr(attr_name=attr_name, attr_type=child_attr_type, attr_val=child_attr_val)
							child_attr_check = True
							break
						except:
							pass
					if not child_attr_check:
						raise InvalidAttrException(attr_name=attr_name, attr_type=attr_type, val_type=type(attr_val))
				return attr_val
		elif type(attr_type) == str and attr_type == 'locales':
			if attr_val in Config.locales:
				return attr_val
		elif attr_type in Config.types.keys():
			return Config.types[attr_type](attr_name=attr_name, attr_type=attr_type, attr_val=attr_val)
		
		raise InvalidAttrException(attr_name=attr_name, attr_type=attr_type, val_type=type(attr_val))
	except:
		raise InvalidAttrException(attr_name=attr_name, attr_type=attr_type, val_type=type(attr_val))