from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_LITERAL_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_LITERAL',
			attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
			attr_val=None,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_LITERAL_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_LITERAL',
			attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
			attr_val='0',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_LITERAL_int_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_LITERAL',
			attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
			attr_val=1,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_LITERAL_str():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
		attr_val='str',
		allow_update=False,
	)
	assert attr_val == 'str'


@pytest.mark.asyncio
async def test_validate_attr_LITERAL_int():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
		attr_val=0,
		allow_update=False,
	)
	assert attr_val == 0


@pytest.mark.asyncio
async def test_validate_attr_LITERAL_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
		attr_val=None,
		allow_update=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_LITERAL_default_None():
	attr_type = ATTR.LITERAL(literal=['str', 0, 1.1])
	attr_type._default = 'test_validate_attr_LITERAL'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=attr_type,
		attr_val=None,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_LITERAL'


@pytest.mark.asyncio
async def test_validate_attr_LITERAL_default_int():
	attr_type = ATTR.LITERAL(literal=['str', 0, 1.1])
	attr_type._default = 'test_validate_attr_LITERAL'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=attr_type,
		attr_val=1,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_LITERAL'


@pytest.mark.asyncio
async def test_validate_attr_LITERAL_default_int_allow_none():
	attr_type = ATTR.LITERAL(literal=['str', 0, 1.1])
	attr_type._default = 'test_validate_attr_LITERAL'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=attr_type,
		attr_val=1,
		allow_update=True,
	)
	assert attr_val == None
