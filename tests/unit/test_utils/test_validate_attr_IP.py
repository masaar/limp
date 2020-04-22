from classes import ATTR
import utils

import pytest


def test_validate_attr_IP_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_IP',
			attr_type=ATTR.IP(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_IP_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_IP',
			attr_type=ATTR.IP(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_IP_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_IP',
			attr_type=ATTR.IP(),
			attr_val='str',
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_IP_ip():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_IP',
		attr_type=ATTR.IP(),
		attr_val='127.0.0.1',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '127.0.0.1'

def test_validate_attr_IP_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_IP',
		attr_type=ATTR.IP(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None

def test_validate_attr_IP_default_None():
	attr_type = ATTR.IP()
	attr_type._default = 'test_validate_attr_IP'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_IP',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_IP'

def test_validate_attr_IP_default_int():
	attr_type = ATTR.IP()
	attr_type._default = 'test_validate_attr_IP'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_IP',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_IP'

def test_validate_attr_IP_default_int_allow_none():
	attr_type = ATTR.IP()
	attr_type._default = 'test_validate_attr_IP'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_IP',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
