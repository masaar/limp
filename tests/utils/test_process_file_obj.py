from limp.utils import process_file_obj

from bson import ObjectId

import pytest


@pytest.mark.asyncio
async def test_process_file_obj(mock_module, mock_call_results):
	modules = {
		'file': mock_module(
			read=mock_call_results(
				status=200, count=1, doc={
					'_id': ObjectId(),
					'file': {
						'name': 'test_process_file_obj',
						# ... rest of FILE attrs
					}
				}
			),
			delete=mock_call_results(status=200, count=1),
		)
	}

	doc = {
		'file': {'__file': '000000000000000000000000'},
	}

	await process_file_obj(doc=doc, modules=modules, env={})

	assert doc['file']['name'] == 'test_process_file_obj'


@pytest.mark.asyncio
async def test_process_file_obj_invalid(mock_module):
	modules = {'file': mock_module()}

	doc = {
		'file': {'__file': '000000000000000000000000'},
	}

	await process_file_obj(doc=doc, modules=modules, env={})

	assert doc['file'] == None
