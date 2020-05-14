from limp.base_module import BaseModule
from limp.enums import Event
from limp.classes import ATTR, PERM
from limp.config import Config
from limp.utils import extract_attr, validate_attr

from bson import ObjectId

import base64


class File(BaseModule):
	'''`File` module provides functionality for `File Upload Workflow`.'''

	collection = 'files'
	attrs = {
		'user': ATTR.ID(desc='`_id` of `User` doc file belongs to.'),
		'file': ATTR.FILE(desc='File object.'),
		'create_time': ATTR.DATETIME(
			desc='Python `datetime` ISO format of the doc creation.'
		),
	}
	methods = {
		'read': {'permissions': [PERM(privilege='__sys')]},
		'create': {'permissions': [PERM(privilege='create')], 'post_method': True,},
		'delete': {'permissions': [PERM(privilege='__sys')]},
	}

	async def on_read(self, results, skip_events, env, query, doc, payload):
		for i in range(len(results['docs'])):
			results['docs'][i]['file']['lastModified'] = int(
				results['docs'][i]['file']['lastModified']
			)
		return (results, skip_events, env, query, doc, payload)

	async def pre_create(self, skip_events, env, query, doc, payload):
		if (
			Config.file_upload_limit != -1
			and len(doc[b'file'][3]) > Config.file_upload_limit
		):
			return self.status(
				status=400,
				msg=f'File size is beyond allowed limit.',
				args={
					'code': 'INVALID_SIZE',
					'attr': doc[b'__attr'][3].decode('utf-8'),
					'name': doc[b'name'][3].decode('utf-8'),
				},
			)
		if (module := doc[b'__module'][3].decode('utf-8')) not in Config.modules.keys():
			return self.status(
				status=400,
				msg=f'Invalid module \'{module}\'',
				args={'code': 'INVALID_MODULE'},
			)
		try:
			attr_type = extract_attr(
				scope=Config.modules[module].attrs,
				attr_path='$__' + (attr := doc[b'__attr'][3].decode('utf-8')),
			)
			doc = {
				'file': {
					'name': doc[b'name'][3].decode('utf-8'),
					'type': doc[b'type'][3].decode('utf-8'),
					'size': len(doc[b'file'][3]),
					'lastModified': int(doc[b'lastModified'][3].decode('utf-8')),
					'content': doc[b'file'][3],
				},
			}
			try:
				validate_attr(attr_name=attr, attr_type=attr_type, attr_val=doc['file'])
			except:
				return self.status(
					status=400,
					msg=f'Invalid file for \'{attr}\' of module \'{module}\'',
					args={'code': 'INVALID_FILE'},
				)
		except:
			return self.status(
				status=400,
				msg=f'Invalid attr \'{attr}\' of module \'{module}\'',
				args={'code': 'INVALID_ATTR'},
			)
		return (skip_events, env, query, doc, payload)
