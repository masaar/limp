from ....classes import ATTR
from .... import utils

import pytest


def test_validate_attr_DICT_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.DICT(dict={'key': ATTR.STR()}),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_DICT_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.DICT(dict={'key': ATTR.STR()}),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_DICT_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.DICT(dict={'key': ATTR.STR()}),
			attr_val={'key': 'value', 'key2': 'value',},
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_DICT_simple_dict():
	dict_attr_val = {
		'key1': 'value',
		'key2': 2,
	}
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=ATTR.DICT(dict={'key1': ATTR.STR(), 'key2': ATTR.INT()}),
		attr_val=dict_attr_val,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == dict_attr_val


def test_validate_attr_DICT_nested_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.DICT(
				dict={
					'key1': ATTR.STR(),
					'key2': ATTR.DICT(dict={'child_key': ATTR.INT()}),
				}
			),
			attr_val={'key1': 'value', 'key2': 2,},
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_DICT_nested_dict():
	dict_attr_val = {
		'key1': 'value',
		'key2': {'child_key': 2},
	}
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=ATTR.DICT(
			dict={'key1': ATTR.STR(), 'key2': ATTR.DICT(dict={'child_key': ATTR.INT()})}
		),
		attr_val=dict_attr_val,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == dict_attr_val


def test_validate_attr_DICT_nested_list_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.DICT(
				dict={'key1': ATTR.STR(), 'key2': ATTR.LIST(list=[ATTR.INT()]),}
			),
			attr_val={'key1': 'value', 'key2': ['a'],},
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_DICT_nested_list_dict():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=ATTR.DICT(
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


def test_validate_attr_DICT_typed_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.DICT(
				dict={'__key': ATTR.STR(), '__val': ATTR.INT()},
				min=2,
				max=3,
			),
			attr_val={'key1': 'value', 'key2': ['a']},
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_DICT_typed_dict_invalid_count():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DICT',
			attr_type=ATTR.DICT(
				dict={'__key': ATTR.STR(), '__val': ATTR.INT()},
				min=2,
				max=3,
			),
			attr_val={'key1': '1', 'key2': 2, 'key3': 3, 'key4': '4'},
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_DICT_typed_dict():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=ATTR.DICT(
			dict={'__key': ATTR.STR(), '__val': ATTR.INT()},
			min=2,
			max=4,
		),
		attr_val={'key1': '1', 'key2': 2, 'key3': 3, 'key4': '4'},
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == {'key1': 1, 'key2': 2, 'key3': 3, 'key4': 4}


def test_validate_attr_DICT_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=ATTR.DICT(dict={'key': ATTR.STR()}),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


# [TODO] Add tests for nested default values

def test_validate_attr_DICT_default_None():
	attr_type = ATTR.DICT(dict={'key': ATTR.STR()})
	attr_type._default = 'test_validate_attr_DICT'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_DICT'


def test_validate_attr_DICT_default_int():
	attr_type = ATTR.DICT(dict={'key': ATTR.STR()})
	attr_type._default = 'test_validate_attr_DICT'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_DICT'


def test_validate_attr_DICT_default_int_allow_none():
	attr_type = ATTR.DICT(dict={'key': ATTR.STR()})
	attr_type._default = 'test_validate_attr_DICT'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DICT',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
