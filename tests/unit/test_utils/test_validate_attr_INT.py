from ....classes import ATTR
from .... import utils

import pytest


def test_validate_attr_INT_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_INT',
			attr_type=ATTR.INT(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_INT_str():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_INT',
			attr_type=ATTR.INT(),
			attr_val='str',
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_INT_float():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_INT',
			attr_type=ATTR.INT(),
			attr_val=1.1,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_INT_int():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_INT',
		attr_type=ATTR.INT(),
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 1


def test_validate_attr_INT_float_as_str():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_INT',
			attr_type=ATTR.INT(),
			attr_val='1.1',
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_INT_int_as_str():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_INT',
		attr_type=ATTR.INT(),
		attr_val='1',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 1


def test_validate_attr_INT_range_int_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_INT',
			attr_type=ATTR.INT(ranges=[[0, 10]]),
			attr_val=10,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_INT_range_int():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_INT',
		attr_type=ATTR.INT(ranges=[[0, 10]]),
		attr_val=0,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 0


def test_validate_attr_INT_range_int_as_str():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_INT',
		attr_type=ATTR.INT(ranges=[[0, 10]]),
		attr_val='0',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 0


def test_validate_attr_INT_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_INT',
		attr_type=ATTR.INT(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


def test_validate_attr_INT_default_None():
	attr_type = ATTR.INT()
	attr_type._default = 'test_validate_attr_INT'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_INT',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_INT'


def test_validate_attr_INT_default_str():
	attr_type = ATTR.INT()
	attr_type._default = 'test_validate_attr_INT'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_INT',
		attr_type=attr_type,
		attr_val='str',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_INT'


def test_validate_attr_INT_default_int_allow_none():
	attr_type = ATTR.INT()
	attr_type._default = 'test_validate_attr_INT'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_INT',
		attr_type=attr_type,
		attr_val='str',
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
