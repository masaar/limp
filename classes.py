from enums import Event, LIMP_VALUES

from typing import (
	Union,
	List,
	Tuple,
	Set,
	Dict,
	Literal,
	TypedDict,
	Any,
	Callable,
	Type,
	ForwardRef,
)
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId, binary
from aiohttp.web import WebSocketResponse

import logging, re, datetime, time, json, copy
from dataclasses import dataclass, field

logger = logging.getLogger('limp')

LIMP_EVENTS = List[Event]
LIMP_ENV = TypedDict(
	'LIMP_ENV',
	conn=AsyncIOMotorClient,
	REMOTE_ADDR=str,
	HTTP_USER_AGENT=str,
	client_app=str,
	session='BaseModel',
	ws=WebSocketResponse,
	watch_tasks=Dict[str, Dict[Literal['watch', 'task'], Callable]],
)
LIMP_QUERY = List[
	Union[
		'LIMP_QUERY',
		Union[
			Dict[
				str,
				Union[
					'LIMP_QUERY',
					Any,
					Union[
						Dict[Literal['$ne'], Any],
						Dict[Literal['$eq'], Any],
						Dict[Literal['$gt'], Union[int, str]],
						Dict[Literal['$gte'], Union[int, str]],
						Dict[Literal['$lt'], Union[int, str]],
						Dict[Literal['$lte'], Union[int, str]],
						Dict[Literal['$bet'], Union[List[int], List[str]]],
						Dict[Literal['$all'], List[Any]],
						Dict[Literal['$in'], List[Any]],
						Dict[Literal['$regex'], str],
					],
				],
			],
			Dict[Literal['$search'], str],
			Dict[Literal['$sort'], Dict[str, Literal[1, -1]]],
			Dict[Literal['$skip'], int],
			Dict[Literal['$limit'], int],
			Dict[Literal['$extn'], Union[Literal[False], List[str]]],
			Dict[Literal['$attrs'], List[str]],
			Dict[
				Literal['$group'],
				List[TypedDict('LIMP_QUERY_GROUP', by=str, count=int)],
			],
		],
	]
]
LIMP_DOC = Dict[
	str,
	Union[
		Dict[
			str,
			Union[
				Dict[Literal['$add', '$multiply'], int],
				Dict[Literal['$append', '$remove'], Any],
				Any,
			],
		],
		Any,
	],
]


ATTRS_TYPES: Dict[str, Dict[str, Type]] = {
	'ANY': {},
	'ACCESS': {},
	'ID': {},
	'STR': {'pattern': str},
	'INT': {'ranges': List[List[int]]},
	'FLOAT': {'ranges': List[List[float]]},
	'BOOL': {},
	'LOCALE': {},
	'LOCALES': {},
	'EMAIL': {'allowed_domains': List[str], 'disallowed_domains': List[str]},
	'PHONE': {'codes': List[str]},
	'IP': {},
	'URI_WEB': {'allowed_domains': List[str], 'disallowed_domains': List[str]},
	'DATETIME': {'ranges': List[List[datetime.datetime]]},
	'DATE': {'ranges': List[List[datetime.date]]},
	'TIME': {'ranges': List[List[datetime.time]]},
	'FILE': {
		'types': List[str],
		'max_ratio': List[int],
		'min_ratio': List[int],
		'max_dims': List[int],
		'min_dims': List[int],
		'max_size': int,
	},
	'GEO': {},
	'LIST': {'list': List['ATTR'], 'min': int, 'max': int},
	'DICT': {'dict': Dict[str, 'ATTR']},
	'LITERAL': {'literal': List[Union[str, int, float, bool]]},
	'UNION': {'union': List['ATTR']},
	'TYPE': {'type': str},
}


class L10N(dict):
	pass


