from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_FLOAT',
			attr_type=ATTR.FLOAT(),
			attr_val=None,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_str():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_FLOAT',
			attr_type=ATTR.FLOAT(),
			attr_val='str',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_float():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(),
		attr_val=1.1,
		allow_update=False,
	)
	assert attr_val == 1.1


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_int():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(),
		attr_val=1,
		allow_update=False,
	)
	assert attr_val == 1


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_float_as_str():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(),
		attr_val='1.1',
		allow_update=False,
	)
	assert attr_val == 1.1


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_int_as_str():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(),
		attr_val='1',
		allow_update=False,
	)
	assert attr_val == 1


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_range_float_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_FLOAT',
			attr_type=ATTR.FLOAT(ranges=[[0.5, 9.5]]),
			attr_val=9.5,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_range_float():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(ranges=[[0.5, 9.5]]),
		attr_val=0.5,
		allow_update=False,
	)
	assert attr_val == 0.5


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_range_float_as_str():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(ranges=[[0.5, 9.5]]),
		attr_val='0.5',
		allow_update=False,
	)
	assert attr_val == 0.5


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(),
		attr_val=None,
		allow_update=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_default_None():
	attr_type = ATTR.FLOAT()
	attr_type._default = 'test_validate_attr_FLOAT'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=attr_type,
		attr_val=None,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_FLOAT'


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_default_str():
	attr_type = ATTR.FLOAT()
	attr_type._default = 'test_validate_attr_FLOAT'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=attr_type,
		attr_val='str',
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_FLOAT'


@pytest.mark.asyncio
async def test_validate_attr_FLOAT_default_int_allow_none():
	attr_type = ATTR.FLOAT()
	attr_type._default = 'test_validate_attr_FLOAT'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=attr_type,
		attr_val='str',
		allow_update=True,
	)
	assert attr_val == None
