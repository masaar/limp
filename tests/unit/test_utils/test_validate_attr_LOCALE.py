from ....classes import ATTR
from .... import utils

import pytest


def test_validate_attr_LOCALE_None(monkeypatch):
	from ....config import Config
	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	monkeypatch.setattr(Config, 'locale', 'ar_AE')
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LOCALE',
			attr_type=ATTR.LOCALE(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_LOCALE_dict_invalid(monkeypatch):
	from ....config import Config
	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	monkeypatch.setattr(Config, 'locale', 'ar_AE')
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LOCALE',
			attr_type=ATTR.LOCALE(),
			attr_val={
				'ar': 'str',
			},
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_LOCALE_locale_all(monkeypatch):
	from ....config import Config
	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	monkeypatch.setattr(Config, 'locale', 'ar_AE')
	locale_attr_val = {
		'ar_AE': 'str',
		'en_AE': 'str',
		'de_DE': 'str',
	}
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALE',
		attr_type=ATTR.LOCALE(),
		attr_val=locale_attr_val,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == locale_attr_val

def test_validate_attr_LOCALE_locale_min(monkeypatch):
	from ....config import Config
	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	monkeypatch.setattr(Config, 'locale', 'ar_AE')
	locale_attr_val = {
		'ar_AE': 'str',
		'en_AE': 'str',
		'de_DE': 'str',
	}
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALE',
		attr_type=ATTR.LOCALE(),
		attr_val={
			'ar_AE': 'str',
		},
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == locale_attr_val

def test_validate_attr_LOCALE_locale_extra(monkeypatch):
	from ....config import Config
	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	monkeypatch.setattr(Config, 'locale', 'ar_AE')
	with pytest.raises(utils.InvalidAttrException):
		utils.validate_attr(
			attr_name='test_validate_attr_LOCALE',
			attr_type=ATTR.LOCALE(),
			attr_val={
				'ar_AE': 'str',
				'invalid': 'str',
			},
			allow_opers=False,
			allow_none=False,
		)

def test_validate_attr_LOCALE_None_allow_none(monkeypatch):
	from ....config import Config
	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	monkeypatch.setattr(Config, 'locale', 'ar_AE')
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALE',
		attr_type=ATTR.LOCALE(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None

def test_validate_attr_LOCALE_default_None(monkeypatch):
	from ....config import Config
	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	monkeypatch.setattr(Config, 'locale', 'ar_AE')
	attr_type = ATTR.LOCALE()
	attr_type._default = 'test_validate_attr_LOCALE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALE',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_LOCALE'

def test_validate_attr_LOCALE_default_int(monkeypatch):
	from ....config import Config
	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	monkeypatch.setattr(Config, 'locale', 'ar_AE')
	attr_type = ATTR.LOCALE()
	attr_type._default = 'test_validate_attr_LOCALE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALE',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_LOCALE'

def test_validate_attr_LOCALE_default_int_allow_none(monkeypatch):
	from ....config import Config
	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	monkeypatch.setattr(Config, 'locale', 'ar_AE')
	attr_type = ATTR.LOCALE()
	attr_type._default = 'test_validate_attr_LOCALE'
	attr_val = utils.validate_attr(
		attr_name='test_validate_attr_LOCALE',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None