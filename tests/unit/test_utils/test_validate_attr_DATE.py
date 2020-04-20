from classes import ATTR
import utils

import pytest


def test_validate_attr_DATE_None(mocker):
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATE',
			attr_type=ATTR.DATE(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_DATE_int(mocker):
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATE',
			attr_type=ATTR.DATE(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_DATE_str_invalid(mocker):
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATE',
			attr_type=ATTR.DATE(),
			attr_val='20200202',
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_DATE_date(mocker):
	mocker.patch('utils.return_valid_attr')
	utils.validate_attr(
		attr_name='test_validate_attr_DATE',
		attr_type=ATTR.DATE(),
		attr_val='2020-02-02',
		allow_opers=False,
		allow_none=False,
	)
	utils.return_valid_attr.assert_called_once_with(attr_val='2020-02-02', attr_oper=False)

def test_validate_attr_DATE_None_allow_none(mocker):
	test = utils.validate_attr(
		attr_name='test_validate_attr_DATE',
		attr_type=ATTR.DATE(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert test == None

def test_validate_attr_DATE_default_None(mocker):
	attr_type = ATTR.BOOL()
	attr_type._default = '2020-02-02'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DATE',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '2020-02-02'

def test_validate_attr_DATE_default_int_allow_none(mocker):
	attr_type = ATTR.DATE()
	attr_type._default = True
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATE',
			attr_type=attr_type,
			attr_val=1,
			allow_opers=True,
			allow_none=True,
		)
