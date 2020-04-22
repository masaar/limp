from classes import ATTR
import utils

import pytest


def test_validate_attr_FLOAT_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_FLOAT',
			attr_type=ATTR.FLOAT(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_FLOAT_str():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_FLOAT',
			attr_type=ATTR.FLOAT(),
			attr_val='str',
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_FLOAT_float():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(),
		attr_val=1.1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 1.1

def test_validate_attr_FLOAT_int():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(),
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 1

def test_validate_attr_FLOAT_float_as_str():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(),
		attr_val='1.1',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 1.1

def test_validate_attr_FLOAT_int_as_str():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(),
		attr_val='1',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 1

def test_validate_attr_FLOAT_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=ATTR.FLOAT(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None

def test_validate_attr_FLOAT_default_None():
	attr_type = ATTR.FLOAT()
	attr_type._default = 'test_validate_attr_FLOAT'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_FLOAT'

def test_validate_attr_FLOAT_default_str():
	attr_type = ATTR.FLOAT()
	attr_type._default = 'test_validate_attr_FLOAT'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=attr_type,
		attr_val='str',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_FLOAT'

def test_validate_attr_FLOAT_default_int_allow_none():
	attr_type = ATTR.FLOAT()
	attr_type._default = 'test_validate_attr_FLOAT'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FLOAT',
		attr_type=attr_type,
		attr_val='str',
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None