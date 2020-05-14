from limp.classes import ATTR
from limp import utils

from bson import ObjectId
import pytest


@pytest.mark.asyncio
async def test_validate_attr_ID_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_ID',
			attr_type=ATTR.ID(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_ID_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_ID',
			attr_type=ATTR.ID(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_ID_str():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=ATTR.ID(),
		attr_val='000000000000000000000000',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == ObjectId('000000000000000000000000')


@pytest.mark.asyncio
async def test_validate_attr_ID_objectid():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=ATTR.ID(),
		attr_val=ObjectId('000000000000000000000000'),
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == ObjectId('000000000000000000000000')


@pytest.mark.asyncio
async def test_validate_attr_ID_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=ATTR.ID(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_ID_default_None():
	attr_type = ATTR.ID()
	attr_type._default = 'test_validate_attr_ID'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_ID'


@pytest.mark.asyncio
async def test_validate_attr_ID_default_int():
	attr_type = ATTR.ID()
	attr_type._default = 'test_validate_attr_ID'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_ID'


@pytest.mark.asyncio
async def test_validate_attr_ID_default_int_allow_none():
	attr_type = ATTR.ID()
	attr_type._default = 'test_validate_attr_ID'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
