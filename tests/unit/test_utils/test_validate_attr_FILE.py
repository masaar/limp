from classes import ATTR
import utils

import pytest


def test_validate_attr_FILE_None():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_FILE',
			attr_type=ATTR.FILE(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_FILE_int():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_FILE',
			attr_type=ATTR.FILE(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_FILE_dict_invalid():
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_FILE',
			attr_type=ATTR.FILE(),
			attr_val={
				'key': 'value'
			},
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_FILE_file():
	file_attr_val = {
		'name': '__filename',
		'type': 'mime/type',
		'lastModified': 0,
		'size': 6,
		'content': b'__file'
	}
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=ATTR.FILE(),
		attr_val=file_attr_val,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == file_attr_val

def test_validate_attr_FILE_None_allow_none():
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=ATTR.FILE(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None

def test_validate_attr_FILE_default_None():
	attr_type = ATTR.FILE()
	attr_type._default = 'test_validate_attr_FILE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_FILE'

def test_validate_attr_FILE_default_int():
	attr_type = ATTR.FILE()
	attr_type._default = 'test_validate_attr_FILE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_FILE'

def test_validate_attr_FILE_default_int_allow_none():
	attr_type = ATTR.FILE()
	attr_type._default = 'test_validate_attr_FILE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_FILE',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
