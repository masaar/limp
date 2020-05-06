from limp.classes import ATTR
from limp import utils

import pytest


def test_validate_attr_BOOL_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_BOOL',
			attr_type=ATTR.BOOL(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_BOOL_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_BOOL',
			attr_type=ATTR.BOOL(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_BOOL_bool():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=ATTR.BOOL(),
		attr_val=False,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == False


def test_validate_attr_BOOL_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=ATTR.BOOL(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


def test_validate_attr_BOOL_default_None():
	attr_type = ATTR.BOOL()
	attr_type._default = 'test_validate_attr_BOOL'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_BOOL'


def test_validate_attr_BOOL_default_int():
	attr_type = ATTR.STR()
	attr_type._default = 'test_validate_attr_BOOL'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_BOOL'


def test_validate_attr_BOOL_default_int_allow_none():
	attr_type = ATTR.STR()
	attr_type._default = 'test_validate_attr_BOOL'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
