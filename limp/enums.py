from enum import Enum, auto


class Event(Enum):
	ARGS = auto()
	VALIDATE = auto()
	PERM = auto()
	PRE = auto()
	ON = auto()
	EXTN = auto()
	SOFT = auto()
	DIFF = auto()
	SYS_DOCS = auto()


class DELETE_STRATEGY(Enum):
	SOFT_SKIP_SYS = auto()
	SOFT_SYS = auto()
	FORCE_SKIP_SYS = auto()
	FORCE_SYS = auto()


class LOCALE_STRATEGY(Enum):
	DUPLICATE = auto()
	NONE_VALUE = auto()


class LIMP_VALUES(Enum):
	NONE_VALUE = auto()
