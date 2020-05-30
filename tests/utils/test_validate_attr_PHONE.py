from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_PHONE_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_PHONE',
			attr_type=ATTR.PHONE(),
			attr_val=None,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_PHONE_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_PHONE',
			attr_type=ATTR.PHONE(),
			attr_val=1,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_PHONE_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_PHONE',
			attr_type=ATTR.PHONE(),
			attr_val='str',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_PHONE_phone():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=ATTR.PHONE(),
		attr_val='+0',
		allow_update=False,
	)
	assert attr_val == '+0'


@pytest.mark.asyncio
async def test_validate_attr_PHONE_codes_phone_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_PHONE',
			attr_type=ATTR.PHONE(codes=['971', '1']),
			attr_val='+0',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_PHONE_codes_phone():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=ATTR.PHONE(codes=['971', '1']),
		attr_val='+9710',
		allow_update=False,
	)
	assert attr_val == '+9710'


@pytest.mark.asyncio
async def test_validate_attr_PHONE_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=ATTR.PHONE(),
		attr_val=None,
		allow_update=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_PHONE_default_None():
	attr_type = ATTR.PHONE()
	attr_type._default = 'test_validate_attr_PHONE'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=attr_type,
		attr_val=None,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_PHONE'


@pytest.mark.asyncio
async def test_validate_attr_PHONE_default_int():
	attr_type = ATTR.PHONE()
	attr_type._default = 'test_validate_attr_PHONE'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=attr_type,
		attr_val=1,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_PHONE'


@pytest.mark.asyncio
async def test_validate_attr_PHONE_default_int_allow_none():
	attr_type = ATTR.PHONE()
	attr_type._default = 'test_validate_attr_PHONE'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=attr_type,
		attr_val=1,
		allow_update=True,
	)
	assert attr_val == None