class LIMP_MODULE:
	collection: Union[str, bool]
	proxy: str
	attrs: Dict[str, 'ATTR']
	diff: Union[bool, 'ATTR_MOD']
	defaults: Dict[str, Any]
	unique_attrs: List[str]
	extns: Dict[str, 'EXTN']
	privileges: List[str]
	methods: TypedDict(
		'METHODS',
		permissions=List['PERM'],
		query_args=Dict[str, Union['ATTR', 'ATTR_MOD']],
		doc_args=Dict[str, Union['ATTR', 'ATTR_MOD']],
		get_method=bool,
		post_method=bool,
		watch_method=bool,
	)
	cache: List['CACHE']
	analytics: List['ANALYTIC']
	package_name: str
	module_name: str

	async def pre_read(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, 'Query'], LIMP_DOC, Dict[str, Any]
	]:
		pass

	async def on_read(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, 'Query'],
		LIMP_DOC,
		Dict[str, Any],
	]:
		pass

	async def read(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, 'Query'] = [],
		doc: LIMP_DOC = {},
	) -> 'DictObj':
		pass

	async def pre_create(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, 'Query'], LIMP_DOC, Dict[str, Any]
	]:
		pass

	async def on_create(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, 'Query'],
		LIMP_DOC,
		Dict[str, Any],
	]:
		pass

	async def create(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, 'Query'] = [],
		doc: LIMP_DOC = {},
	) -> 'DictObj':
		pass

	async def pre_update(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, 'Query'], LIMP_DOC, Dict[str, Any]
	]:
		pass

	async def on_update(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, 'Query'],
		LIMP_DOC,
		Dict[str, Any],
	]:
		pass

	async def update(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, 'Query'] = [],
		doc: LIMP_DOC = {},
	) -> 'DictObj':
		pass

	async def pre_delete(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, 'Query'], LIMP_DOC, Dict[str, Any]
	]:
		pass

	async def on_delete(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, 'Query'],
		LIMP_DOC,
		Dict[str, Any],
	]:
		pass

	async def delete(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, 'Query'] = [],
		doc: LIMP_DOC = {},
	) -> 'DictObj':
		pass

	async def pre_create_file(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, 'Query'], LIMP_DOC, Dict[str, Any]
	]:
		pass

	async def on_create_file(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, 'Query'],
		LIMP_DOC,
		Dict[str, Any],
	]:
		pass

	async def create_file(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, 'Query'] = [],
		doc: LIMP_DOC = {},
	) -> 'DictObj':
		pass

	async def pre_delete_file(
		self,
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		LIMP_EVENTS, LIMP_ENV, Union[LIMP_QUERY, 'Query'], LIMP_DOC, Dict[str, Any]
	]:
		pass

	async def on_delete_file(
		self,
		results: Dict[str, Any],
		skip_events: LIMP_EVENTS,
		env: LIMP_ENV,
		query: Union[LIMP_QUERY, 'Query'],
		doc: LIMP_DOC,
		payload: Dict[str, Any],
	) -> Tuple[
		Dict[str, Any],
		LIMP_EVENTS,
		LIMP_ENV,
		Union[LIMP_QUERY, 'Query'],
		LIMP_DOC,
		Dict[str, Any],
	]:
		pass

	async def delete_file(
		self,
		skip_events: LIMP_EVENTS = [],
		env: LIMP_ENV = {},
		query: Union[LIMP_QUERY, 'Query'] = [],
		doc: LIMP_DOC = {},
	) -> 'DictObj':
		pass


class InvalidAttrTypeException(Exception):
	def __init__(self, *, attr_type: str):
		self.attr_type = attr_type

	def __str__(self):
		return f'Unkown or invalid Attr Type \'{self.attr_type}\'.'


class InvalidAttrTypeArgException(Exception):
	def __init__(self, *, arg_name: str, arg_type: Any, arg_val: Any):
		self.arg_name = arg_name
		self.arg_type = arg_type
		self.arg_val = arg_val

	def __str__(self):
		return f'Invalid Attr Type Arg for \'{self.arg_name}\' expecting type \'{self.arg_type}\' but got \'{self.arg_val}\'.'


