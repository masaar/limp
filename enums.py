from enum import Enum

class Event(Enum):
	__ARGS__ = '__ARGS__'
	__VALIDATE__ = '__VALIDATE__'
	__PERM__ = '__PERM__'
	__PRE__ = '__PRE__'
	__ON__ = '__ON__'
	__EXTN__ = '__EXTN__'
	__SOFT__ = '__SOFT__'
	__DIFF__ = '__DIFF__'
	__SYS_DOCS__ = '__SYS_DOCS__'

class DELETE_STRATEGY(Enum):
	SOFT_SKIP_SYS = 'DELETE_SOFT_SKIP_SYS'
	SOFT_SYS = 'DELETE_SOFT_SYS'
	FORCE_SKIP_SYS = 'DELETE_FORCE_SKIP_SYS'
	FORCE_SYS = 'DELETE_FORCE_SYS'

class LIMP_VALUES(Enum):
	NONE_VALUE = 'NONE_VALUE'