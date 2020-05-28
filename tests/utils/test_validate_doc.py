from limp.classes import ATTR

import limp.config
import limp.utils

import pytest


@pytest.mark.asyncio
async def test_validate_doc_valid():
    attrs = {
        'attr_str': ATTR.STR(),
        'attr_int': ATTR.INT(),
    }
    doc = {'attr_str':'str', 'attr_int': '42'}
    await limp.utils.validate_doc(doc=doc, attrs=attrs)
    assert doc == {'attr_str':'str', 'attr_int': 42}


@pytest.mark.asyncio
async def test_validate_doc_invalid():
    attrs = {
        'attr_str': ATTR.STR(),
        'attr_int': ATTR.INT(),
    }
    doc = {'attr_str':'str', 'attr_int': 'abc'}
    with pytest.raises(limp.utils.InvalidAttrException):
        await limp.utils.validate_doc(doc=doc, attrs=attrs)


@pytest.mark.asyncio
async def test_validate_doc_invalid_none():
    attrs = {
        'attr_str': ATTR.STR(),
        'attr_int': ATTR.INT(),
    }
    doc = {'attr_str':'str', 'attr_int': None}
    with pytest.raises(limp.utils.MissingAttrException):
        await limp.utils.validate_doc(doc=doc, attrs=attrs)


@pytest.mark.asyncio
async def test_validate_doc_allow_none_valid_none():
    attrs = {
        'attr_str': ATTR.STR(),
        'attr_int': ATTR.INT(),
    }
    doc = {'attr_str':'str', 'attr_int': None}
    await limp.utils.validate_doc(doc=doc, attrs=attrs, allow_none=True, allow_opers=True)
    assert doc == {'attr_str':'str', 'attr_int': None}


@pytest.mark.asyncio
async def test_validate_doc_allow_none_list_int_str(preserve_state):
    with preserve_state(limp.config, 'Config'):
        limp.config.Config.locales = ['ar_AE', 'en_AE']
        limp.config.Config.locale = 'ar_AE'
        attrs = {
            'attr_list_int': ATTR.LIST(list=[ATTR.INT()]),
        }
        doc = {'attr_list_int': {'$append':'1'}}
        await limp.utils.validate_doc(doc=doc, attrs=attrs, allow_none=True, allow_opers=True)
        assert doc == {'attr_list_int': {'$append': 1, '$unique': False}}


@pytest.mark.asyncio
async def test_validate_doc_allow_none_locale_dict_dot_notated(preserve_state):
    with preserve_state(limp.config, 'Config'):
        limp.config.Config.locales = ['ar_AE', 'en_AE']
        limp.config.Config.locale = 'ar_AE'
        attrs = {
            'attr_locale': ATTR.LOCALE(),
        }
        doc = {'attr_locale.ar_AE': 'ar_AE value'}
        await limp.utils.validate_doc(doc=doc, attrs=attrs, allow_none=True, allow_opers=True)
        assert doc == {'attr_locale.ar_AE': 'ar_AE value'}