class ATTR:
	_type: Literal[
		'ANY',
		'ACCESS',
		'ID',
		'STR',
		'INT',
		'FLOAT',
		'BOOL',
		'LOCALE',
		'LOCALES',
		'EMAIL',
		'PHONE',
		'IP',
		'URI_WEB',
		'DATETIME',
		'DATE',
		'TIME',
		'FILE',
		'GEO',
		'LIST',
		'DICT',
		'LITERAL',
		'UNION',
		'TYPE',
	]
	_desc: str
	_args: Dict[str, Any]
	_valid: bool = False
	_extn: Union['EXTN', 'ATTR_MOD'] = None

	__default = LIMP_VALUES.NONE_VALUE

	@property
	def _default(self):
		if self.__default == '$__datetime':
			return datetime.datetime.utcnow().isoformat()
		elif self.__default == '$__date':
			return datetime.date.today().isoformat()
		elif self.__default == '$__time':
			return datetime.datetime.now().time().isoformat()
		else:
			return self.__default

	@_default.setter
	def _default(self, value):
		self.__default = value

	def __repr__(self):
		return f'<ATTR:{self._type},{self._args}>'

	def __init__(self, *, attr_type: str, desc: str = None, **kwargs: Dict[str, Any]):
		self._type = attr_type
		self._desc = desc
		self._args = kwargs
		ATTR.validate_type(attr_type=self, skip_type=True)

	@classmethod
	def ANY(cls, *, desc: str = None):
		return ATTR(attr_type='ANY', desc=desc)

	@classmethod
	def ACCESS(cls, *, desc: str = None):
		return ATTR(attr_type='ACCESS', desc=desc)

	@classmethod
	def ID(cls, *, desc: str = None):
		return ATTR(attr_type='ID', desc=desc)

	@classmethod
	def STR(cls, *, desc: str = None, pattern: str = None):
		return ATTR(attr_type='STR', desc=desc, pattern=pattern)

	@classmethod
	def INT(cls, *, desc: str = None, ranges: List[List[int]] = None):
		return ATTR(attr_type='INT', desc=desc, ranges=ranges)

	@classmethod
	def FLOAT(cls, *, desc: str = None, ranges: List[List[int]] = None):
		return ATTR(attr_type='FLOAT', desc=desc, ranges=ranges)

	@classmethod
	def BOOL(cls, *, desc: str = None):
		return ATTR(attr_type='BOOL', desc=desc)

	@classmethod
	def LOCALE(cls, *, desc: str = None):
		return ATTR(attr_type='LOCALE', desc=desc)

	@classmethod
	def LOCALES(cls, *, desc: str = None):
		return ATTR(attr_type='LOCALES', desc=desc)

	@classmethod
	def EMAIL(
		cls,
		*,
		desc: str = None,
		allowed_domains: List[str] = None,
		disallowed_domains: List[str] = None,
	):
		return ATTR(
			attr_type='EMAIL',
			desc=desc,
			allowed_domains=allowed_domains,
			disallowed_domains=disallowed_domains,
		)

	@classmethod
	def PHONE(cls, *, desc: str = None, codes: List[str] = None):
		return ATTR(attr_type='PHONE', desc=desc, codes=codes)

	@classmethod
	def IP(cls, *, desc: str = None):
		return ATTR(attr_type='IP', desc=desc)

	@classmethod
	def URI_WEB(
		cls,
		*,
		desc: str = None,
		allowed_domains: List[str] = None,
		disallowed_domains: List[str] = None,
	):
		return ATTR(
			attr_type='URI_WEB',
			desc=desc,
			allowed_domains=allowed_domains,
			disallowed_domains=disallowed_domains,
		)

	@classmethod
	def DATETIME(cls, *, desc: str = None, ranges: List[List[str]] = None):
		return ATTR(attr_type='DATETIME', desc=desc, ranges=ranges)

	@classmethod
	def DATE(cls, *, desc: str = None, ranges: List[List[str]] = None):
		return ATTR(attr_type='DATE', desc=desc, ranges=ranges)

	@classmethod
	def TIME(cls, *, desc: str = None, ranges: List[List[str]] = None):
		return ATTR(attr_type='TIME', desc=desc, ranges=ranges)

	@classmethod
	def FILE(
		cls,
		*,
		desc: str = None,
		types: List[str] = None,
		max_ratio: List[int] = None,
		min_ratio: List[int] = None,
		max_dims: List[int] = None,
		min_dims: List[int] = None,
		max_size: int = None,
	):
		return ATTR(
			attr_type='FILE',
			desc=desc,
			types=types,
			max_ratio=max_ratio,
			min_ratio=min_ratio,
			max_dims=max_dims,
			min_dims=min_dims,
			max_size=max_size,
		)

	@classmethod
	def GEO(cls, *, desc: str = None):
		return ATTR(attr_type='GEO', desc=desc)

	@classmethod
	def LIST(
		cls, *, desc: str = None, list: List['ATTR'], min: int = None, max: int = None,
	):
		return ATTR(attr_type='LIST', desc=desc, list=list, min=min, max=max)

	@classmethod
	def DICT(cls, *, desc: str = None, dict: Dict[str, 'ATTR']):
		return ATTR(attr_type='DICT', desc=desc, dict=dict)

	@classmethod
	def LITERAL(cls, *, desc: str = None, literal: List[Union[str, int, float, bool]]):
		return ATTR(attr_type='LITERAL', desc=desc, literal=literal)

	@classmethod
	def UNION(cls, *, desc: str = None, union: List['ATTR']):
		return ATTR(attr_type='UNION', desc=desc, union=union)

	@classmethod
	def TYPE(cls, *, desc: str = None, type: str):
		return ATTR(attr_type='TYPE', desc=desc, type=type)

	@classmethod
	def validate_type(cls, *, attr_type: 'ATTR', skip_type: bool = False):
		from config import Config

		if type(attr_type) != ATTR:
			raise InvalidAttrTypeException(attr_type=attr_type)

		if attr_type._valid:
			return

		if attr_type._type not in [
			'ANY',
			'ACCESS',
			'ID',
			'STR',
			'INT',
			'FLOAT',
			'BOOL',
			'LOCALE',
			'LOCALES',
			'EMAIL',
			'PHONE',
			'IP',
			'URI_WEB',
			'DATETIME',
			'DATE',
			'TIME',
			'FILE',
			'GEO',
			'LIST',
			'DICT',
			'LITERAL',
			'UNION',
			'TYPE',
		]:
			raise InvalidAttrTypeException(attr_type=attr_type)
		elif (
			not skip_type
			and attr_type._type == 'TYPE'
			and attr_type._args['type'] not in Config.types.keys()
		):
			raise InvalidAttrTypeException(attr_type=attr_type)
		elif attr_type._type != 'TYPE':
			for arg in ATTRS_TYPES[attr_type._type].keys():
				if (
					arg in ['list', 'dict', 'literal', 'union', 'type']
					and arg not in attr_type._args.keys()
				):
					raise InvalidAttrTypeArgException(
						arg_name=arg,
						arg_type=ATTRS_TYPES[attr_type._type][arg],
						arg_val=attr_type._args[arg],
					)
				elif arg in attr_type._args.keys() and attr_type._args[arg]:
					cls.validate_arg(
						arg_name=arg,
						arg_type=ATTRS_TYPES[attr_type._type][arg],
						arg_val=attr_type._args[arg],
					)
				else:
					attr_type._args[arg] = None
			attr_type._valid = True

	@classmethod
	def validate_arg(cls, *, arg_name: str, arg_type: Any, arg_val: Any):
		if arg_type == str:
			if type(arg_val) != str:
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			return
		elif arg_type == int:
			if type(arg_val) != int:
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			return
		elif arg_type == float:
			if type(arg_val) not in [float, int]:
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			return
		elif type(arg_type) == ForwardRef:
			if type(arg_val) != ATTR:
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			return
		elif arg_name == 'literal':
			if type(arg_val) != list:
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			for arg_val_child in arg_val:
				if type(arg_val_child) not in arg_type.__args__[0].__args__:
					raise InvalidAttrTypeArgException(
						arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
					)
			return
		elif arg_name == 'union':
			if type(arg_val) != list:
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			for arg_val_child in arg_val:
				if type(arg_val_child) != ATTR:
					raise InvalidAttrTypeArgException(
						arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
					)
			return
		elif arg_type == datetime.date:
			if not re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', arg_val) and not re.match(r'^[\-\+][0-9]+[dsmhw]$', arg_val):
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			return
		elif arg_type == datetime.datetime:
			if not re.match(
				r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]{6})?)?$',
				arg_val,
			) and not re.match(r'^[\-\+][0-9]+[dsmhw]$', arg_val):
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			return
		elif arg_type == datetime.time:
			if not re.match(r'^[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]{6})?)?$', arg_val) and not re.match(r'^[\-\+][0-9]+[dsmhw]$', arg_val):
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			return
		elif arg_type._name == 'List':
			if type(arg_val) != list:
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			for arg_val_child in arg_val:
				cls.validate_arg(
					arg_name=arg_name,
					arg_type=arg_type.__args__[0],
					arg_val=arg_val_child,
				)
			return
		elif arg_type._name == 'Dict':
			if type(arg_val) != dict:
				raise InvalidAttrTypeArgException(
					arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
				)
			else:
				if '__key' in arg_val.keys():
					if arg_val['__key']._type not in ['STR', 'LITERAL']:
						raise InvalidAttrTypeArgException(
							arg_name=f'{arg_name}.__key',
							arg_type=['STR', 'LITERAL'],
							arg_val=arg_val['__key']._type,
						)
			return

		raise InvalidAttrTypeArgException(
			arg_name=arg_name, arg_type=arg_type, arg_val=arg_val
		)


