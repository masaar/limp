from ....utils import process_file_obj

from dataclasses import dataclass
from typing import Any
import pytest

@pytest.mark.asyncio
async def test_process_file_obj(monkeypatch):
	@dataclass
	class Module:
		_read: Any
		_delete: Any
		async def read(self, **kwargs):
			return self._read
		async def delete(self, **kwargs):
			return self._delete

	@dataclass
	class FileResults:
		args: Any
		status: Any = 200
	
	@dataclass
	class FileResultsArgs:
		docs: Any
		count: Any = 1
	
	@dataclass
	class FileResultsArgsDoc:
		file: Any
	
	read_file_results = FileResults(args=FileResultsArgs(docs=[FileResultsArgsDoc(file={
		'name': 'test_process_file_obj'
		# ... more FILE Attr Type specific items
	})]))

	delete_file_results = FileResults(args=FileResultsArgs(docs=None))

	modules = {
		'file': Module(_read=read_file_results, _delete=delete_file_results)
	}

	doc = {
		'file': {'__file': '000000000000000000000000'},
	}

	await process_file_obj(doc=doc, modules=modules, env={})

	assert doc['file']['name'] == 'test_process_file_obj'


@pytest.mark.asyncio
async def test_process_file_obj_invalid(monkeypatch):
	@dataclass
	class Module:
		_read: Any
		_delete: Any
		async def read(self, **kwargs):
			return self._read
		async def delete(self, **kwargs):
			return self._delete

	modules = {
		'file': Module(_read=None, _delete=None)
	}

	doc = {
		'file': {'__file': '000000000000000000000000'},
	}

	await process_file_obj(doc=doc, modules=modules, env={})

	assert doc['file'] == None