from config import Config
from event import Event

from bson import ObjectId

import logging, json, pkgutil, inspect, re, datetime, time, json, copy
logger = logging.getLogger('limp')

class ClassSingleton(type):
	def __new__(cls, cls_name, bases, attrs):
		for name, attr in attrs.items():
			if callable(attr):
				attrs[name] = classmethod(attr)
		attrs['module_name'] = re.sub(r'([A-Z])', r'_\1', cls_name[0].lower() + cls_name[1:]).lower()
		return type.__new__(cls, cls_name, bases, attrs)
	
	def __init__(cls, cls_name, bases, attrs):
		cls.singleton()

class JSONEncoder(json.JSONEncoder):
	def default(self, o): # pylint: disable=E0202
		from base_model import BaseModel
		if isinstance(o, ObjectId):
			return str(o)
		elif isinstance(o, BaseModel) or isinstance(o, DictObj):
			return o._attrs()
		elif type(o) == datetime.datetime:
			# return o.timestamp()
			return (o - datetime.datetime(1970,1,1)).total_seconds()
		return json.JSONEncoder.default(self, o)

class DictObj:
	def __init__(self, attrs):
		self.__attrs = attrs
	def __repr__(self):
		return '<DictObj:{}>'.format(self.__attrs)
	def __getattr__(self, attr):
		return self.__attrs[attr]
	def __getitem__(self, attr):
		return self.__attrs[attr]
	def __setitem__(self, attr, val):
		self.__attrs[attr] = val
	def __delitem__(self, attr):
		del self.__attrs[attr]
	def _attrs(self):
		return self.__attrs

def import_modules(env=None, packages=None):
	import modules as package
	from base_module import BaseModule
	from config import Config # pylint: disable=W0612
	# package = modules
	modules = {}
	package_prefix = package.__name__ + '.'
	for importer, pkgname, ispkg in pkgutil.iter_modules(package.__path__, package_prefix):
		if packages and pkgname.replace('modules.', '') not in packages:
			#logger.debug('Skipping package: %s', pkgname)
			continue
		child_package = __import__(pkgname, fromlist='*')
		print('child_package', child_package, dir(child_package))
		for k, v in child_package.config().items():
			if k == 'envs':
				if env and env in v.keys():
					for kk, vv in v[env].items():
						setattr(Config, kk, vv)
			elif type(v) == dict:
				getattr(Config, k).update(v)
				# exec('Config.{} = "{}"'.format(k, v))
			else:
				setattr(Config, k, v)
				# exec('Config.{} = {}'.format(k, v))
		child_prefix = child_package.__name__ + '.'
		for importer, modname, ispkg in pkgutil.iter_modules(child_package.__path__, child_prefix):
			module = __import__(modname, fromlist='*')
			module_prefix = module.__name__ + '.'
			for clsname in dir(module):
				if clsname != 'BaseModule' and inspect.isclass(getattr(module, clsname)) and issubclass(getattr(module, clsname), BaseModule):
					cls = getattr(module, clsname)
					modules[re.sub(r'([A-Z])', r'_\1', clsname[0].lower() + clsname[1:]).lower()] = cls
	for module in modules.values():
		module.modules = modules
	return modules

def objectify_args(args):
	args_object = {}
	for arg in args.keys():
		arg_object = args_object
		arg_split = re.split(r'([^\\\]\.)', arg)
		for i in range(0, arg_split.__len__()):
			if i != arg_split.__len__() -1 and arg_split[i+1] and arg_split[i+1][-1] == '.':
				arg_split[i] += arg_split[i+1][0]
				arg_split[i+1] = '.'
		arg_split = [path.replace('\\.', '.') for path in arg_split if path != '.']
		for arg_path in arg_split:
			if arg_path == arg_split[-1]:
				arg_object[arg_path] = args[arg]
			else:
				if arg_path not in arg_object.keys():
					arg_object[arg_path] = {}
				arg_object = arg_object[arg_path]
	return args_object

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
		return type(attr) == dict and 'anon' in attr.keys() and type(attr['anon']) == bool and 'users' in attr.keys() and type(attr['users']) == list and 'groups' in attr.keys() and type(attr['users']) == list
	elif type(attr_type) == list:
		if type(attr) != list: return False
		for child_attr in attr:
			if not validate_attr(child_attr, attr_type[0]):
				return False
	elif type(attr_type) == str and attr_type == 'locale':
		if type(attr) != dict: return False
		for locale in attr.keys():
			print('checking:', locale)
			if locale not in Config.locales:
				return False
	return True

def call_event(event, query, context_module, user_module, notification_module):
	module_name = context_module.module_name
	#logger.debug('Checking %s event on module: %s', event, module_name)
	if '{}.{}'.format(module_name, event) in Config.events.keys():
		logger.debug('Found %s event on module: %s. Calling with query: %s', event, module_name, query)
		doc_results = context_module.methods['read'](skip_events=[Event.__PERM__], query=query)
		for doc in doc_results['args']['docs']:
			for module_event in Config.events['{}.{}'.format(module_name, event)]:
				if module_event['handler'] == 'notification':
					event_query = copy.deepcopy(module_event['query'])
					for arg in event_query.keys():
						if type(event_query[arg]['val']) == str and event_query[arg]['val'].startswith('$__doc.'):
							event_query[arg]['val'] = doc[event_query[arg]['val'].replace('$__doc.', '')]
					event_results = user_module.methods['read'](skip_events=[Event.__PERM__, Event.__ON__], query=event_query)
					#logger.debug('found %s users to notify.', event_results['args']['count'])
					# [DOC] Create notification for matching users
					for user in event_results['args']['docs']:
						#logger.debug('adding notification to user: %s, %s', user._id, user.name['en_AE'])
						notification_module.methods['create'](skip_events=[Event.__PERM__, Event.__NOTIF__], doc={
							'user':user._id,
							'title':module_event['context']['title'],
							'content':doc_results['args']['docs'][0],
							'status':'new'
						})
				elif module_event['handler'] == 'email':
					# [TODO] Re-implement omitted code
					1/0