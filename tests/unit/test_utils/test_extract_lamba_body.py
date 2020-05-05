from ....utils import extract_lambda_body


def test_extract_lamba_body_inline():
	lambda_func = lambda x: x * 2
	lambda_func_body = extract_lambda_body(lambda_func=lambda_func)
	assert lambda_func_body == 'lambda_func = lambda x: x * 2'


def test_extract_lamba_body_obj():
	obj = {
		'lambda_func': lambda x: x * 2,
	}
	lambda_func_body = extract_lambda_body(lambda_func=obj['lambda_func'])
	assert lambda_func_body == '\'lambda_func\': lambda x: x * 2'
