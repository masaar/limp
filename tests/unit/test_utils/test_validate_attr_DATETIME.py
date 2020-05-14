from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_DATETIME_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_DATETIME',
			attr_type=ATTR.DATETIME(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_DATETIME_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_DATETIME',
			attr_type=ATTR.DATETIME(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_DATETIME_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_DATETIME',
			attr_type=ATTR.DATETIME(),
			attr_val='202002020000',
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_DATETIME_datetime_short():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=ATTR.DATETIME(),
		attr_val='2020-02-02T00:00',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '2020-02-02T00:00'


@pytest.mark.asyncio
async def test_validate_attr_DATETIME_datetime_medium():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=ATTR.DATETIME(),
		attr_val='2020-02-02T00:00:00',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '2020-02-02T00:00:00'


@pytest.mark.asyncio
async def test_validate_attr_DATETIME_datetime_iso():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=ATTR.DATETIME(),
		attr_val='2020-02-02T00:00:00.000000',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '2020-02-02T00:00:00.000000'


@pytest.mark.asyncio
async def test_validate_attr_DATETIME_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=ATTR.DATETIME(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_DATETIME_default_None():
	attr_type = ATTR.DATETIME()
	attr_type._default = 'test_validate_attr_DATETIME'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_DATETIME'


@pytest.mark.asyncio
async def test_validate_attr_DATETIME_default_int():
	attr_type = ATTR.DATETIME()
	attr_type._default = 'test_validate_attr_DATETIME'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_DATETIME'


@pytest.mark.asyncio
async def test_validate_attr_DATETIME_default_int_allow_none():
	attr_type = ATTR.DATETIME()
	attr_type._default = 'test_validate_attr_DATETIME'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
