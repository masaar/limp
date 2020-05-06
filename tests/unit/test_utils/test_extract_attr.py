from limp.utils import extract_attr

from .fixtures import attr_obj


def test_extract_attr_item(attr_obj):
	attr_val = extract_attr(scope=attr_obj, attr_path='item2')
	assert attr_val == 'val2'


def test_extract_attr_list_item(attr_obj):
	attr_val = extract_attr(scope=attr_obj, attr_path='$__list_item1:1')
	assert attr_val == 'list_child2'


def test_extract_attr_dict_item(attr_obj):
	attr_val = extract_attr(scope=attr_obj, attr_path='dict_item1.dict_child2')
	assert attr_val == 'child_val2'


def test_extract_attr_nested_dict_item(attr_obj):
	attr_val = extract_attr(
		scope=attr_obj, attr_path='$__nested_dict.child_dict.child_child_item1'
	)
	assert attr_val == 'child_child_val1'


def test_extract_attr_nested_list_item(attr_obj):
	attr_val = extract_attr(scope=attr_obj, attr_path='nested_list:1:0')
	assert attr_val == 'child_child_item21'


def test_extract_attr_nested_obj_list_item(attr_obj):
	attr_val = extract_attr(scope=attr_obj, attr_path='nested_obj.list:1.item2')
	assert attr_val == 'val2'


def test_extract_attr_nested_obj_dict_item(attr_obj):
	attr_val = extract_attr(scope=attr_obj, attr_path='$__nested_obj.dict.list:0')
	assert attr_val == 'item1'
