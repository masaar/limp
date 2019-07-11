from utils import DictObj

class BaseModel(DictObj):
	def __init__(self, attrs):
		for attr in attrs.keys():
			if type(attrs[attr]) == dict and '_id' in attrs[attr].keys():
				attrs[attr] = BaseModel(attrs[attr])
		super().__init__(attrs)
	
	def __str__(self):
		return '<Model:{}>'.format(str(self._id))