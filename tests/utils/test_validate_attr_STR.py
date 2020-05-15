from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_STR_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_STR',
			attr_type=ATTR.STR(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_STR_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_STR',
			attr_type=ATTR.STR(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_STR_str():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_STR',
		attr_type=ATTR.STR(),
		attr_val='test_validate_attr_STR',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_STR'


@pytest.mark.asyncio
async def test_validate_attr_STR_pattern_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_STR',
			attr_type=ATTR.STR(pattern=r'[a-z_]+'),
			attr_val='test_validate_attr_STR',
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_STR_pattern_str():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_STR',
		attr_type=ATTR.STR(pattern=r'[a-zA-Z_]+'),
		attr_val='test_validate_attr_STR',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_STR'


@pytest.mark.asyncio
async def test_validate_attr_STR_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_STR',
		attr_type=ATTR.STR(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_STR_default_None():
	attr_type = ATTR.STR()
	attr_type._default = 'test_validate_attr_STR'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_STR',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_STR'


@pytest.mark.asyncio
async def test_validate_attr_STR_default_int():
	attr_type = ATTR.STR()
	attr_type._default = 'test_validate_attr_STR'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_STR',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_STR'


@pytest.mark.asyncio
async def test_validate_attr_STR_default_int_allow_none():
	attr_type = ATTR.STR()
	attr_type._default = 'test_validate_attr_STR'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_STR',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None