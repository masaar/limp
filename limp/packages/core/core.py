from limp.base_module import BaseModule
from limp.classes import ATTR, PERM
from limp.config import Config
from limp.utils import extract_lambda_body


class Core(BaseModule):
	'''`Core` module provides access to ADMIN user to fetch `LIMP` instance.'''

	methods = {
		'retrieve_config': {
			'permissions': [PERM(privilege='admin')],
			'query_args': {'config_attr': ATTR.STR()},
		},
		'retrieve_cache_sets': {
			'permissions': [PERM(privilege='admin')],
			'query_args': {'module': ATTR.STR()},
		},
		'retrieve_cache_queries': {
			'permissions': [PERM(privilege='admin')],
			'query_args': {'module': ATTR.STR(), 'cache_set': ATTR.INT()},
		},
		'retrieve_cache_results': {
			'permissions': [PERM(privilege='admin')],
			'query_args': {
				'module': ATTR.STR(),
				'cache_set': ATTR.INT(),
				'query': ATTR.INT(),
			},
		},
	}

	async def retrieve_config(self, skip_events=[], env={}, query=[], doc={}):
		return self.status(
			status=200,
			msg='Config Attr value retrieved.',
			args={'value': getattr(Config, query['config_attr'][0])},
		)

	async def retrieve_cache_sets(self, skip_events=[], env={}, query=[], doc={}):
		return self.status(
			status=200,
			msg='Module Cache Sets retrieved.',
			args={
				'sets': [
					extract_lambda_body(cache_set.condition)
					for cache_set in Config.modules[query['module'][0]].cache
				]
			},
		)

	async def retrieve_cache_queries(self, skip_events=[], env={}, query=[], doc={}):
		return self.status(
			status=200,
			msg='Module Cache Sets queries retrieved.',
			args={
				'queries': list(
					Config.modules[query['module'][0]]
					.cache[query['cache_set'][0]]
					.queries.keys()
				)
			},
		)
		
	async def retrieve_cache_results(self, skip_events=[], env={}, query=[], doc={}):
		cache_set_query = list(
			Config.modules[query['module'][0]]
			.cache[query['cache_set'][0]]
			.queries.keys()
		)[query['query'][0]]
		return self.status(
			status=200,
			msg='Module Cache Sets results retrieved.',
			args={
				'results': Config.modules[query['module'][0]]
				.cache[query['cache_set'][0]]
				.queries[cache_set_query]
				.results,
				'query_time': Config.modules[query['module'][0]]
				.cache[query['cache_set'][0]]
				.queries[cache_set_query]
				.query_time.isoformat(),
			},
		)

