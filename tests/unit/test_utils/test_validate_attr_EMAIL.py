from ....classes import ATTR
from .... import utils

import pytest


def test_validate_attr_EMAIL_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_EMAIL',
			attr_type=ATTR.EMAIL(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_EMAIL_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_EMAIL',
			attr_type=ATTR.EMAIL(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_EMAIL_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_EMAIL',
			attr_type=ATTR.EMAIL(),
			attr_val='str',
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_EMAIL_email():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=ATTR.EMAIL(),
		attr_val='info@limp.masaar.com',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'info@limp.masaar.com'

def test_validate_attr_EMAIL_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=ATTR.EMAIL(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None

def test_validate_attr_EMAIL_default_None():
	attr_type = ATTR.EMAIL()
	attr_type._default = 'test_validate_attr_EMAIL'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_EMAIL'

def test_validate_attr_EMAIL_default_int():
	attr_type = ATTR.EMAIL()
	attr_type._default = 'test_validate_attr_EMAIL'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_EMAIL'

def test_validate_attr_EMAIL_default_int_allow_none():
	attr_type = ATTR.EMAIL()
	attr_type._default = 'test_validate_attr_EMAIL'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