class ATTR_MOD:
	condition: Callable
	default: Union[Callable, Any]

	def __repr__(self):
		return f'<ATTR_MOD:{self.condition},{self.default}>'

	def __init__(
		self,
		*,
		condition: Callable[[List[str], Dict[str, Any], 'Query', LIMP_DOC], bool],
		default: Union[
			Callable[[List[str], Dict[str, Any], 'Query', LIMP_DOC], Any], Any
		],
	):
		self.condition = condition
		self.default = default


class PERM:
	privilege: str
	query_mod: Union[LIMP_DOC, List[LIMP_DOC]]
	doc_mod: Union[LIMP_DOC, List[LIMP_DOC]]

	def __repr__(self):
		return f'<PERM:{self.privilege},{self.query_mod},{self.doc_mod}>'

	def __init__(
		self,
		*,
		privilege: str,
		query_mod: Union[LIMP_DOC, List[LIMP_DOC]] = None,
		doc_mod: Union[LIMP_DOC, List[LIMP_DOC]] = None,
	):
		if not query_mod:
			query_mod = {}
		if not doc_mod:
			doc_mod = {}
		self.privilege = privilege
		self.query_mod = query_mod
		self.doc_mod = doc_mod


class EXTN:
	module: str
	attrs: List[str]
	force: bool = False

	def __repr__(self):
		return f'<EXTN:{self.module},{self.attrs},{self.force}>'

	def __init__(self, *, module: str, attrs: List[str] = None, force: bool = False):
		if not attrs:
			attrs = ['*']
		self.module = module
		self.attrs = attrs
		self.force = force


