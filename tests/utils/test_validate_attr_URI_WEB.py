from limp.classes import ATTR
from limp import utils

import pytest


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_None():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_URI_WEB',
			attr_type=ATTR.URI_WEB(),
			attr_val=None,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_int():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_URI_WEB',
			attr_type=ATTR.URI_WEB(),
			attr_val=1,
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_str_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_URI_WEB',
			attr_type=ATTR.URI_WEB(),
			attr_val='str',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_uri_web_insecure():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(),
		attr_val='http://sub.example.com',
		allow_update=False,
	)
	assert attr_val == 'http://sub.example.com'


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_uri_web_secure():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(),
		attr_val='https://sub.example.com',
		allow_update=False,
	)
	assert attr_val == 'https://sub.example.com'


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_uri_web_params():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(),
		attr_val='https://sub.example.com?param1=something-here&param2=something_else',
		allow_update=False,
	)
	assert (
		attr_val
		== 'https://sub.example.com?param1=something-here&param2=something_else'
	)


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_allowed_domains_uri_web_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_URI_WEB',
			attr_type=ATTR.URI_WEB(allowed_domains=['foo.com', 'bar.net']),
			attr_val='https://sub.example.com',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_allowed_domains_strict_uri_web_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_URI_WEB',
			attr_type=ATTR.URI_WEB(allowed_domains=['foo.com', 'bar.net'], strict=True),
			attr_val='http://sub.bar.net',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_allowed_domains_uri_web():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(allowed_domains=['foo.com', 'bar.net']),
		attr_val='https://sub.foo.com/index?something=value',
		allow_update=False,
	)
	assert attr_val == 'https://sub.foo.com/index?something=value'


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_allowed_domains_strict_uri_web():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(allowed_domains=['foo.com', 'bar.net'], strict=True),
		attr_val='http://bar.net/some-params/and+page',
		allow_update=False,
	)
	assert attr_val == 'http://bar.net/some-params/and+page'


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_disallowed_domains_uri_web_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_URI_WEB',
			attr_type=ATTR.URI_WEB(disallowed_domains=['foo.com', 'bar.net']),
			attr_val='https://sub.foo.com',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_disallowed_domains_strict_uri_web_invalid():
	with pytest.raises(utils.InvalidAttrException):
		await utils.validate_attr(
			attr_name='test_validate_attr_URI_WEB',
			attr_type=ATTR.URI_WEB(disallowed_domains=['foo.com', 'bar.net'], strict=True),
			attr_val='https://bar.net',
			allow_update=False,
		)


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_disallowed_domains_uri_web():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(disallowed_domains=['foo.com', 'bar.net']),
		attr_val='https://sub.foobar.com',
		allow_update=False,
	)
	assert attr_val == 'https://sub.foobar.com'


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_disallowed_domains_strict_uri_web():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(disallowed_domains=['foo.com', 'bar.net'], strict=True),
		attr_val='http://sub.bar.net',
		allow_update=False,
	)
	assert attr_val == 'http://sub.bar.net'


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_None_allow_none():
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=ATTR.URI_WEB(),
		attr_val=None,
		allow_update=True,
	)
	assert attr_val == None


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_default_None():
	attr_type = ATTR.URI_WEB()
	attr_type._default = 'test_validate_attr_URI_WEB'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=attr_type,
		attr_val=None,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_URI_WEB'


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_default_int():
	attr_type = ATTR.URI_WEB()
	attr_type._default = 'test_validate_attr_URI_WEB'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=attr_type,
		attr_val=1,
		allow_update=False,
	)
	assert attr_val == 'test_validate_attr_URI_WEB'


@pytest.mark.asyncio
async def test_validate_attr_URI_WEB_default_int_allow_none():
	attr_type = ATTR.URI_WEB()
	attr_type._default = 'test_validate_attr_URI_WEB'
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_URI_WEB',
		attr_type=attr_type,
		attr_val=1,
		allow_update=True,
	)
	assert attr_val == None
