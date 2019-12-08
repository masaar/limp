from enum import Enum
from typing import Union, List, Tuple, Set, Dict, Literal, TypedDict, Any

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

LIMP_ATTR = Union[str, List['LIMP_ATTR'], Tuple['LIMP_ATTR'], Set[str], Dict[str, 'LIMP_ATTR']]
LIMP_ATTRS = Dict[str, LIMP_ATTR]
LIMP_QUERY = List[Union[
	'LIMP_QUERY', Union[
		Dict[str, Union['LIMP_QUERY', Any, Union[
			Dict[Literal['$not'], Any],
			Dict[Literal['$eq'], Any],
			Dict[Literal['$gt'], Union[int, str]],
			Dict[Literal['$gte'], Union[int, str]],
			Dict[Literal['$lt'], Union[int, str]],
			Dict[Literal['$lte'], Union[int, str]],
			Dict[Literal['$bet'], Union[List[int], List[str]]],
			Dict[Literal['$all'], List[Any]],
			Dict[Literal['$in'], List[Any]],
			Dict[Literal['$regex'], str]
		]]],
		Dict[Literal['$search'], str],
		Dict[Literal['$sort'], Dict[str, Literal[1, -1]]],
		Dict[Literal['$skip'], int],
		Dict[Literal['$limit'], int],
		Dict[Literal['$extn'], Union[Literal[False], List[str]]],
		Dict[Literal['$attrs'], List[str]],
		Dict[Literal['$group'], List[
			TypedDict('LIMP_QUERY_GROUP', by=str, count=int)
		]]
	]
]]
LIMP_DOC = Dict[str, Union[Dict[Literal['$add', '$push', '$push_unique', '$pull'], Any], Any]]