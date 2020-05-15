from limp.utils import set_attr


def test_set_attr_item(attr_obj):
	set_attr(scope=attr_obj, attr_path='item2', value='test_set_attr_item')
	assert attr_obj['item2'] == 'test_set_attr_item'


def test_set_attr_list_item(attr_obj):
	set_attr(
		scope=attr_obj, attr_path='$__list_item1:1', value='test_set_attr_list_item'
	)
	assert attr_obj['list_item1'][1] == 'test_set_attr_list_item'


def test_set_attr_dict_item(attr_obj):
	set_attr(
		scope=attr_obj,
		attr_path='dict_item1.dict_child2',
		value='test_set_attr_dict_item',
	)
	assert attr_obj['dict_item1']['dict_child2'] == 'test_set_attr_dict_item'


def test_set_attr_nested_dict_item(attr_obj):
	set_attr(
		scope=attr_obj,
		attr_path='$__nested_dict.child_dict.child_child_item1',
		value='test_set_attr_nested_dict_item',
	)
	assert (
		attr_obj['nested_dict']['child_dict']['child_child_item1']
		== 'test_set_attr_nested_dict_item'
	)


def test_set_attr_nested_list_item(attr_obj):
	set_attr(
		scope=attr_obj,
		attr_path='nested_list:1:0',
		value='test_set_attr_nested_list_item',
	)
	assert attr_obj['nested_list'][1][0] == 'test_set_attr_nested_list_item'


def test_set_attr_nested_obj_list_item(attr_obj):
	set_attr(
		scope=attr_obj,
		attr_path='nested_obj.list:1.item2',
		value='test_set_attr_nested_obj_list_item',
	)
	assert (
		attr_obj['nested_obj']['list'][1]['item2']
		== 'test_set_attr_nested_obj_list_item'
	)


def test_set_attr_nested_obj_dict_item(attr_obj):
	set_attr(
		scope=attr_obj,
		attr_path='$__nested_obj.dict.list:0',
		value='test_set_attr_nested_obj_dict_item',
	)
	assert (
		attr_obj['nested_obj']['dict']['list'][0]
		== 'test_set_attr_nested_obj_dict_item'
	)
