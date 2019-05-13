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

	def read(self, conn, session, collection, attrs, extns, modules, query):
		query = self.sanitise_attrs(query)
		return self.driver.read(conn=conn, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query)
	
	def create(self, conn, session, collection, attrs, extns, modules, doc):
		doc = self.sanitise_attrs(doc)
		return self.driver.create(conn=conn, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, doc=doc)
	
	def update(self, conn, session, collection, attrs, extns, modules, query, doc):
		query = self.sanitise_attrs(query)
		doc = self.sanitise_attrs(doc)
		return self.driver.update(conn=conn, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query, doc=doc)
	
	def delete(self, conn, session, collection, attrs, extns, modules, query, force_delete):
		# attrs = self.sanitise_attrs(attrs)
		# _id = self.sanitise_attrs([_id])[0]
		query = self.sanitise_attrs(query)
		return self.driver.delete(conn=conn, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query, force_delete=force_delete)
	
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
			# elif type(attrs[attr]) == datetime.datetime:
			# 	attrs[attr] = (attrs[attr].timestamp())
		return attrs