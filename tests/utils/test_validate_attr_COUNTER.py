from limp.classes import ATTR, InvalidAttrTypeException
from limp import utils

from bson import ObjectId

import pytest


@pytest.mark.asyncio
async def test_validate_attr_COUNTER_invalid_type():
	with pytest.raises(InvalidAttrTypeException):
		ATTR.COUNTER(pattern='not-valid-pattern')


@pytest.mark.asyncio
async def test_validate_attr_COUNTER_valid_type():
	from limp.config import Config

	ATTR.COUNTER(
		pattern='O-$__values:0$__values:1$__values:2-$__counters.order_counter'
	)
	assert Config.docs[0]['doc']['var'] == '__counter:order_counter'


@pytest.mark.asyncio
async def test_validate_attr_COUNTER_valid_type():
	from limp.config import Config

	attr_type = ATTR.COUNTER(
		pattern='COUNTER-$__values:0$__values:1$__values:0',
		values=[
			lambda skip_events, env, query, doc: 42,
			lambda skip_events, env, query, doc: 24,
		],
	)
	attr_val = await utils.validate_attr(
		attr_name='test_validate_attr_COUNTER',
		attr_type=attr_type,
		attr_val=None,
		allow_opers=False,
		allow_none=False,
	)
	assert attr_val == 'COUNTER-422442'
