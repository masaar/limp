from limp.classes import DictObj

from dataclasses import dataclass
from typing import Dict, Any
from bson import ObjectId
from contextlib import contextmanager

import pytest, copy


@dataclass
class Module:
	_read: DictObj
	_create: DictObj
	_delete: DictObj
	_update: DictObj

	async def read(self, **kwargs):
		return self._read
	
	async def create(self, **kwargs):
		return self._create
	
	async def update(self, **kwargs):
		return self._update

	async def delete(self, **kwargs):
		return self._delete


@pytest.fixture
def mock_call_results():
	def _(status: int, count: int, doc: Dict[str, Any] = None, code: str = None):
		return DictObj({
			'status': status,
			'args': DictObj({
				'count': count,
				'code': code,
				'docs': [
					DictObj(doc if doc else {'_id': ObjectId()}) for __ in range(count)
				]
			})
		})

	return _


@pytest.fixture
def mock_module():
	def _(read: DictObj = None, create: DictObj = None, update: DictObj = None, delete: DictObj = None):
		return Module(
			_read=read,
			_create=create,
			_update=update,
			_delete=delete
		)

	return _


@pytest.fixture
def attr_obj():
	return {
		'item1': 'val1',
		'item2': 'val2',
		'list_item1': ['list_child1', 'list_child2', 'list_child3'],
		'dict_item1': {'dict_child1': 'child_val1', 'dict_child2': 'child_val2',},
		'nested_dict': {
			'child_item': 'child_val',
			'child_dict': {'child_child_item1': 'child_child_val1'},
		},
		'nested_list': [
			['child_child_item11', 'child_child_item12'],
			['child_child_item21', 'child_child_item22'],
		],
		'nested_obj': {
			'list': [{'item1': 'val1'}, {'item2': 'val2'}],
			'dict': {'list': ['item1', 'item2']},
		},
	}


@pytest.fixture
def preserve_state():
	@contextmanager
	def preserve_state_manager(module, state_name):
		state = getattr(module, state_name)
		state_attrs = {}
		for attr in dir(state):
			if not attr.startswith('__'):
				state_attrs[attr] = copy.deepcopy(getattr(state, attr))
		try:
			yield
		finally:
			for attr in dir(state):
				if not attr.startswith('__'):
					setattr(state, attr, state_attrs[attr])

	def _(module, state_name):
		return preserve_state_manager(module, state_name)

	return _