class CACHE:
	condition: Callable[[List[str], Dict[str, Any], Union['Query', LIMP_QUERY]], bool]
	period: int
	queries: Dict[str, 'CACHED_QUERY']

	def __repr__(self):
		return f'<CACHE:{self.condition},{self.period}>'

	def __init__(
		self,
		*,
		condition: Callable[
			[List[str], Dict[str, Any], Union['Query', LIMP_QUERY]], bool
		],
		period: int = None,
	):
		self.condition = condition
		self.period = period
		self.queries = {}

	def cache_query(self, *, query_key: str, results: 'DictObj'):
		self.queries[query_key] = CACHED_QUERY(results=results)


class CACHED_QUERY:
	results: 'DictObj'
	query_time: datetime.datetime

	def __init__(self, *, results: 'DictObj', query_time: datetime.datetime = None):
		self.results = results
		if not query_time:
			query_time = datetime.datetime.utcnow()
		self.query_time = query_time


class ANALYTIC:
	condition: Callable[
		[List[str], Dict[str, Any], Union['Query', LIMP_QUERY], LIMP_DOC], bool
	]
	doc: Callable[
		[List[str], Dict[str, Any], Union['Query', LIMP_QUERY], LIMP_DOC], LIMP_DOC
	]

	def __init__(
		self,
		*,
		condition: Callable[
			[List[str], Dict[str, Any], Union['Query', LIMP_QUERY], LIMP_DOC], bool
		],
		doc: Callable[
			[List[str], Dict[str, Any], Union['Query', LIMP_QUERY], LIMP_DOC], LIMP_DOC
		],
	):
		self.condition = condition
		self.doc = doc


