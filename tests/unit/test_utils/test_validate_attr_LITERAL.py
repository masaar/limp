from ....classes import ATTR
from .... import utils

import pytest


def test_validate_attr_LITERAL_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LITERAL',
			attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_LITERAL_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LITERAL',
			attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
			attr_val='0',
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_LITERAL_int_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LITERAL',
			attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_LITERAL_str():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
		attr_val='str',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'str'

def test_validate_attr_LITERAL_int():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
		attr_val=0,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 0

def test_validate_attr_LITERAL_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=ATTR.LITERAL(literal=['str', 0, 1.1]),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None

def test_validate_attr_LITERAL_default_None():
	attr_type = ATTR.LITERAL(literal=['str', 0, 1.1])
	attr_type._default = 'test_validate_attr_LITERAL'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_LITERAL'

def test_validate_attr_LITERAL_default_int():
	attr_type = ATTR.LITERAL(literal=['str', 0, 1.1])
	attr_type._default = 'test_validate_attr_LITERAL'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_LITERAL'

def test_validate_attr_LITERAL_default_int_allow_none():
	attr_type = ATTR.LITERAL(literal=['str', 0, 1.1])
	attr_type._default = 'test_validate_attr_LITERAL'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LITERAL',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None