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
	'''`Analytic` module provides data type and controller from `Analytics Workflow` and accompanying analytics docs. It uses `pre_create` handler to assure no events duplications occur and all occurrences of the same event are recorded in one doc.'''
	collection = 'analytics'
	attrs = {
		'user': ATTR.ID(desc='`_id` of `User` doc the doc belongs to.'),
		'event': ATTR.STR(desc='Analytics event name.'),
		'subevent': ATTR.ANY(desc='Analytics subevent distinguishing attribute. This is usually `STR`, or `ID` but it is introduced in the module as `ANY` to allow wider use-cases by developers.'),
		'date': ATTR.DATE(desc='Analytics event date. This allows clustering of events occurances to limit doc size.'),
		'occurrences': ATTR.LIST(
			desc='All occurrences of the event as list.',
			list=[
				ATTR.DICT(
					desc='Single occurrence of the event details.',
					dict={
						'args': ATTR.DICT(
							desc='Key-value `dict` containing event args, if any.',
							dict={'__key': ATTR.STR(), '__val': ATTR.ANY()}
						),
						'score': ATTR.INT(desc='Numerical score for occurrence of the event.'),
						'create_time': ATTR.DATETIME(desc='Python `datetime` ISO format of the occurrence of the event.'),
					}
				)
			]
		),
		'score': ATTR.INT(desc='Total score of all scores of all occurrences of the event. This can be used for data analysis.'),
	}
	unique_attrs = [('user', 'event', 'subevent', 'date')]
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
					'date': datetime.date.today().isoformat(),
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
					'occurrences': {
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
				'date': datetime.date.today().isoformat(),
				'occurrences': [
					{
						'args': doc['args'],
						'score': doc['score'] if 'score' in doc.keys() else 0,
						'create_time': datetime.datetime.utcnow().isoformat(),
					}
				],
				'score': doc['score'] if 'score' in doc.keys() else 0,
			}
			return (skip_events, env, query, doc, payload)
