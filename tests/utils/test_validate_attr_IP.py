from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_IP_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_IP',
			attr_type=ATTR.IP(),
			attr_val=None,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_IP_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_IP',
			attr_type=ATTR.IP(),
			attr_val=1,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_IP_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_IP',
			attr_type=ATTR.IP(),
			attr_val='str',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_IP_ip():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_IP',
		attr_type=ATTR.IP(),
		attr_val='127.0.0.1',
		allow_update=False,
	)
	assert attr_val == '127.0.0.1'


@pytest.mark.asyncio
async def test_validate_attr_IP_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_IP',
		attr_type=ATTR.IP(),
		attr_val=None,
		allow_update=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_IP_default_None():
	attr_type = ATTR.IP()
	attr_type._default = 'test_validate_attr_IP'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_IP',
		attr_type=attr_type,
		attr_val=None,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_IP'


@pytest.mark.asyncio
async def test_validate_attr_IP_default_int():
	attr_type = ATTR.IP()
	attr_type._default = 'test_validate_attr_IP'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_IP',
		attr_type=attr_type,
		attr_val=1,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_IP'


@pytest.mark.asyncio
async def test_validate_attr_IP_default_int_allow_none():
	attr_type = ATTR.IP()
	attr_type._default = 'test_validate_attr_IP'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_IP',
		attr_type=attr_type,
		attr_val=1,
		allow_update=True,
	)
	assert attr_val == None
