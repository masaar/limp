from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_TIME_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_TIME',
			attr_type=ATTR.TIME(),
			attr_val=None,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_TIME_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_TIME',
			attr_type=ATTR.TIME(),
			attr_val=1,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_TIME_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_TIME',
			attr_type=ATTR.TIME(),
			attr_val='0000',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_TIME_datetime_short():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=ATTR.TIME(),
		attr_val='00:00',
		allow_update=False,
	)
	assert attr_val == '00:00'


@pytest.mark.asyncio
async def test_validate_attr_TIME_datetime_medium():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=ATTR.TIME(),
		attr_val='00:00:00',
		allow_update=False,
	)
	assert attr_val == '00:00:00'


@pytest.mark.asyncio
async def test_validate_attr_TIME_datetime_iso():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=ATTR.TIME(),
		attr_val='00:00:00.000000',
		allow_update=False,
	)
	assert attr_val == '00:00:00.000000'


@pytest.mark.asyncio
async def test_validate_attr_TIME_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=ATTR.TIME(),
		attr_val=None,
		allow_update=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_TIME_default_None():
	attr_type = ATTR.TIME()
	attr_type._default = 'test_validate_attr_TIME'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=attr_type,
		attr_val=None,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_TIME'


@pytest.mark.asyncio
async def test_validate_attr_TIME_default_int():
	attr_type = ATTR.TIME()
	attr_type._default = 'test_validate_attr_TIME'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=attr_type,
		attr_val=1,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_TIME'


@pytest.mark.asyncio
async def test_validate_attr_TIME_default_int_allow_none():
	attr_type = ATTR.TIME()
	attr_type._default = 'test_validate_attr_TIME'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=attr_type,
		attr_val=1,
		allow_update=True,
	)
	assert attr_val == None
