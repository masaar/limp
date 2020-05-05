from ....classes import ATTR
from ....utils import update_attr_values


def test_update_attr_values_default_dict():
	attr = ATTR.TYPED_DICT(dict={'key': ATTR.STR()})
	update_attr_values(
		attr=ATTR.TYPED_DICT(dict={'attr': attr}),
		value='default',
		value_path='attr.key',
		value_val='test_update_attr_values',
	)
	assert attr._args['dict']['key']._default == 'test_update_attr_values'


def test_update_attr_values_default_list():
	attr = ATTR.LIST(list=[ATTR.STR()])
	update_attr_values(
		attr=ATTR.TYPED_DICT(dict={'attr': attr}),
		value='default',
		value_path='attr:0',
		value_val='test_update_attr_values',
	)
	assert attr._args['list'][0]._default == 'test_update_attr_values'


def test_update_attr_values_default_dict_nested_list():
	attr = ATTR.TYPED_DICT(dict={'key': ATTR.LIST(list=[ATTR.STR()])})
	update_attr_values(
		attr=ATTR.TYPED_DICT(dict={'attr': attr}),
		value='default',
		value_path='attr.key:0',
		value_val='test_update_attr_values',
	)
	assert (
		attr._args['dict']['key']._args['list'][0]._default == 'test_update_attr_values'
	)


def test_update_attr_values_default_list_dict():
	attr = ATTR.LIST(list=[ATTR.TYPED_DICT(dict={'key': ATTR.STR()})])
	update_attr_values(
		attr=ATTR.TYPED_DICT(dict={'attr': attr}),
		value='default',
		value_path='attr:0.key',
		value_val='test_update_attr_values',
	)
	assert (
		attr._args['list'][0]._args['dict']['key']._default == 'test_update_attr_values'
	)
