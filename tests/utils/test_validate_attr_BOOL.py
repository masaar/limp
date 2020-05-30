from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_BOOL_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_BOOL',
			attr_type=ATTR.BOOL(),
			attr_val=None,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_BOOL_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_BOOL',
			attr_type=ATTR.BOOL(),
			attr_val=1,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_BOOL_bool():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=ATTR.BOOL(),
		attr_val=False,
		allow_update=False,
	)
	assert attr_val == False


@pytest.mark.asyncio
async def test_validate_attr_BOOL_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=ATTR.BOOL(),
		attr_val=None,
		allow_update=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_BOOL_default_None():
	attr_type = ATTR.BOOL()
	attr_type._default = 'test_validate_attr_BOOL'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=attr_type,
		attr_val=None,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_BOOL'


@pytest.mark.asyncio
async def test_validate_attr_BOOL_default_int():
	attr_type = ATTR.STR()
	attr_type._default = 'test_validate_attr_BOOL'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=attr_type,
		attr_val=1,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_BOOL'


@pytest.mark.asyncio
async def test_validate_attr_BOOL_default_int_allow_none():
	attr_type = ATTR.STR()
	attr_type._default = 'test_validate_attr_BOOL'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=attr_type,
		attr_val=1,
		allow_update=True,
	)
	assert attr_val == None
