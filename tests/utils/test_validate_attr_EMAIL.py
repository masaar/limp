from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_EMAIL',
			attr_type=ATTR.EMAIL(),
			attr_val=None,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_EMAIL',
			attr_type=ATTR.EMAIL(),
			attr_val=1,
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_EMAIL',
			attr_type=ATTR.EMAIL(),
			attr_val='str',
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_email():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=ATTR.EMAIL(),
		attr_val='info@limp.foobar.baz',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'info@limp.foobar.baz'


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_allowed_domains_email_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_EMAIL',
			attr_type=ATTR.EMAIL(allowed_domains=['foo.com', 'bar.net']),
			attr_val='info@limp.foobar.baz',
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_allowed_domains_strict_email_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_EMAIL',
			attr_type=ATTR.EMAIL(allowed_domains=['foo.com', 'bar.net'], strict=True),
			attr_val='info@sub.foo.com',
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_allowed_domains_email():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=ATTR.EMAIL(allowed_domains=['foo.com', 'bar.net']),
		attr_val='info@sub.foo.com',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'info@sub.foo.com'


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_allowed_domains_strict_email():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=ATTR.EMAIL(allowed_domains=['foo.com', 'bar.net'], strict=True),
		attr_val='info@foo.com',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'info@foo.com'


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_disallowed_domains_email_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_EMAIL',
			attr_type=ATTR.EMAIL(disallowed_domains=['foo.com', 'bar.net']),
			attr_val='info@limp.foo.com',
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_disallowed_domains_strict_email_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_EMAIL',
			attr_type=ATTR.EMAIL(disallowed_domains=['foo.com', 'bar.net'], strict=True),
			attr_val='info@foo.com',
			allow_opers=False,
			allow_none=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_disallowed_domains_email():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=ATTR.EMAIL(disallowed_domains=['foo.com', 'bar.net']),
		attr_val='info@sub.foobar.com',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'info@sub.foobar.com'


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_disallowed_domains_strict_email():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=ATTR.EMAIL(disallowed_domains=['foo.com', 'bar.net'], strict=True),
		attr_val='info@sub.foo.com',
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'info@sub.foo.com'


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=ATTR.EMAIL(),
		attr_val=None,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_default_None():
	attr_type = ATTR.EMAIL()
	attr_type._default = 'test_validate_attr_EMAIL'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_EMAIL'


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_default_int():
	attr_type = ATTR.EMAIL()
	attr_type._default = 'test_validate_attr_EMAIL'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'test_validate_attr_EMAIL'


@pytest.mark.asyncio
async def test_validate_attr_EMAIL_default_int_allow_none():
	attr_type = ATTR.EMAIL()
	attr_type._default = 'test_validate_attr_EMAIL'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_EMAIL',
		attr_type=attr_type,
		attr_val=1,
		allow_opers=True,
		allow_none=True,
	)
	assert attr_val == None
