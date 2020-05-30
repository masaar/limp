from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_UNION_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_UNION',
			attr_type=ATTR.UNION(union=[ATTR.STR(), ATTR.INT()]),
			attr_val=None,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_UNION_float():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_UNION',
			attr_type=ATTR.UNION(union=[ATTR.STR(), ATTR.INT()]),
			attr_val=1.1,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_UNION_str():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=ATTR.UNION(union=[ATTR.STR(), ATTR.INT()]),
		attr_val='str',
		allow_update=False,
	)
	assert attr_val == 'str'


@pytest.mark.asyncio
async def test_validate_attr_UNION_int():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=ATTR.UNION(union=[ATTR.STR(), ATTR.INT()]),
		attr_val=1,
		allow_update=False,
	)
	assert attr_val == 1


@pytest.mark.asyncio
async def test_validate_attr_UNION_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=ATTR.UNION(union=[ATTR.STR(), ATTR.INT()]),
		attr_val=None,
		allow_update=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_UNION_default_None():
	attr_type = ATTR.UNION(union=[ATTR.STR(), ATTR.INT()])
	attr_type._default = 'test_validate_attr_UNION'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=attr_type,
		attr_val=None,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_UNION'


@pytest.mark.asyncio
async def test_validate_attr_UNION_default_float():
	attr_type = ATTR.UNION(union=[ATTR.STR(), ATTR.INT()])
	attr_type._default = 'test_validate_attr_UNION'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=attr_type,
		attr_val=1.1,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_UNION'


@pytest.mark.asyncio
async def test_validate_attr_UNION_default_float_allow_none():
	attr_type = ATTR.UNION(union=[ATTR.STR(), ATTR.INT()])
	attr_type._default = 'test_validate_attr_UNION'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=attr_type,
		attr_val=1.1,
		allow_update=True,
	)
	assert attr_val == None
