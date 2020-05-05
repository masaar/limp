from ....classes import ATTR
from .... import utils

import pytest


def test_validate_attr_LOCALES_None(monkeypatch):
	from ....config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LOCALES',
			attr_type=ATTR.LOCALES(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_LOCALES_str_invalid(monkeypatch):
	from ....config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LOCALES',
			attr_type=ATTR.LOCALES(),
			attr_val='ar',
			allow_opers=False,
			allow_none=False,
		)


def test_validate_attr_LOCALES_locale(monkeypatch):
	from ....config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALES',
		attr_type=ATTR.LOCALES(),
		attr_val='en_AE',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'en_AE'


def test_validate_attr_LOCALES_None_allow_none(monkeypatch):
	from ....config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALES',
		attr_type=ATTR.LOCALES(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


def test_validate_attr_LOCALES_default_None(monkeypatch):
	from ....config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	attr_type = ATTR.LOCALES()
	attr_type._default = 'test_validate_attr_LOCALES'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALES',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_LOCALES'


def test_validate_attr_LOCALES_default_int(monkeypatch):
	from ....config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	attr_type = ATTR.LOCALES()
	attr_type._default = 'test_validate_attr_LOCALES'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALES',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_LOCALES'


def test_validate_attr_LOCALES_default_int_allow_none(monkeypatch):
	from ....config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	attr_type = ATTR.LOCALES()
	attr_type._default = 'test_validate_attr_LOCALES'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALES',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
