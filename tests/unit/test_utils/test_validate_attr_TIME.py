from limp.classes import ATTR
from limp import utils

import pytest


def test_validate_attr_TIME_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_TIME',
			attr_type=ATTR.TIME(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_TIME_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_TIME',
			attr_type=ATTR.TIME(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_TIME_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_TIME',
			attr_type=ATTR.TIME(),
			attr_val='0000',
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_TIME_datetime_short():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=ATTR.TIME(),
		attr_val='00:00',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '00:00'


def test_validate_attr_TIME_datetime_medium():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=ATTR.TIME(),
		attr_val='00:00:00',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '00:00:00'


def test_validate_attr_TIME_datetime_iso():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=ATTR.TIME(),
		attr_val='00:00:00.000000',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == '00:00:00.000000'


def test_validate_attr_TIME_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=ATTR.TIME(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


def test_validate_attr_TIME_default_None():
	attr_type = ATTR.TIME()
	attr_type._default = 'test_validate_attr_TIME'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_TIME'


def test_validate_attr_TIME_default_int():
	attr_type = ATTR.TIME()
	attr_type._default = 'test_validate_attr_TIME'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_TIME'


def test_validate_attr_TIME_default_int_allow_none():
	attr_type = ATTR.TIME()
	attr_type._default = 'test_validate_attr_TIME'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_TIME',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
