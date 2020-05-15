from limp.utils import expand_attr


def test_expand_attr():
	doc = {
		'key_1': {'child_key_1': 'value'},
		'key_1.child_key_2': 'value',
		'key_2.child_key_1': 'value',
		'key_3.child_key_1.grand_child_key_1': 'value',
	}
	expanded_doc = expand_attr(doc=doc)
	assert expanded_doc == {
		'key_1': {'child_key_1': 'value', 'child_key_2': 'value'},
		'key_2': {'child_key_1': 'value'},
		'key_3': {'child_key_1': {'grand_child_key_1': 'value'}},
	}
