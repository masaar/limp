from config import Config
from event import Event

from bson import ObjectId, binary

import logging, json, pkgutil, inspect, re, datetime, time, json, copy
logger = logging.getLogger('limp')

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
		return json.JSONEncoder.default(self, o)

class DictObj:
	__attrs = {}
	def __init__(self, attrs):
		self.__attrs = attrs
	def __deepcopy__(self, memo):
		return self.__attrs
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
	def __init__(self, query):
		self._query = query
		self._special = {}
		self._index = {}
		self._create_index(query)
		super().__init__(query)
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
					modules[re.sub(r'([A-Z])', r'_\1', clsname[0].lower() + clsname[1:]).lower()] = cls()
	for module in modules.values():
		module.modules = modules
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
	def __init__(self, attr):
		self.attr = attr
	def __str__(self):
		return 'Missing attr \'{}\''.format(self.attr)

class InvalidAttrException(Exception):
	def __init__(self, attr, attr_type):
		self.attr = attr
		self.attr_type = attr_type
	def __str__(self):
		return 'Invalid attr \'{}\' of type \'{}\''.format(self.attr, self.attr_type)

class ConvertAttrException(Exception):
	def __init__(self, attr, attr_type, val_type):
		self.attr = attr
		self.attr_type = attr_type
		self.val_type = val_type
	def __str__(self):
		return 'Can\'t convert attr \'{}\' of type \'{}\' to type \'{}\''.format(self.attr, self.val_type, self.attr_type)

def validate_doc(doc, attrs, optional_attrs=[], allow_opers=False):
	for attr in attrs:
		if attr not in doc.keys():
			if attr not in optional_attrs:
				raise MissingAttrException(attr)
		else:
			if attr == None and attr in optional_attrs:
				pass
			else:
				if allow_opers:
					if type(doc[attr]) == dict:
						if '$add' in doc[attr].keys():
							doc[attr] = {'$add':validate_attr(doc[attr]['$add'], attrs[attr])}
						elif '$push' in doc[attr].keys():
							doc[attr] = {'$push':validate_attr([doc[attr]['$push']], attrs[attr])[0]}
						elif '$pushUnique' in doc[attr].keys():
							doc[attr] = {'$pushUnique':validate_attr([doc[attr]['$pushUnique']], attrs[attr])[0]}
						elif '$pull' in doc[attr].keys():
							doc[attr] = {'$pull':validate_attr(doc[attr]['$pull'], attrs[attr])}
						else:
							doc[attr] = validate_attr(doc[attr], attrs[attr])
				else:
					doc[attr] = validate_attr(doc[attr], attrs[attr])

def validate_attr(attr, attr_type):
	from base_model import BaseModel
	try:
		if attr_type == 'any':
			return attr
		elif type(attr_type) == str and attr_type == 'id':
			if type(attr) == BaseModel:
				return attr._id
			elif type(attr) == ObjectId:
				return attr
			elif type(attr) == str:
				try:
					return ObjectId(attr)
				except:
					raise ConvertAttrException(attr, type(attr), attr_type)
		elif type(attr_type) == str and attr_type == 'str':
			if type(attr) == str:
				return attr
		elif type(attr_type) == str and attr_type == 'int':
			if type(attr) == int:
				return attr
		elif type(attr_type) == str and attr_type == 'float':
			if type(attr) == float:
				return attr
		elif type(attr_type) == tuple:
			if attr in attr_type:
				return attr
		elif attr_type == 'bool':
			if type(attr) == bool:
				return attr
		elif type(attr_type) == str and attr_type == 'ip':
			if re.match(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', attr):
				return attr
		elif type(attr_type) == str and attr_type == 'email':
			if re.match(r'[^@]+@[^@]+\.[^@]+', attr):
				return attr
		elif type(attr_type) == str and attr_type == 'phone':
			if re.match(r'\+[0-9]+', attr):
				return attr
		elif type(attr_type) == str and attr_type == 'uri:web':
			if re.match(r'https?:\/\/(?:[\w\-\_]+\.)(?:\.?[\w]{2,})+$', attr):
				return attr
		elif type(attr_type) == str and attr_type == 'datetime':
			if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{6})?$', attr):
				return attr
		elif type(attr_type) == str and attr_type == 'date':
			if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', attr):
				return attr
		elif type(attr_type) == str and attr_type == 'time':
			if re.match(r'^[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]{6})?)?$', attr):
				return attr
		elif type(attr_type) == str and attr_type.startswith('file'):
			file_type = type(attr) == dict and 'name' in attr.keys() and 'lastModified' in attr.keys() and 'type' in attr.keys() and 'size' in attr.keys() and 'content' in attr.keys()
			if not file_type: return False
			if attr_type != 'file':
				for file_type in attr_type[5:-1].split(','):
					if attr['type'].split('/')[0] == file_type.split('/')[0]:
						if attr['type'].split('/')[1] == file_type.split('/')[1] or file_type.split('/')[1] == '*':
							return attr
		elif type(attr_type) == str and attr_type == 'geo':
			if type(attr) == dict and 'type' in attr.keys() and 'coordinates' in attr.keys() and attr['type'] in ['Point'] and type(attr['coordinates']) == list and attr['coordinates'].__len__() == 2 and type(attr['coordinates'][0]) in [int, float] and type(attr['coordinates'][1]) in [int, float]:
				return attr
		elif attr_type == 'privileges':
			if type(attr) == dict:
				return attr
		elif attr_type == 'attrs':
			if type(attr) == dict:
				return attr
		elif type(attr_type) == dict:
			if type(attr) == dict:
				for child_attr_type in attr_type.keys():
					if child_attr_type not in attr.keys(): raise InvalidAttrException(attr, attr_type)
					attr[child_attr_type] = validate_attr(attr[child_attr_type], attr_type[child_attr_type])
				return attr
		elif type(attr_type) == str and attr_type == 'access':
			if type(attr) == dict and 'anon' in attr.keys() and type(attr['anon']) == bool and 'users' in attr.keys() and type(attr['users']) == list and 'groups' in attr.keys() and type(attr['groups']) == list:
				return attr
		elif type(attr_type) == list:
			if type(attr) == list:
				for child_attr in attr:
					child_attr_check = False
					for child_attr_type in attr_type:
						try:
							validate_attr(child_attr, child_attr_type)
							child_attr_check = True
							break
						except:
							pass
					if not child_attr_check:
						raise InvalidAttrException(attr, attr_type)
				return attr
		elif type(attr_type) == str and attr_type == 'locale':
			if type(attr) == dict:
				for locale in attr.keys():
					if locale not in Config.locales:
						raise InvalidAttrException(attr, attr_type)
				return attr
		elif type(attr_type) == str and attr_type == 'locales':
			if attr in Config.locales:
				return attr
		elif attr_type in Config.types.keys():
			Config.types[attr_type](attr=attr, attr_type=attr_type)
			return attr
		
		raise InvalidAttrException(attr, attr_type)
	except:
		raise InvalidAttrException(attr, attr_type)