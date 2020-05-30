from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_LOCALES_None(monkeypatch):
	from limp.config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_LOCALES',
			attr_type=ATTR.LOCALES(),
			attr_val=None,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_LOCALES_str_invalid(monkeypatch):
	from limp.config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_LOCALES',
			attr_type=ATTR.LOCALES(),
			attr_val='ar',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_LOCALES_locale(monkeypatch):
	from limp.config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LOCALES',
		attr_type=ATTR.LOCALES(),
		attr_val='en_AE',
		allow_update=False,
	)
	assert attr_val == 'en_AE'


@pytest.mark.asyncio
async def test_validate_attr_LOCALES_None_allow_none(monkeypatch):
	from limp.config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LOCALES',
		attr_type=ATTR.LOCALES(),
		attr_val=None,
		allow_update=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_LOCALES_default_None(monkeypatch):
	from limp.config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	attr_type = ATTR.LOCALES()
	attr_type._default = 'test_validate_attr_LOCALES'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LOCALES',
		attr_type=attr_type,
		attr_val=None,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_LOCALES'


@pytest.mark.asyncio
async def test_validate_attr_LOCALES_default_int(monkeypatch):
	from limp.config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	attr_type = ATTR.LOCALES()
	attr_type._default = 'test_validate_attr_LOCALES'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LOCALES',
		attr_type=attr_type,
		attr_val=1,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_LOCALES'


@pytest.mark.asyncio
async def test_validate_attr_LOCALES_default_int_allow_none(monkeypatch):
	from limp.config import Config

	monkeypatch.setattr(Config, 'locales', ['ar_AE', 'en_AE', 'de_DE'])
	attr_type = ATTR.LOCALES()
	attr_type._default = 'test_validate_attr_LOCALES'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_LOCALES',
		attr_type=attr_type,
		attr_val=1,
		allow_update=True,
	)
	assert attr_val == None
