from base_module import BaseModule
from enums import Event
from classes import ATTR, PERM
from config import Config

from bson import ObjectId

import base64


class File(BaseModule):
	'''`File` module provides functionality for `File Upload Workflow`.'''
	collection = 'files'
	attrs = {
		'user': ATTR.ID(desc='`_id` of `User` doc file belongs to.'),
		'file': ATTR.FILE(desc='File object.'),
		'create_time': ATTR.DATETIME(desc='Python `datetime` ISO format of the doc creation.'),
	}
	methods = {
		'read': {'permissions': [PERM(privilege='__sys')]},
		'create': {
            'permissions': [PERM(privilege='*')],
            'post_method': True,
        },
		'delete': {'permissions': [PERM(privilege='__sys')]},
	}

	async def on_read(self, results, skip_events, env, query, doc, payload):
		for i in range(len(results['docs'])):
			results['docs'][i]['file']['lastModified'] = int(results['docs'][i]['file']['lastModified'])
		return (results, skip_events, env, query, doc, payload)

	async def pre_create(self, skip_events, env, query, doc, payload):
		file_content = doc[b'content'][3].decode('utf-8')
		file_content = base64.decodebytes(file_content[file_content.index('base64,')+7:].encode('utf-8'))
		doc = {
			'file': {
				'name': doc[b'name'][3].decode('utf-8'),
				'type': doc[b'type'][3].decode('utf-8'),
				'size': int(doc[b'size'][3].decode('utf-8')),
				'lastModified': int(doc[b'lastModified'][3].decode('utf-8')),
				'content': file_content,
			},
		}
		return (skip_events, env, query, doc, payload)

