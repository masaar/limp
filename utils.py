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
			return (o - datetime.datetime(1970,1,1)).total_seconds()
		elif type(o) == bytes:
			return True
		return json.JSONEncoder.default(self, o)

class DictObj:
	def __init__(self, attrs):
		self.__attrs = attrs
	def __deepcopy__(self, memo):
		return self.__attrs
	def __repr__(self):
		return '<DictObj:{}>'.format(self.__attrs)
	def __getattr__(self, attr):
		return self.__attrs[attr]
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
	def _attrs(self):
		return self.__attrs

class Query(list):
	def _create_index(self, query, path=[]):
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
							attr_index = '{}:{}'.format(attr, list(query[i][attr].keys())[0])
						else:
							attr_index = '{}:$eq'.format(attr)
						if attr_index not in self._index.keys():
							self._index[attr_index] = []
						if isinstance(query[i][attr], DictObj):
							query[i][attr] = query[i][attr]._id
						self._index[attr_index].append({
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
		self._index = {}
		self._create_index(self._query)
		super().__init__(self._query)
	def __contains__(self, attr):
		if attr[0] == '$':
			return attr in self._special.keys()
		else:
			if ':' not in attr:
				attr += ':$eq'
			return attr in self._index.keys()
	def __getitem__(self, attr):
		if attr[0] == '$':
			return self._special[attr]
		else:
			attrs = []
			vals = []
			paths = []

			if attr.split(':')[0] == '*':
				attr_filter = False
			else:
				attr_filter = attr.split(':')[0]

			if ':' not in attr:
				oper_filter = '$eq'
				attr += ':$eq'
			elif ':*' in attr:
				oper_filter = False
			else:
				oper_filter = attr.split(':')[1]

			for index_attr in self._index.keys():
				if attr_filter and index_attr.split(':')[0] != attr_filter: continue
				if oper_filter and index_attr.split(':')[1] != oper_filter: continue
				
				attrs += [index_attr for val in self._index[index_attr]]
				vals += [val['val'] for val in self._index[index_attr]]
				paths += [val['path'] for val in self._index[index_attr]]
			return QueryAttrList(self, attrs, paths, vals)
	def __setitem__(self, attr, val):
		if attr[0] != '$':
			raise Exception('Non-special attrs can only be updated by attr index.')
		self._special[attr] = val
	def __delitem__(self, attr):
		if attr[0] != '$':
			raise Exception('Non-special attrs can only be deleted by attr index.')
		del self._special[attr]

class QueryAttrList(list):
	def __init__(self, query, attrs, paths, vals):
		self._query = query
		self._attrs = attrs
		self._paths = paths
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
			instance_attr[self._attrs[item]] = val
			self._query._index[self._attrs[item]][item]['val'] = val
	def __delitem__(self, item):
		if item == '*':
			for i in range(0, self._vals.__len__()):
				self.__delitem__(i)
		else:
			instance_attr = self._query._query
			for path_part in self._paths[item]:
				instance_attr = instance_attr[path_part]
			del instance_attr[self._attrs[item].split(':')[0]]
			del self._query._index[self._attrs[item]][item]
	
def import_modules(packages=None):
	import modules as package
	from base_module import BaseModule
	from config import Config # pylint: disable=W0612
	# package = modules
	modules = {}
	package_prefix = package.__name__ + '.'
	for importer, pkgname, ispkg in pkgutil.iter_modules(package.__path__, package_prefix): # pylint: disable=unused-variable
		if packages and pkgname.replace('modules.', '') not in packages:
			#logger.debug('Skipping package: %s', pkgname)
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

def validate_attr(attr, attr_type):
	from base_model import BaseModel
	
	if attr == None: return True
	if attr_type == 'any':
		return True
	elif type(attr_type) == str and attr_type == 'id':
		return type(attr) == ObjectId or type(attr) == BaseModel
	elif type(attr_type) == str and attr_type == 'str':
		return type(attr) == str
	elif type(attr_type) == str and attr_type == 'int':
		return type(attr) == int
	elif type(attr_type) == tuple:
		return attr in attr_type
	elif attr_type == 'bool':
		return type(attr) == bool
	elif type(attr_type) == str and attr_type == 'email':
		return re.match(r'[^@]+@[^@]+\.[^@]+', attr) != None
	elif type(attr_type) == str and attr_type == 'phone':
		return re.match(r'\+[0-9]+', attr) != None
	elif type(attr_type) == str and attr_type == 'uri:web':
		return re.match(r'https?:\/\/(?:[\w\-\_]+\.)(?:\.?[\w]{2,})+$', attr) != None
	elif type(attr_type) == str and attr_type == 'time':
		return type(attr) == datetime.datetime
	elif type(attr_type) == str and attr_type == 'file':
		return type(attr) == dict and 'name' in attr.keys() and 'lastModified' in attr.keys() and 'type' in attr.keys() and 'size' in attr.keys() and 'content' in attr.keys()
	elif type(attr_type) == str and attr_type == 'geo':
		return type(attr) == dict and 'type' in attr.keys() and 'coordinates' in attr.keys() and attr['type'] in ['Point'] and type(attr['coordinates']) == list and attr['coordinates'].__len__() == 2 and type(attr['coordinates'][0]) in [int, float] and type(attr['coordinates'][1]) in [int, float]
	elif attr_type == 'privileges':
		return type(attr) == dict
	elif attr_type == 'attrs':
		return type(attr) == dict or type(attr) == list
	elif type(attr_type) == str and attr_type == 'access':
		return type(attr) == dict and 'anon' in attr.keys() and type(attr['anon']) == bool and 'users' in attr.keys() and type(attr['users']) == list and 'groups' in attr.keys() and type(attr['groups']) == list
	elif type(attr_type) == list:
		if type(attr) != list: return False
		for child_attr in attr:
			if not validate_attr(child_attr, attr_type[0]):
				return False
	elif type(attr_type) == str and attr_type == 'locale':
		if type(attr) != dict: return False
		for locale in attr.keys():
			if locale not in Config.locales:
				return False
	elif type(attr_type) == str and attr_type == 'locales':
		return attr in Config.locales
	return True