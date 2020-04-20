from classes import ATTR
import utils

import pytest


def test_validate_attr_DATETIME_None(mocker):
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATETIME',
			attr_type=ATTR.DATETIME(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_DATETIME_int(mocker):
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATETIME',
			attr_type=ATTR.DATETIME(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_DATETIME_str_invalid(mocker):
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATETIME',
			attr_type=ATTR.DATETIME(),
			attr_val='202002020000',
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_DATETIME_datetime_short(mocker):
	mocker.patch('utils.return_valid_attr')
	utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=ATTR.DATETIME(),
		attr_val='2020-02-02T00:00',
		allow_opers=False,
		allow_none=False,
	)
	utils.return_valid_attr.assert_called_once_with(attr_val='2020-02-02T00:00', attr_oper=False)

def test_validate_attr_DATETIME_datetime_medium(mocker):
	mocker.patch('utils.return_valid_attr')
	utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=ATTR.DATETIME(),
		attr_val='2020-02-02T00:00:00',
		allow_opers=False,
		allow_none=False,
	)
	utils.return_valid_attr.assert_called_once_with(attr_val='2020-02-02T00:00:00', attr_oper=False)

def test_validate_attr_DATETIME_datetime_iso(mocker):
	mocker.patch('utils.return_valid_attr')
	utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=ATTR.DATETIME(),
		attr_val='2020-02-02T00:00:00.000000',
		allow_opers=False,
		allow_none=False,
	)
	utils.return_valid_attr.assert_called_once_with(attr_val='2020-02-02T00:00:00.000000', attr_oper=False)

def test_validate_attr_DATETIME_None_allow_none(mocker):
	test = utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=ATTR.DATETIME(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert test == None

def test_validate_attr_DATETIME_default_None(mocker):
	attr_type = ATTR.BOOL()
	attr_type._default = '2020-02-02'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DATETIME',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '2020-02-02'

def test_validate_attr_DATETIME_default_int_allow_none(mocker):
	attr_type = ATTR.DATETIME()
	attr_type._default = True
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATETIME',
			attr_type=attr_type,
			attr_val=1,
			allow_opers=True,
			allow_none=True,
		)
