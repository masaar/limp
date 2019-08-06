from config import Config
from utils import Query
from base_model import BaseModel

import logging, datetime
logger = logging.getLogger('limp')

DELETE_SOFT_SKIP_SYS = 'DELETE_SOFT_SKIP_SYS'
DELETE_SOFT_SYS = 'DELETE_SOFT_SYS'
DELETE_FORCE_SKIP_SYS = 'DELETE_FORCE_SKIP_SYS'
DELETE_FORCE_SYS = 'DELETE_FORCE_SYS'

class Data():
	driver = None
	
	@classmethod
	def create_conn(self):
		return self.driver.create_conn()

	@classmethod
	def read(self, env, session, collection, attrs, extns, modules, query):
		return self.driver.read(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, query=query)
	
	@classmethod
	def create(self, env, session, collection, attrs, extns, modules, doc):
		doc = self.sanitise_attrs(doc)
		return self.driver.create(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, doc=doc)
	
	@classmethod
	def update(self, env, session, collection, attrs, extns, modules, docs, doc):
		doc = self.sanitise_attrs(doc)
		return self.driver.update(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, docs=docs, doc=doc)
	
	@classmethod
	def delete(self, env, session, collection, attrs, extns, modules, docs, strategy):
		return self.driver.delete(env=env, session=session, collection=collection, attrs=attrs, extns=extns, modules=modules, docs=docs, strategy=strategy)

	@classmethod
	def drop(self, env, session, collection):
		return self.driver.drop(env=env, session=session, collection=collection)
	
	@classmethod
	def sanitise_attrs(self, attrs):
		if type(attrs) == dict:
			iter = attrs.keys()
			for attr in iter:
				if type(attrs[attr]) == dict:
					attrs[attr] = self.sanitise_attrs(attrs[attr])
				elif type(attrs[attr]) == list:
					attrs[attr] = self.sanitise_attrs(attrs[attr])
				elif isinstance(attrs[attr], BaseModel):
					attrs[attr] = attrs[attr]._id
		return attrs