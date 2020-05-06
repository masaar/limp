from limp.classes import ATTR
from limp import utils

import pytest


def test_validate_attr_URI_WEB_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_URI_WEB',
			attr_type=ATTR.URI_WEB(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_URI_WEB_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_URI_WEB',
			attr_type=ATTR.URI_WEB(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_URI_WEB_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_URI_WEB',
			attr_type=ATTR.URI_WEB(),
			attr_val='str',
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_URI_WEB_uri_web_insecure():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(),
		attr_val='http://sub.example.com',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'http://sub.example.com'

def test_validate_attr_URI_WEB_uri_web_secure():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(),
		attr_val='https://sub.example.com',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'https://sub.example.com'

def test_validate_attr_URI_WEB_uri_web_params():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(),
		attr_val='https://sub.example.com?param1=something-here&param2=something_else',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'https://sub.example.com?param1=something-here&param2=something_else'

def test_validate_attr_URI_WEB_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None

def test_validate_attr_URI_WEB_default_None():
	attr_type = ATTR.URI_WEB()
	attr_type._default = 'test_validate_attr_URI_WEB'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_URI_WEB'

def test_validate_attr_URI_WEB_default_int():
	attr_type = ATTR.URI_WEB()
	attr_type._default = 'test_validate_attr_URI_WEB'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_URI_WEB'

def test_validate_attr_URI_WEB_default_int_allow_none():
	attr_type = ATTR.URI_WEB()
	attr_type._default = 'test_validate_attr_URI_WEB'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