@dataclass
class CONFIG:
	envs: Dict[str, 'CONFIG'] = None
	api_level: str = None
	packages_versions: Dict[str, str] = None
	emulate_test: bool = None
	realm: bool = None
	vars: Dict[str, Any] = None
	client_apps: Dict[
		str,
		TypedDict(
			'CLIENT_APP',
			name=str,
			type=Literal['web', 'ios', 'android'],
			origin=List[str],
			hash=str,
		),
	] = None
	analytics_events: TypedDict(
		'ANALYTICS_EVENTS',
		app_conn_verified=bool,
		session_conn_auth=bool,
		session_user_auth=bool,
		session_conn_reauth=bool,
		session_user_reauth=bool,
		session_conn_deauth=bool,
		session_user_deauth=bool,
	) = None
	conn_timeout: int = None
	quota_anon_min: int = None
	quota_auth_min: int = None
	quota_ip_min: int = None
	data_server: str = None
	data_name: str = None
	data_ssl: bool = None
	data_ca_name: str = None
	data_ca: str = None
	data_disk_use: bool = None
	data_azure_mongo: bool = None
	email_auth: Dict[str, str] = None
	locales: List[str] = None
	locale: str = None
	admin_doc: LIMP_DOC = None
	admin_password: str = None
	anon_token: str = None
	anon_privileges: Dict[str, List[str]] = None
	user_attrs: Dict[str, 'ATTRS_TYPES'] = None
	user_auth_attrs: List[str] = None
	user_attrs_defaults: Dict[str, Any] = None
	user_settings: Dict[
		str, Dict[Literal['type', 'val'], Union[Literal['user', 'user_sys'], Any]]
	] = None
	user_doc_settings: List[str] = None
	groups: List[Dict[str, Any]] = None
	default_privileges: Dict[str, List[str]] = None
	data_indexes: List[Dict[str, Any]] = None
	docs: List[Dict[str, Any]] = None
	jobs: List[Dict[str, Any]] = None
	gateways: Dict[str, Callable] = None
	types: Dict[str, Callable] = None


class JSONEncoder(json.JSONEncoder):
	def default(self, o):  # pylint: disable=E0202
		if isinstance(o, ObjectId):
			return str(o)
		elif isinstance(o, BaseModel) or isinstance(o, DictObj):
			return o._attrs()
		elif type(o) == datetime.datetime:
			return o.isoformat()
		elif type(o) == bytes:
			return True
		try:
			return json.JSONEncoder.default(self, o)
		except TypeError:
			return str(o)


class DictObj:
	__attrs = {}

	def __repr__(self):
		return f'<DictObj:{self.__attrs}>'

	def __init__(self, attrs):
		if type(attrs) == DictObj:
			attrs = attrs._attrs()
		elif type(attrs) != dict:
			raise TypeError(
				f'DictObj can be initilised using DictObj or dict types only. Got \'{type(attrs)}\' instead.'
			)
		self.__attrs = attrs

	def __deepcopy__(self, memo):
		return DictObj(copy.deepcopy(self.__attrs))

	def __getattr__(self, attr):
		return self.__attrs[attr]

	def __setattr__(self, attr, val):
		if not attr.endswith('__attrs'):
			raise AttributeError(
				f'Can\'t assign to DictObj attr \'{attr}\' using __setattr__. Use __setitem__ instead.'
			)
		object.__setattr__(self, attr, val)

	def __getitem__(self, attr):
		try:
			return self.__attrs[attr]
		except Exception as e:
			logger.debug(f'Unable to __getitem__ {attr} of {self.__attrs.keys()}.')
			raise e

	def __setitem__(self, attr, val):
		self.__attrs[attr] = val

	def __delitem__(self, attr):
		del self.__attrs[attr]

	def __contains__(self, attr):
		return attr in self.__attrs.keys()

	def _attrs(self):
		return copy.deepcopy(self.__attrs)


