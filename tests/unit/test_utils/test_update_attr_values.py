from ....classes import ATTR
from ....utils import update_attr_values

import pytest

def test_update_attr_values_default_dict():
	attr = ATTR.DICT(dict={'key':ATTR.STR()})
	update_attr_values(attr=attr, value='default', value_path='key', value_val=None)
	assert attr._args['dict']['key']._default == None
