from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_GEO_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_GEO',
			attr_type=ATTR.GEO(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_GEO_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_GEO',
			attr_type=ATTR.GEO(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_GEO_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_GEO',
			attr_type=ATTR.GEO(),
			attr_val={'key': 'value'},
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_GEO_geo():
	geo_attr_val = {'type': 'Point', 'coordinates': [21.422507, 39.826181]}
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_GEO',
		attr_type=ATTR.GEO(),
		attr_val=geo_attr_val,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == geo_attr_val


@pytest.mark.asyncio
async def test_validate_attr_GEO_geo_as_str():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_GEO',
			attr_type=ATTR.GEO(),
			attr_val={'type': 'Point', 'coordinates': ['21.422507', '39.826181']},
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_GEO_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_GEO',
		attr_type=ATTR.GEO(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_GEO_default_None():
	attr_type = ATTR.GEO()
	attr_type._default = 'test_validate_attr_GEO'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_GEO',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_GEO'


@pytest.mark.asyncio
async def test_validate_attr_GEO_default_int():
	attr_type = ATTR.GEO()
	attr_type._default = 'test_validate_attr_GEO'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_GEO',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_GEO'


@pytest.mark.asyncio
async def test_validate_attr_GEO_default_int_allow_none():
	attr_type = ATTR.GEO()
	attr_type._default = 'test_validate_attr_GEO'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_GEO',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
