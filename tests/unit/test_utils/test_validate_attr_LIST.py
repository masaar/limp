from classes import ATTR
import utils

import pytest


def test_validate_attr_LIST_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LIST',
			attr_type=ATTR.LIST(list=[ATTR.STR()]),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_LIST_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LIST',
			attr_type=ATTR.LIST(list=[ATTR.STR()]),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_LIST_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LIST',
			attr_type=ATTR.LIST(list=[ATTR.STR()]),
			attr_val={'key': 'value', 'key2': 'value',},
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_LIST_simple_list():
	list_attr_val = ['str', 'str', 'str']
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LIST',
		attr_type=ATTR.LIST(list=[ATTR.STR()]),
		attr_val=list_attr_val,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == list_attr_val


def test_validate_attr_LIST_nested_list_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LIST',
			attr_type=ATTR.LIST(
				list=[ATTR.LIST(list=[ATTR.STR()])]
			),
			attr_val=['str', 'str', ['str']],
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_LIST_nested_list():
	list_attr_val = [
		['str'],
		['str', 'str'],
		['str']
	]
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LIST',
		attr_type=ATTR.LIST(
			list=[ATTR.LIST(list=[ATTR.STR()])]
		),
		attr_val=list_attr_val,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == list_attr_val


def test_validate_attr_LIST_nested_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LIST',
			attr_type=ATTR.LIST(
				list=[ATTR.DICT(dict={'__key': ATTR.STR(), '__val': ATTR.INT()})]
			),
			attr_val=[{'key':1}, {'key':'val'}],
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_LIST_nested_dict():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LIST',
		attr_type=ATTR.LIST(
			list=[ATTR.DICT(dict={'__key': ATTR.STR(), '__val': ATTR.INT()})]
		),
		attr_val=[{'key':1}, {'key':'2'}],
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == [
		{'key': 1},
		{'key': 2}
	]


def test_validate_attr_LIST_muti_list_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LIST',
			attr_type=ATTR.LIST(
				list=[ATTR.EMAIL(), ATTR.URI_WEB()]
			),
			attr_val=['info@limp.masaar.com', 'http://sub.example.com', '1'],
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_LIST_multi_list_invalid_count():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LIST',
			attr_type=ATTR.LIST(
				list=[ATTR.EMAIL(), ATTR.URI_WEB()],
				min=1,
				max=2
			),
			attr_val=['info@limp.masaar.com', 'http://sub.example.com', 'https://sub.domain.com'],
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_LIST_typed_dict():
	list_attr_val = ['info@limp.masaar.com', 'http://sub.example.com', 'https://sub.domain.com']
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LIST',
		attr_type=ATTR.LIST(
			list=[ATTR.EMAIL(), ATTR.URI_WEB()],
			min=1,
			max=3
		),
		attr_val=list_attr_val,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == list_attr_val


def test_validate_attr_LIST_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LIST',
		attr_type=ATTR.LIST(list=[ATTR.STR()]),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


# [TODO] Add tests for nested default values

def test_validate_attr_LIST_default_None():
	attr_type = ATTR.LIST(list=[ATTR.STR()])
	attr_type._default = 'test_validate_attr_LIST'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LIST',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_LIST'


def test_validate_attr_LIST_default_int():
	attr_type = ATTR.LIST(list=[ATTR.STR()])
	attr_type._default = 'test_validate_attr_LIST'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LIST',
		attr_type=attr_type,
		attr_val=[1],
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_LIST'


def test_validate_attr_LIST_default_int_allow_none():
	attr_type = ATTR.LIST(list=[ATTR.STR()])
	attr_type._default = 'test_validate_attr_LIST'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LIST',
		attr_type=attr_type,
		attr_val=[1],
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == [None]
