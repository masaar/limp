from ....classes import ATTR
from .... import utils

import pytest


def test_validate_attr_DATE_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATE',
			attr_type=ATTR.DATE(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_DATE_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATE',
			attr_type=ATTR.DATE(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_DATE_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_DATE',
			attr_type=ATTR.DATE(),
			attr_val='20200202',
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_DATE_date():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DATE',
		attr_type=ATTR.DATE(),
		attr_val='2020-02-02',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '2020-02-02'


def test_validate_attr_DATE_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DATE',
		attr_type=ATTR.DATE(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


def test_validate_attr_DATE_default_None():
	attr_type = ATTR.DATE()
	attr_type._default = 'test_validate_attr_DATE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DATE',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_DATE'


def test_validate_attr_DATE_default_int():
	attr_type = ATTR.DATE()
	attr_type._default = 'test_validate_attr_DATE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DATE',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_DATE'


def test_validate_attr_DATE_default_int_allow_none():
	attr_type = ATTR.DATE()
	attr_type._default = 'test_validate_attr_DATE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_DATE',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
