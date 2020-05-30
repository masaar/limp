from limp.classes import ATTR
from limp import utils, config

import pytest


@pytest.mark.asyncio
async def test_validate_doc_valid():
    attrs = {
        'attr_str': ATTR.STR(),
        'attr_int': ATTR.INT(),
    }
    doc = {'attr_str':'str', 'attr_int': '42'}
    await utils.validate_doc(doc=doc, attrs=attrs)
    assert doc == {'attr_str':'str', 'attr_int': 42}


@pytest.mark.asyncio
async def test_validate_doc_invalid():
    attrs = {
        'attr_str': ATTR.STR(),
        'attr_int': ATTR.INT(),
    }
    doc = {'attr_str':'str', 'attr_int': 'abc'}
    with pytest.raises(utils.InvalidAttrException):
        await utils.validate_doc(doc=doc, attrs=attrs)


@pytest.mark.asyncio
async def test_validate_doc_invalid_none():
    attrs = {
        'attr_str': ATTR.STR(),
        'attr_int': ATTR.INT(),
    }
    doc = {'attr_str':'str', 'attr_int': None}
    with pytest.raises(utils.MissingAttrException):
        await utils.validate_doc(doc=doc, attrs=attrs)


@pytest.mark.asyncio
async def test_validate_doc_allow_update_valid_none():
    attrs = {
        'attr_str': ATTR.STR(),
        'attr_int': ATTR.INT(),
    }
    doc = {'attr_str':'str', 'attr_int': None}
    await utils.validate_doc(doc=doc, attrs=attrs, allow_update=True)
    assert doc == {'attr_str':'str', 'attr_int': None}


@pytest.mark.asyncio
async def test_validate_doc_allow_update_list_int_str(preserve_state):
    with preserve_state(config, 'Config'):
        config.Config.locales = ['ar_AE', 'en_AE']
        config.Config.locale = 'ar_AE'
        attrs = {
            'attr_list_int': ATTR.LIST(list=[ATTR.INT()]),
        }
        doc = {'attr_list_int': {'$append':'1'}}
        await utils.validate_doc(doc=doc, attrs=attrs, allow_update=True)
        assert doc == {'attr_list_int': {'$append': 1, '$unique': False}}


@pytest.mark.asyncio
async def test_validate_doc_allow_update_locale_dict_dot_notated(preserve_state):
    with preserve_state(config, 'Config'):
        config.Config.locales = ['ar_AE', 'en_AE']
        config.Config.locale = 'ar_AE'
        attrs = {
            'attr_locale': ATTR.LOCALE(),
        }
        doc = {'attr_locale.ar_AE': 'ar_AE value'}
        await utils.validate_doc(doc=doc, attrs=attrs, allow_update=True)
        assert doc == {'attr_locale.ar_AE': 'ar_AE value'}


@pytest.mark.asyncio
async def test_validate_doc_allow_update_kv_dict_typed_dict_time_dict_dot_notated():
    attrs = {
        'shift': ATTR.KV_DICT(key=ATTR.STR(pattern=r'[0-9]{2}'), val=ATTR.TYPED_DICT(dict={'start':ATTR.TIME(), 'end':ATTR.TIME()}))
    }
    doc = {'shift.01.start': '09:00'}
    await utils.validate_doc(doc=doc, attrs=attrs, allow_update=True)
    assert doc == {'shift.01.start': '09:00'}


@pytest.mark.asyncio
async def test_validate_doc_allow_update_list_str_dict_dot_notated():
    attrs = {
        'tags': ATTR.LIST(list=[ATTR.INT(), ATTR.STR()])
    }
    doc = {'tags.0': 'new_tag_val'}
    await utils.validate_doc(doc=doc, attrs=attrs, allow_update=True)
    assert doc == {'tags.0': 'new_tag_val'}


@pytest.mark.asyncio
async def test_validate_doc_allow_update_list_typed_dict_locale_dot_notated(preserve_state):
    with preserve_state(config, 'Config'):
        config.Config.locales = ['en_GB', 'jp_JP']
        config.Config.locale = 'en_GB'
        attrs = {
            'val': ATTR.LIST(list=[ATTR.TYPED_DICT(dict={'address':ATTR.LOCALE(), 'coords':ATTR.GEO()})])
        }
        doc = {'val.0.address.jp_JP': 'new_address'}
        await utils.validate_doc(doc=doc, attrs=attrs, allow_update=True)
        assert doc == {'val.0.address.jp_JP': 'new_address'}


@pytest.mark.asyncio
async def test_validate_doc_allow_update_list_typed_dict_locale_dict_dot_notated(preserve_state):
    with preserve_state(config, 'Config'):
        config.Config.locales = ['en_GB', 'jp_JP']
        config.Config.locale = 'en_GB'
        attrs = {
            'val': ATTR.LIST(list=[ATTR.TYPED_DICT(dict={'address':ATTR.LOCALE(), 'coords':ATTR.GEO()})])
        }
        doc = {
            'val.0.address': {'en_GB' :'new_address'}
        }
        await utils.validate_doc(doc=doc, attrs=attrs, allow_update=True)
        assert doc == {
            'val.0.address': {
                'jp_JP': 'new_address',
                'en_GB': 'new_address',
            }
        }


@pytest.mark.asyncio
async def test_validate_doc_allow_update_list_typed_dict_locale_str_dot_notated(preserve_state):
    with preserve_state(config, 'Config'):
        config.Config.locales = ['en_GB', 'jp_JP']
        config.Config.locale = 'en_GB'
        attrs = {
            'val': ATTR.LIST(list=[ATTR.TYPED_DICT(dict={'address':ATTR.LOCALE(), 'coords':ATTR.GEO()})])
        }
        doc = {
            'val.0.address.jp_JP': 'new_address'
        }
        await utils.validate_doc(doc=doc, attrs=attrs, allow_update=True)
        assert doc == {
            'val.0.address.jp_JP': 'new_address'
        }