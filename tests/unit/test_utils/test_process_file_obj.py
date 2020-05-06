from limp.utils import process_file_obj

from .fixtures import Module, read_file_results, delete_file_results

import pytest


@pytest.mark.asyncio
async def test_process_file_obj(read_file_results, delete_file_results):
	modules = {'file': Module(_read=read_file_results, _delete=delete_file_results)}

	doc = {
		'file': {'__file': '000000000000000000000000'},
	}

	await process_file_obj(doc=doc, modules=modules, env={})

	assert doc['file']['name'] == 'test_process_file_obj'


@pytest.mark.asyncio
async def test_process_file_obj_invalid():
	modules = {'file': Module(_read=None, _delete=None)}

	doc = {
		'file': {'__file': '000000000000000000000000'},
	}

	await process_file_obj(doc=doc, modules=modules, env={})

	assert doc['file'] == None
