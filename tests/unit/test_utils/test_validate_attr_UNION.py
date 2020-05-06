from limp.classes import ATTR
from limp import utils

import pytest


def test_validate_attr_UNION_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_UNION',
			attr_type=ATTR.UNION(union=[ATTR.STR(), ATTR.INT()]),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_UNION_float():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_UNION',
			attr_type=ATTR.UNION(union=[ATTR.STR(), ATTR.INT()]),
			attr_val=1.1,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_UNION_str():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=ATTR.UNION(union=[ATTR.STR(), ATTR.INT()]),
		attr_val='str',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'str'


def test_validate_attr_UNION_int():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=ATTR.UNION(union=[ATTR.STR(), ATTR.INT()]),
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 1


def test_validate_attr_UNION_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=ATTR.UNION(union=[ATTR.STR(), ATTR.INT()]),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


def test_validate_attr_UNION_default_None():
	attr_type = ATTR.UNION(union=[ATTR.STR(), ATTR.INT()])
	attr_type._default = 'test_validate_attr_UNION'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_UNION'


def test_validate_attr_UNION_default_float():
	attr_type = ATTR.UNION(union=[ATTR.STR(), ATTR.INT()])
	attr_type._default = 'test_validate_attr_UNION'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=attr_type,
		attr_val=1.1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_UNION'


def test_validate_attr_UNION_default_float_allow_none():
	attr_type = ATTR.UNION(union=[ATTR.STR(), ATTR.INT()])
	attr_type._default = 'test_validate_attr_UNION'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_UNION',
		attr_type=attr_type,
		attr_val=1.1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
