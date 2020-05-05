from dataclasses import dataclass

from typing import Dict, Any

import pytest


@dataclass
class Module:
	_read: 'Results'
	_delete: 'Results'

	async def read(self, **kwargs):
		return self._read

	async def delete(self, **kwargs):
		return self._delete


@dataclass
class Results:
	args: 'ResultsArgs'
	status: int = 200


@dataclass
class ResultsArgs:
	docs: 'ResultsArgsDoc'
	count: int = 1


@dataclass
class ResultsArgsDoc:
	file: Dict[str, Any]


@pytest.fixture
def read_file_results():
	return Results(
		args=ResultsArgs(
			docs=[
				ResultsArgsDoc(
					file={
						'name': 'test_process_file_obj'
						# ... more FILE Attr Type specific items
					}
				)
			]
		)
	)


@pytest.fixture
def delete_file_results():
	return Results(args=ResultsArgs(docs=None))


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
