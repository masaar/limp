from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_DICT_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.TYPED_DICT(dict={'key': ATTR.STR()}),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_DICT_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.TYPED_DICT(dict={'key': ATTR.STR()}),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_DICT_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.TYPED_DICT(dict={'key': ATTR.STR()}),
			attr_val={'key': 'value', 'key2': 'value',},
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_DICT_simple_dict():
	dict_attr_val = {
		'key1': 'value',
		'key2': 2,
	}
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=ATTR.TYPED_DICT(dict={'key1': ATTR.STR(), 'key2': ATTR.INT()}),
		attr_val=dict_attr_val,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == dict_attr_val


@pytest.mark.asyncio
async def test_validate_attr_DICT_nested_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.TYPED_DICT(
				dict={
					'key1': ATTR.STR(),
					'key2': ATTR.TYPED_DICT(dict={'child_key': ATTR.INT()}),
				}
			),
			attr_val={'key1': 'value', 'key2': 2,},
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_DICT_nested_dict():
	dict_attr_val = {
		'key1': 'value',
		'key2': {'child_key': 2},
	}
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=ATTR.TYPED_DICT(
			dict={
				'key1': ATTR.STR(),
				'key2': ATTR.TYPED_DICT(dict={'child_key': ATTR.INT()}),
			}
		),
		attr_val=dict_attr_val,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == dict_attr_val


@pytest.mark.asyncio
async def test_validate_attr_DICT_nested_list_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.TYPED_DICT(
				dict={'key1': ATTR.STR(), 'key2': ATTR.LIST(list=[ATTR.INT()]),}
			),
			attr_val={'key1': 'value', 'key2': ['a'],},
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_DICT_nested_list_dict():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=ATTR.TYPED_DICT(
			dict={'key1': ATTR.STR(), 'key2': ATTR.LIST(list=[ATTR.INT()]),}
		),
		attr_val={'key1': 'value', 'key2': [1, '2', 3]},
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == {
		'key1': 'value',
		'key2': [1, 2, 3],
	}


@pytest.mark.asyncio
async def test_validate_attr_DICT_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=ATTR.TYPED_DICT(dict={'key': ATTR.STR()}),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


# [TODO] Add tests for nested default values


@pytest.mark.asyncio
async def test_validate_attr_DICT_default_None():
	attr_type = ATTR.TYPED_DICT(dict={'key': ATTR.STR()})
	attr_type._default = 'test_validate_attr_DICT'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_DICT'


@pytest.mark.asyncio
async def test_validate_attr_DICT_default_int():
	attr_type = ATTR.TYPED_DICT(dict={'key': ATTR.STR()})
	attr_type._default = 'test_validate_attr_DICT'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_DICT'


@pytest.mark.asyncio
async def test_validate_attr_DICT_default_int_allow_none():
	attr_type = ATTR.TYPED_DICT(dict={'key': ATTR.STR()})
	attr_type._default = 'test_validate_attr_DICT'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
