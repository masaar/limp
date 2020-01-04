from base_module import BaseModule
from classes import (
	ATTR,
	PERM,
	EXTN,
	ATTR_MOD,
	LIMP_EVENTS,
	LIMP_ENV,
	Query,
	LIMP_QUERY,
	LIMP_DOC,
)
from enums import Event

from typing import Union

import datetime


class Analytic(BaseModule):
	collection = 'analytics'
	attrs = {
		'user': ATTR.ID(),
		'event': ATTR.STR(),
		'subevent': ATTR.ANY(),
		'occurances': ATTR.LIST(
			list=[
				ATTR.DICT(
					dict={
						'args': ATTR.DICT(
							dict={'__key': ATTR.STR(), '__val': ATTR.ANY()}
						),
						'score': ATTR.INT(),
						'create_time': ATTR.DATETIME(),
					}
				)
			]
		),
		'score': ATTR.INT(),
	}
	unique_attrs = [('user', 'event', 'subevent')]
	methods = {
		'read': {'permissions': [PERM(privilege='read')]},
		'create': {
			'permissions': [PERM(privilege='__sys')],
			'doc_args': {
				'event': ATTR.STR(),
				'subevent': ATTR.ANY(),
				'args': ATTR.DICT(dict={'__key': ATTR.STR(), '__val': ATTR.ANY()}),
			},
		},
		'update': {'permissions': [PERM(privilege='__sys')]},
		'delete': {'permissions': [PERM(privilege='delete')]},
	}

	async def pre_create(self, skip_events, env, query, doc, payload):
		analytic_results = await self.read(
			skip_events=[Event.PERM],
			env=env,
			query=[
				{
					'user': env['session'].user._id,
					'event': doc['event'],
					'subevent': doc['subevent'],
				},
				{'$limit': 1},
			],
		)
		if analytic_results.args.count:
			analytic_results = await self.update(
				skip_events=[Event.PERM],
				env=env,
				query=[{'_id': analytic_results.args.docs[0]._id}],
				doc={
					'occurances': {
						'$append': {
							'args': doc['args'],
							'score': doc['score'] if 'score' in doc.keys() else 0,
							'create_time': datetime.datetime.utcnow().isoformat(),
						}
					},
					'score': {'$add': doc['score'] if 'score' in doc.keys() else 0},
				},
			)
			return analytic_results
		else:
			doc = {
				'event': doc['event'],
				'subevent': doc['subevent'],
				'occurances': [
					{
						'args': doc['args'],
						'score': doc['score'] if 'score' in doc.keys() else 0,
						'create_time': datetime.datetime.utcnow().isoformat(),
					}
				],
				'score': doc['score'] if 'score' in doc.keys() else 0,
			}
			return (skip_events, env, query, doc, payload)
