from limp.base_module import BaseModule, BaseModel
from limp.config import Config
from limp.enums import Event
from limp.classes import (
	ATTR,
	PERM,
	EXTN,
	Query,
	ATTR_MOD,
	Query,
	LIMP_DOC,
	LIMP_QUERY,
	ANALYTIC,
)
from limp.utils import DictObj, extract_attr

from typing import List, Dict, Any, Union
from bson import ObjectId
from passlib.hash import pbkdf2_sha512

import logging, secrets, copy, datetime

logger = logging.getLogger('limp')


class Session(BaseModule):
	'''`Session` module provides data type and controller for sessions in LIMP eco-system. CRUD methods of the module are supposed to used for internal calls only, while methods `auth`, `reauth`, and `signout` are available for use by API as well as internal calls when needed.'''

	collection = 'sessions'
	attrs = {
		'user': ATTR.ID(desc='`_id` of `User` doc the doc belongs to.'),
		'groups': ATTR.LIST(
			desc='List of `_id` for every group the session is authenticated against. This attr is set by `auth` method when called with `groups` Doc Arg for Controller Auth Sequence.',
			list=[
				ATTR.ID(desc='`_id` of Group doc the session is authenticated against.')
			],
		),
		'host_add': ATTR.IP(desc='IP of the host the user used to authenticate.'),
		'user_agent': ATTR.STR(
			desc='User-agent of the app the user used to authenticate.'
		),
		'expiry': ATTR.DATETIME(desc='Python `datetime` ISO format of session expiry.'),
		'token_hash': ATTR.STR(desc='Hashed system-generated session token.'),
		'create_time': ATTR.DATETIME(
			desc='Python `datetime` ISO format of the doc creation.'
		),
	}
	defaults = {'groups': []}
	extns = {'user': EXTN(module='user', force=True)}
	methods = {
		'read': {
			'permissions': [PERM(privilege='read', query_mod={'user': '$__user'})]
		},
		'create': {'permissions': [PERM(privilege='create')]},
		'update': {
			'permissions': [
				PERM(
					privilege='update',
					query_mod={'user': '$__user'},
					doc_mod={'user': None},
				)
			],
			'query_args': {'_id': ATTR.ID()},
		},
		'delete': {
			'permissions': [PERM(privilege='delete', query_mod={'user': '$__user'})],
			'query_args': {'_id': ATTR.ID()},
		},
		'auth': {'permissions': [PERM(privilege='*')], 'doc_args': []},
		'reauth': {
			'permissions': [PERM(privilege='*')],
			'query_args': [
				{
					'_id': ATTR.ID(),
					'token': ATTR.STR(),
					'groups': ATTR.LIST(list=[ATTR.ID()]),
				},
				{'_id': ATTR.ID(), 'token': ATTR.STR()},
			],
		},
		'signout': {
			'permissions': [PERM(privilege='*')],
			'query_args': {'_id': ATTR.ID()},
		},
	}

	async def auth(self, skip_events=[], env={}, query=[], doc={}):
		for attr in Config.modules['user'].unique_attrs:
			if attr in doc.keys():
				key = attr
				break
		user_query = [{key: doc[key], '$limit': 1}]
		if 'groups' in doc.keys():
			user_query.append(
				[{'groups': {'$in': doc['groups']}}, {'privileges': {'*': ['*']}}]
			)
		user_results = await Config.modules['user'].read(
			skip_events=[Event.PERM, Event.ON], env=env, query=user_query
		)
		if not user_results.args.count or not pbkdf2_sha512.verify(
			doc['hash'], user_results.args.docs[0][f'{key}_hash']
		):
			return self.status(
				status=403,
				msg='Wrong auth credentials.',
				args={'code': 'INVALID_CREDS'},
			)
		user = user_results.args.docs[0]

		if Event.ON not in skip_events:
			if user.status in ['banned', 'deleted']:
				return self.status(
					status=403,
					msg=f'User is {user.status}.',
					args={'code': 'INVALID_USER'},
				)
			elif user.status == 'disabled_password':
				return self.status(
					status=403,
					msg='User password is disabled.',
					args={'code': 'INVALID_USER'},
				)

		token = secrets.token_urlsafe(32)
		session = {
			'user': user._id,
			'groups': doc['groups'] if 'groups' in doc.keys() else [],
			'host_add': env['REMOTE_ADDR'],
			'user_agent': env['HTTP_USER_AGENT'],
			'expiry': (
				datetime.datetime.utcnow() + datetime.timedelta(days=30)
			).isoformat(),
			'token_hash': pbkdf2_sha512.using(rounds=100000).hash(token),  # pylint: disable=no-member
		}

		results = await self.create(skip_events=[Event.PERM], env=env, doc=session)
		if results.status != 200:
			return results

		session['_id'] = results.args.docs[0]._id
		session['user'] = user
		del session['token_hash']
		session['token'] = token
		results.args.docs[0] = BaseModel(session)

		# [DOC] read user privileges and return them
		user_results = await Config.modules['user'].read_privileges(
			skip_events=[Event.PERM], env=env, query=[{'_id': user._id}]
		)
		if user_results.status != 200:
			return user_results
		results.args.docs[0]['user'] = user_results.args.docs[0]

		# [DOC] Create CONN_AUTH Analytic doc
		if Config.analytics_events['session_conn_auth']:
			analytic_doc = {
				'event': 'CONN_AUTH',
				'subevent': env['client_app'],
				'args': {
					'user': user_results.args.docs[0]._id,
					'session': results.args.docs[0]._id,
					'REMOTE_ADDR': env['REMOTE_ADDR'],
					'HTTP_USER_AGENT': env['HTTP_USER_AGENT'],
				},
			}
			analytic_results = await Config.modules['analytic'].create(
				skip_events=[Event.PERM], env=env, doc=analytic_doc
			)
			if analytic_results.status != 200:
				logger.error(
					f'Failed to create \'Analytic\' doc: {analytic_doc}. Results: {analytic_results}'
				)
		# [DOC] Create USER_AUTH Analytic doc
		if Config.analytics_events['session_user_auth']:
			analytic_doc = {
				'event': 'USER_AUTH',
				'subevent': user_results.args.docs[0]._id,
				'args': {
					'session': results.args.docs[0]._id,
					'REMOTE_ADDR': env['REMOTE_ADDR'],
					'HTTP_USER_AGENT': env['HTTP_USER_AGENT'],
					'client_app': env['client_app'],
				},
			}
			analytic_results = await Config.modules['analytic'].create(
				skip_events=[Event.PERM], env=env, doc=analytic_doc
			)
			if analytic_results.status != 200:
				logger.error(
					f'Failed to create \'Analytic\' doc: {analytic_doc}. Results: {analytic_results}'
				)

		return self.status(
			status=200,
			msg='You were successfully authed.',
			args={'session': results.args.docs[0]},
		)

	async def reauth(self, skip_events=[], env={}, query=[], doc={}):
		if str(query['_id'][0]) == 'f00000000000000000000012':
			return self.status(
				status=400,
				msg='Reauth is not required for \'__ANON\' user.',
				args={'code': 'ANON_REAUTH'},
			)
		session_query = [{'_id': query['_id'][0]}]
		if 'groups' in query:
			session_query.append({'groups': {'$in': query['groups'][0]}})
		results = await self.read(
			skip_events=[Event.PERM], env=env, query=session_query
		)
		if not results.args.count:
			return self.status(
				status=403, msg='Session is invalid.', args={'code': 'INVALID_SESSION'}
			)

		if not pbkdf2_sha512.verify(query['token'][0], results.args.docs[0].token_hash):
			return self.status(
				status=403,
				msg='Reauth token hash invalid.',
				args={'code': 'INVALID_REAUTH_HASH'},
			)
		del results.args.docs[0]['token_hash']
		results.args.docs[0]['token'] = query['token'][0]

		if results.args.docs[0].expiry < datetime.datetime.utcnow().isoformat():
			results = await self.delete(
				skip_events=[Event.PERM, Event.SOFT],
				env=env,
				query=[{'_id': env['session']._id}],
			)
			return self.status(
				status=403, msg='Session had expired.', args={'code': 'SESSION_EXPIRED'}
			)
		# [DOC] update user's last_login timestamp
		await Config.modules['user'].update(
			skip_events=[Event.PERM],
			env=env,
			query=[{'_id': results.args.docs[0].user}],
			doc={'login_time': datetime.datetime.utcnow().isoformat()},
		)
		await self.update(
			skip_events=[Event.PERM],
			env=env,
			query=[{'_id': results.args.docs[0]._id}],
			doc={
				'expiry': (
					datetime.datetime.utcnow() + datetime.timedelta(days=30)
				).isoformat()
			},
		)
		# [DOC] read user privileges and return them
		user_results = await Config.modules['user'].read_privileges(
			skip_events=[Event.PERM],
			env=env,
			query=[{'_id': results.args.docs[0].user._id}],
		)
		results.args.docs[0]['user'] = user_results.args.docs[0]

		# [DOC] Create CONN_AUTH Analytic doc
		if Config.analytics_events['session_conn_reauth']:
			analytic_doc = {
				'event': 'CONN_REAUTH',
				'subevent': env['client_app'],
				'args': {
					'user': user_results.args.docs[0]._id,
					'session': results.args.docs[0]._id,
					'REMOTE_ADDR': env['REMOTE_ADDR'],
					'HTTP_USER_AGENT': env['HTTP_USER_AGENT'],
				},
			}
			analytic_results = await Config.modules['analytic'].create(
				skip_events=[Event.PERM], env=env, doc=analytic_doc
			)
			if analytic_results.status != 200:
				logger.error(
					f'Failed to create \'Analytic\' doc: {analytic_doc}. Results: {analytic_results}'
				)
		# [DOC] Create USER_AUTH Analytic doc
		if Config.analytics_events['session_user_reauth']:
			analytic_doc = {
				'event': 'USER_REAUTH',
				'subevent': user_results.args.docs[0]._id,
				'args': {
					'session': results.args.docs[0]._id,
					'REMOTE_ADDR': env['REMOTE_ADDR'],
					'HTTP_USER_AGENT': env['HTTP_USER_AGENT'],
					'client_app': env['client_app'],
				},
			}
			analytic_results = await Config.modules['analytic'].create(
				skip_events=[Event.PERM], env=env, doc=analytic_doc
			)
			if analytic_results.status != 200:
				logger.error(
					f'Failed to create \'Analytic\' doc: {analytic_doc}. Results: {analytic_results}'
				)

		return self.status(
			status=200,
			msg='You were successfully reauthed.',
			args={'session': results.args.docs[0]},
		)

	async def signout(self, skip_events=[], env={}, query=[], doc={}):
		if str(query['_id'][0]) == 'f00000000000000000000012':
			return self.status(
				status=400,
				msg='Singout is not allowed for \'__ANON\' user.',
				args={'code': 'ANON_SIGNOUT'},
			)
		results = await self.read(
			skip_events=[Event.PERM], env=env, query=[{'_id': query['_id'][0]}]
		)

		if not results.args.count:
			return self.status(
				status=403, msg='Session is invalid.', args={'code': 'INVALID_SESSION'}
			)
		results = await self.delete(
			skip_events=[Event.PERM], env=env, query=[{'_id': env['session']._id}]
		)

		# [DOC] Create CONN_AUTH Analytic doc
		if Config.analytics_events['session_conn_deauth']:
			analytic_doc = {
				'event': 'CONN_DEAUTH',
				'subevent': env['client_app'],
				'args': {
					'user': env['session'].user._id,
					'session': env['session']._id,
					'REMOTE_ADDR': env['REMOTE_ADDR'],
					'HTTP_USER_AGENT': env['HTTP_USER_AGENT'],
				},
			}
			analytic_results = await Config.modules['analytic'].create(
				skip_events=[Event.PERM], env=env, doc=analytic_doc
			)
			if analytic_results.status != 200:
				logger.error(
					f'Failed to create \'Analytic\' doc: {analytic_doc}. Results: {analytic_results}'
				)
		# [DOC] Create USER_AUTH Analytic doc
		if Config.analytics_events['session_user_deauth']:
			analytic_doc = {
				'event': 'USER_DEAUTH',
				'subevent': env['session'].user._id,
				'args': {
					'session': env['session']._id,
					'REMOTE_ADDR': env['REMOTE_ADDR'],
					'HTTP_USER_AGENT': env['HTTP_USER_AGENT'],
					'client_app': env['client_app'],
				},
			}
			analytic_results = await Config.modules['analytic'].create(
				skip_events=[Event.PERM], env=env, doc=analytic_doc
			)
			if analytic_results.status != 200:
				logger.error(
					f'Failed to create \'Analytic\' doc: {analytic_doc}. Results: {analytic_results}'
				)

		return self.status(
			status=200,
			msg='You are successfully signed-out.',
			args={'session': DictObj({'_id': 'f00000000000000000000012'})},
		)

	def check_permissions(
		self,
		skip_events: List[str],
		env: Dict[str, Any],
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		module: BaseModule,
		permissions: List[PERM],
	):
		user = env['session'].user

		permissions = copy.deepcopy(permissions)

		for permission in permissions:
			logger.debug(
				f'checking permission: {permission} against: {user.privileges}'
			)
			permission_pass = False
			if permission.privilege == '*':
				permission_pass = True

			if not permission_pass:
				if permission.privilege.find('.') == -1:
					permission_module = module.module_name
					permission_attr = permission.privilege
				elif permission.privilege.find('.') != -1:
					permission_module = permission.privilege.split('.')[0]
					permission_attr = permission.privilege.split('.')[1]

				if ('*' in user.privileges.keys()):
					user.privileges[permission_module] = copy.deepcopy(
						user.privileges['*']
					)
				if permission_module in user.privileges.keys():
					if (
						type(user.privileges[permission_module]) == list
						and '*' in user.privileges[permission_module]
					):
						user.privileges[permission_module] += copy.deepcopy(
							module.privileges
						)
				if permission_module not in user.privileges.keys():
					user.privileges[permission_module] = []

				if permission_attr in user.privileges[permission_module]:
					permission_pass = True

			if permission_pass:
				query = self._parse_permission_args(
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					permission_args=permission.query_mod,
				)
				doc = self._parse_permission_args(
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					permission_args=permission.doc_mod,
				)
				return {'query': query, 'doc': doc}
		# [DOC] If all permission checks fail
		return False

	def _parse_permission_args(
		self,
		skip_events: List[str],
		env: Dict[str, Any],
		query: Union[LIMP_QUERY, Query],
		doc: LIMP_DOC,
		permission_args: Any,
	):
		user = env['session'].user

		if type(permission_args) == list:
			args_iter = range(len(permission_args))
		elif type(permission_args) == dict:
			args_iter = list(permission_args.keys())

		for j in args_iter:
			if type(permission_args[j]) == ATTR_MOD:
				# [DOC] If attr is of type ATTR_MOD, call condition callable
				if permission_args[j].condition(
					skip_events=skip_events, env=env, query=query, doc=doc
				):
					# [DOC] If condition return is True, update attr value
					if callable(permission_args[j].default):
						permission_args[j] = permission_args[j].default(
							skip_events=skip_events, env=env, query=query, doc=doc
						)
						if type(permission_args[j]) == Exception:
							raise permission_args[j]
					else:
						permission_args[j] = permission_args[j].default
			elif type(permission_args[j]) == dict:
				# [DOC] Check opers
				for oper in [
					'$gt',
					'$lt',
					'$gte',
					'$lte',
					'$bet',
					'$ne',
					'$regex',
					'$all',
					'$in',
				]:
					if oper in permission_args[j].keys():
						if oper == '$bet':
							permission_args[j]['$bet'] = self._parse_permission_args(
								skip_events=skip_events,
								env=env,
								query=query,
								doc=doc,
								permission_args=permission_args[j]['$bet'],
							)
						else:
							permission_args[j][oper] = self._parse_permission_args(
								skip_events=skip_events,
								env=env,
								query=query,
								doc=doc,
								permission_args=[permission_args[j][oper]],
							)[0]
						# [DOC] Continue the iteration
						continue
				# [DOC] Child args, parse
				permission_args[j] = self._parse_permission_args(
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					permission_args=permission_args[j],
				)
			elif type(permission_args[j]) == list:
				permission_args[j] = self._parse_permission_args(
					skip_events=skip_events,
					env=env,
					query=query,
					doc=doc,
					permission_args=permission_args[j],
				)
			elif type(permission_args[j]) == str:
				# [DOC] Check for variables
				if permission_args[j] == '$__user':
					permission_args[j] = user._id
				elif permission_args[j].startswith('$__user.'):
					permission_args[j] = extract_attr(
						scope=user,
						attr_path=permission_args[j].replace('$__user.', '$__'),
					)
				elif permission_args[j] == '$__access':
					permission_args[j] = {'$__user': user._id, '$__groups': user.groups}
				elif permission_args[j] == '$__datetime':
					permission_args[j] = datetime.datetime.utcnow().isoformat()
				elif permission_args[j] == '$__date':
					permission_args[j] = datetime.date.today().isoformat()
				elif permission_args[j] == '$__time':
					permission_args[j] = datetime.datetime.now().time().isoformat()

		return permission_args
