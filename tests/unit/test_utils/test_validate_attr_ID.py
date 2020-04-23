from ....classes import ATTR
from .... import utils

from bson import ObjectId
import pytest


def test_validate_attr_ID_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_ID',
			attr_type=ATTR.ID(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_ID_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_ID',
			attr_type=ATTR.ID(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_ID_str():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=ATTR.ID(),
		attr_val='000000000000000000000000',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == ObjectId('000000000000000000000000')

def test_validate_attr_ID_objectid():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=ATTR.ID(),
		attr_val=ObjectId('000000000000000000000000'),
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == ObjectId('000000000000000000000000')

def test_validate_attr_ID_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=ATTR.ID(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None

def test_validate_attr_ID_default_None():
	attr_type = ATTR.ID()
	attr_type._default = 'test_validate_attr_ID'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_ID'

def test_validate_attr_ID_default_int():
	attr_type = ATTR.ID()
	attr_type._default = 'test_validate_attr_ID'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_ID'

def test_validate_attr_ID_default_int_allow_none():
	attr_type = ATTR.ID()
	attr_type._default = 'test_validate_attr_ID'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_ID',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None