from classes import ATTR
import utils

import pytest


def test_validate_attr_PHONE_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_PHONE',
			attr_type=ATTR.PHONE(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_PHONE_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_PHONE',
			attr_type=ATTR.PHONE(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_PHONE_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_PHONE',
			attr_type=ATTR.PHONE(),
			attr_val='str',
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_PHONE_phone():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=ATTR.PHONE(),
		attr_val='+0',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '+0'

def test_validate_attr_PHONE_codes_phone_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_PHONE',
			attr_type=ATTR.PHONE(codes=['971', '1']),
			attr_val='+0',
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_PHONE_codes_phone():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=ATTR.PHONE(codes=['971', '1']),
		attr_val='+9710',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '+9710'

def test_validate_attr_PHONE_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=ATTR.PHONE(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None

def test_validate_attr_PHONE_default_None():
	attr_type = ATTR.PHONE()
	attr_type._default = 'test_validate_attr_PHONE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_PHONE'

def test_validate_attr_PHONE_default_int():
	attr_type = ATTR.PHONE()
	attr_type._default = 'test_validate_attr_PHONE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_PHONE'

def test_validate_attr_PHONE_default_int_allow_none():
	attr_type = ATTR.PHONE()
	attr_type._default = 'test_validate_attr_PHONE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_PHONE',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
