from config import Config
from utils import ClassSingleton
from base_model import BaseModel

import logging, datetime
logger = logging.getLogger('limp')

class Data(metaclass=ClassSingleton):
	driver = Config.data_driver

	def singleton(self):
		if self.driver == 'mongodb':
			from drivers.mongodb import MongoDb
			self.driver = MongoDb
	
	def create_conn(self):
		return self.driver.create_conn()

	def read(self, env, session, collection, attrs, extns, modules, query):
		query = self.sanitise_attrs(query)
		return self.driver.read(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query)
	
	def create(self, env, session, collection, attrs, extns, modules, doc):
		doc = self.sanitise_attrs(doc)
		return self.driver.create(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, doc=doc)
	
	def update(self, env, session, collection, attrs, extns, modules, query, doc):
		query = self.sanitise_attrs(query)
		doc = self.sanitise_attrs(doc)
		return self.driver.update(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query, doc=doc)
	
	def delete(self, env, session, collection, attrs, extns, modules, query, force_delete):
		query = self.sanitise_attrs(query)
		return self.driver.delete(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query, force_delete=force_delete)

	def drop(self, env, session, collection):
		return self.driver.drop(env=env, session=session, collection=collection)
	
	def sanitise_attrs(self, attrs):
		if type(attrs) == dict:
			iter = attrs.keys()
		elif type(attrs) == list:
			iter = range(0, attrs.__len__())
		for attr in iter:
			# #logger.debug('testing attr: %s, %s, agaisnt type BaseModel: %s.', attr, attrs[attr], isinstance(attrs[attr], BaseModel))
			if type(attrs[attr]) == dict:
				attrs[attr] = self.sanitise_attrs(attrs[attr])
			elif type(attrs[attr]) == list:
				attrs[attr] = self.sanitise_attrs(attrs[attr])
			elif isinstance(attrs[attr], BaseModel):
				attrs[attr] = attrs[attr]._id
		return attrs