class BaseModel(DictObj):
	def __repr__(self):
		return f'<Model:{str(self._id)}>'

	def __init__(self, attrs):
		for attr in attrs.keys():
			if type(attrs[attr]) == dict and '_id' in attrs[attr].keys():
				attrs[attr] = BaseModel(attrs[attr])
		super().__init__(attrs)


class InvalidQueryArgException(Exception):
	def __init__(
		self,
		*,
		arg_name: str,
		arg_oper: Literal[
			'$ne',
			'$eq',
			'$gt',
			'$gte',
			'$lt',
			'$lte',
			'$bet',
			'$all',
			'$in',
			'$nin',
			'$regex',
		],
		arg_type: Any,
		arg_val: Any,
	):
		self.arg_name = arg_name
		self.arg_oper = arg_oper
		self.arg_type = arg_type
		self.arg_val = arg_val

	def __str__(self):
		return f'Invalid value for Query Arg \'{self.arg_name}\' with Query Arg Oper \'{self.arg_oper}\' expecting type \'{self.arg_type}\' but got \'{self.arg_val}\'.'


class UnknownQueryArgException(Exception):
	def __init__(
		self,
		*,
		arg_name: str,
		arg_oper: Literal[
			'$ne',
			'$eq',
			'$gt',
			'$gte',
			'$lt',
			'$lte',
			'$bet',
			'$all',
			'$in',
			'$nin',
			'$regex',
		],
	):
		self.arg_name = arg_name
		self.arg_oper = arg_oper

	def __str__(self):
		return f'Unknown Query Arg Oper \'{self.arg_oper}\' for Query Arg \'{self.arg_name}\'.'


