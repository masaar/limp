from classes import ATTR
import utils

import pytest


def test_validate_attr_BOOL_None(mocker):
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_BOOL',
			attr_type=ATTR.BOOL(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_BOOL_int(mocker):
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_BOOL',
			attr_type=ATTR.BOOL(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_BOOL_bool(mocker):
	mocker.patch('utils.return_valid_attr')
	utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=ATTR.BOOL(),
		attr_val=False,
		allow_opers=False,
		allow_none=False,
	)
	utils.return_valid_attr.assert_called_once_with(attr_val=False, attr_oper=False)

def test_validate_attr_BOOL_None_allow_none(mocker):
	test = utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=ATTR.BOOL(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert test == None

def test_validate_attr_BOOL_default_None(mocker):
	attr_type = ATTR.BOOL()
	attr_type._default = True
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_BOOL',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == True

def test_validate_attr_BOOL_default_int_allow_none(mocker):
	attr_type = ATTR.STR()
	attr_type._default = True
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_BOOL',
			attr_type=attr_type,
			attr_val=1,
			allow_opers=True,
			allow_none=True,
		)
