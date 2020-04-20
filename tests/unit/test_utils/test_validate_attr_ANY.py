from classes import ATTR
import utils

import pytest


def test_validate_attr_ANY_None(mocker):
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_ANY',
			attr_type=ATTR.ANY(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_ANY_str(mocker):
	mocker.patch('utils.return_valid_attr')
	utils.validate_attr(
		attr_name='test_validate_attr_ANY',
		attr_type=ATTR.ANY(),
		attr_val='test_validate_attr_ANY',
		allow_opers=False,
		allow_none=False,
	)
	utils.return_valid_attr.assert_called_once_with(attr_val='test_validate_attr_ANY', attr_oper=False)


def test_validate_attr_ANY_default_None(mocker):
	mocker.patch('utils.return_valid_attr')
	attr_type = ATTR.ANY()
	attr_type._default = 'test_validate_attr_ANY'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_ANY',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_ANY'