class Query(list):
	def __init__(self, query: Union[LIMP_QUERY, 'Query']):
		self._query = query
		if type(self._query) == Query:
			self._query = query._query + [query._special]
		self._special = {}
		self._index = {}
		self._create_index(self._query)
		super().__init__(self._query)

	def __repr__(self):
		return str(self._query + [self._special])

	def _create_index(self, query: LIMP_QUERY, path=[]):
		if not path:
			self._index = {}
		for i in range(len(query)):
			if type(query[i]) == dict:
				del_attrs = []
				for attr in query[i].keys():
					if attr[0] == '$':
						self._special[attr] = query[i][attr]
						del_attrs.append(attr)
					elif attr.startswith('__or'):
						self._create_index(query[i][attr], path=path + [i, attr])
					else:
						if (
							type(query[i][attr]) == dict
							and len(query[i][attr].keys()) == 1
							and list(query[i][attr].keys())[0][0] == '$'
						):
							attr_oper = list(query[i][attr].keys())[0]
						else:
							attr_oper = '$eq'
						if attr not in self._index.keys():
							self._index[attr] = []
						if isinstance(query[i][attr], DictObj):
							query[i][attr] = query[i][attr]._id
						Query.validate_arg(
							arg_name=attr, arg_oper=attr_oper, arg_val=query[i][attr]
						)
						self._index[attr].append(
							{
								'oper': attr_oper,
								'path': path + [i],
								'val': query[i][attr],
							}
						)
				for attr in del_attrs:
					del query[i][attr]
			elif type(query[i]) == list:
				self._create_index(query[i], path=path + [i])
		if not path:
			self._query = self._sanitise_query()

	def _sanitise_query(self, query: LIMP_QUERY = None):
		if query == None:
			query = self._query
		query_shadow = []
		for step in query:
			if type(step) == dict:
				for attr in step.keys():
					if attr.startswith('__or'):
						step[attr] = self._sanitise_query(step[attr])
						if len(step[attr]):
							query_shadow.append(step)
							break
					elif attr[0] != '$':
						query_shadow.append(step)
						break
			elif type(step) == list:
				step = self._sanitise_query(step)
				if len(step):
					query_shadow.append(step)
		return query_shadow

	def __deepcopy__(self, memo):
		return Query(copy.deepcopy(self._query + [self._special]))

	def append(self, obj: Any):
		self._query.append(obj)
		self._create_index(self._query)
		super().__init__(self._query)

	def __contains__(self, attr: str):
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

	def __getitem__(self, attr: str):
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
				if attr_filter and index_attr != attr_filter:
					continue

				attrs += [
					index_attr
					for val in self._index[index_attr]
					if not oper_filter or (oper_filter and val['oper'] == oper_filter)
				]
				vals += [
					val['val']
					for val in self._index[index_attr]
					if not oper_filter or (oper_filter and val['oper'] == oper_filter)
				]
				paths += [
					val['path']
					for val in self._index[index_attr]
					if not oper_filter or (oper_filter and val['oper'] == oper_filter)
				]
				indexes += [
					i
					for i in range(len(self._index[index_attr]))
					if not oper_filter
					or (
						oper_filter
						and self._index[index_attr][i]['oper'] == oper_filter
					)
				]
			return QueryAttrList(self, attrs, paths, indexes, vals)

	def __setitem__(self, attr: str, val: Any):
		if attr[0] != '$':
			raise Exception('Non-special attrs can only be updated by attr index.')
		self._special[attr] = val

	def __delitem__(self, attr: str):
		if attr[0] != '$':
			raise Exception('Non-special attrs can only be deleted by attr index.')
		del self._special[attr]

	@classmethod
	def validate_arg(cls, *, arg_name, arg_oper, arg_val):
		if arg_oper in ['$ne', '$eq']:
			return
		elif arg_oper in ['$gt', '$gte', '$lt', '$lte']:
			if type(arg_val[arg_oper]) not in [str, int, float]:
				raise InvalidQueryArgException(
					arg_name=arg_name,
					arg_oper=arg_oper,
					arg_type=[str, int, float],
					arg_val=arg_val[arg_oper],
				)
		elif arg_oper == '$bet':
			if (
				type(arg_val[arg_oper]) != list
				or len(arg_val[arg_oper]) != 2
				or type(arg_val[arg_oper][0]) not in [str, int, float]
				or type(arg_val[arg_oper][1]) not in [str, int, float]
			):
				raise InvalidQueryArgException(
					arg_name=arg_name,
					arg_oper=arg_oper,
					arg_type=list,
					arg_val=arg_val[arg_oper],
				)
		elif arg_oper in ['$all', '$in', '$nin']:
			if type(arg_val[arg_oper]) != list or not len(arg_val[arg_oper]):
				raise InvalidQueryArgException(
					arg_name=arg_name,
					arg_oper=arg_oper,
					arg_type=list,
					arg_val=arg_val[arg_oper],
				)
		elif arg_oper == '$regex':
			if type(arg_val[arg_oper]) != str:
				raise InvalidQueryArgException(
					arg_name=arg_name,
					arg_oper=arg_oper,
					arg_type=str,
					arg_val=arg_val[arg_oper],
				)
		else:
			raise UnknownQueryArgException(arg_name=arg_name, arg_oper=arg_oper)


class QueryAttrList(list):
	def __init__(
		self,
		query: Query,
		attrs: List[str],
		paths: List[List[int]],
		indexes: List[int],
		vals: List[Any],
	):
		self._query = query
		self._attrs = attrs
		self._paths = paths
		self._indexes = indexes
		self._vals = vals
		super().__init__(vals)

	def __setitem__(self, item: Union[Literal['*'], int], val: Any):
		if item == '*':
			for i in range(len(self._vals)):
				self.__setitem__(i, val)
		else:
			instance_attr = self._query._query
			for path_part in self._paths[item]:
				instance_attr = instance_attr[path_part]
			instance_attr[self._attrs[item].split(':')[0]] = val
			self._query._create_index(self._query._query)

	def __delitem__(self, item: Union[Literal['*'], int]):
		if item == '*':
			for i in range(len(self._vals)):
				self.__delitem__(i)
		else:
			instance_attr = self._query._query
			for path_part in self._paths[item]:
				instance_attr = instance_attr[path_part]
			del instance_attr[self._attrs[item].split(':')[0]]
			self._query._create_index(self._query._query)

	def replace_attr(self, item: Union[Literal['*'], int], new_attr: str):
		if item == '*':
			for i in range(len(self._vals)):
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

