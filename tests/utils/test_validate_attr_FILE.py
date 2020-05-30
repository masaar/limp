from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_FILE_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_FILE',
			attr_type=ATTR.FILE(),
			attr_val=None,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_FILE_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_FILE',
			attr_type=ATTR.FILE(),
			attr_val=1,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_FILE_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_FILE',
			attr_type=ATTR.FILE(),
			attr_val={'key': 'value'},
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_FILE_file():
	file_attr_val = {
		'name': '__filename',
		'type': 'mime/type',
		'lastModified': 0,
		'size': 6,
		'content': b'__file',
	}
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=ATTR.FILE(),
		attr_val=file_attr_val,
		allow_update=False,
	)
	assert attr_val == file_attr_val


@pytest.mark.asyncio
async def test_validate_attr_FILE_file_list():
	file_attr_val = {
		'name': '__filename',
		'type': 'mime/type',
		'lastModified': 0,
		'size': 6,
		'content': b'__file',
	}
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=ATTR.FILE(),
		attr_val=[file_attr_val],
		allow_update=False,
	)
	assert attr_val == file_attr_val


@pytest.mark.asyncio
async def test_validate_attr_FILE_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=ATTR.FILE(),
		attr_val=None,
		allow_update=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_FILE_default_None():
	attr_type = ATTR.FILE()
	attr_type._default = 'test_validate_attr_FILE'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=attr_type,
		attr_val=None,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_FILE'


@pytest.mark.asyncio
async def test_validate_attr_FILE_default_int():
	attr_type = ATTR.FILE()
	attr_type._default = 'test_validate_attr_FILE'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=attr_type,
		attr_val=1,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_FILE'


@pytest.mark.asyncio
async def test_validate_attr_FILE_default_int_allow_none():
	attr_type = ATTR.FILE()
	attr_type._default = 'test_validate_attr_FILE'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=attr_type,
		attr_val=1,
		allow_update=True,
	)
	assert attr_val == None
