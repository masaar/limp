# Quick Start
> Make sure you have MongoDB daemon working before proceeding. The daemon should accept connections on the hostname `localhost` on the default port `27017`. There should be no admin user created in order to allow LIMPd to create the database on your behalf. If any of these conditions don't apply in your case, go to the full [tutorial](/tutorial.md) which lets you create a package with the ability to connect to any `data_server`.

To begin with LIMP, clone this repo in your working directory. Next, clone [LIMP Sample App](https://github.com/masaar/limp-sample-app) into the `modules` folder, like:
```bash
git clone https://github.com/masaar/limp
cd limp/modules
git clone https://github.com/masaar/limp-sample-app
```

Once both repos are cloned, you can install LIMP dependencies using the command:
```bash
python limpd.py --install-deps
```
Note that, LIMPd currently doesn't check the exit status of the `pip` commands executed, which means you have to check the console output yourself to confirm the installation of all the dependencies is successful. Once the process is done successfully you can run LIMPd using the following command:
```bash
python limpd.py --env dev --debug
```
If odds are in your favour (and ours) you should have this by the second last line in the console:
```
======== Running on http://0.0.0.0:8081 ========
```

# Under the Hood
When LIMPd runs, it connects to the `data_server` specified in https://github.com/masaar/limp-sample-app/blob/master/__init__.py#L9 and then attempts to access https://github.com/masaar/limp-sample-app/blob/master/__init__.py#L15 database. This behaviour is introduced in LIMPd for two reasons:
1. Confirm the `data` attrs are valid for when the app starts serving.
2. Create the necessary config collections and docs.

If you look at the full console output you should get:
```
2019-05-18 12:32:23,788  [DEBUG]  Testing realm mode.
2019-05-18 12:32:23,789  [DEBUG]  Testing users collection.
2019-05-18 12:32:23,789  [DEBUG]  Calling: <class 'modules.core.user.User'>.read, with sid:None, query:{'_id': {'val': 'f00000000000000000000010'}}, doc.keys:dict_keys([])
2019-05-18 12:32:23,790  [DEBUG]  testing args, list: query, args: {'_id': {'val': 'f00000000000000000000010'}}
2019-05-18 12:32:23,790  [DEBUG]  testing args, list: doc, args: {}
2019-05-18 12:32:23,791  [DEBUG]  attempting to parse query: {'_id': {'val': 'f00000000000000000000010'}}
2019-05-18 12:32:23,808  [DEBUG]  final query: Collection(Database(MongoClient(host=['localhost:27017'], document_class=dict, tz_aware=False, connect=True, ssl=False), 'limp_data'), 'users'), [{'$match': {'$or': [{'__deleted': {'$exists': False}}, {'__deleted': False}]}}, {'$match': {'_id': ObjectId('f00000000000000000000010')}}, {'$group': {'username': {'$first': '$username'}, 'email': {'$first': '$email'}, 'name': {'$first': '$name'}, 'bio': {'$first': '$bio'}, 'address': {'$first': '$address'}, 'postal_code': {'$first': '$postal_code'}, 'phone': {'$first': '$phone'}, 'website': {'$first': '$website'}, 'locale': {'$first': '$locale'}, 'create_time': {'$first': '$create_time'}, 'login_time': {'$first': '$login_time'}, 'groups': {'$first': '$groups'}, 'privileges': {'$first': '$privileges'}, 'username_hash': {'$first': '$username_hash'}, 'email_hash': {'$first': '$email_hash'}, 'phone_hash': {'$first': '$phone_hash'}, 'status': {'$first': '$status'}, 'attrs': {'$first': '$attrs'}, '_id': '$_id'}}, {'$sort': {'_id': -1}}].
2019-05-18 12:32:23,814  [DEBUG]  Calling: <class 'modules.core.user.User'>.read, with sid:None, query:{'_id': {'val': 'f00000000000000000000011'}}, doc.keys:dict_keys([])
2019-05-18 12:32:23,815  [DEBUG]  testing args, list: query, args: {'_id': {'val': 'f00000000000000000000011'}}
2019-05-18 12:32:23,816  [DEBUG]  testing args, list: doc, args: {}
2019-05-18 12:32:23,816  [DEBUG]  attempting to parse query: {'_id': {'val': 'f00000000000000000000011'}}
2019-05-18 12:32:23,818  [DEBUG]  final query: Collection(Database(MongoClient(host=['localhost:27017'], document_class=dict, tz_aware=False, connect=True, ssl=False), 'limp_data'), 'users'), [{'$match': {'$or': [{'__deleted': {'$exists': False}}, {'__deleted': False}]}}, {'$match': {'_id': ObjectId('f00000000000000000000011')}}, {'$group': {'username': {'$first': '$username'}, 'email': {'$first': '$email'}, 'name': {'$first': '$name'}, 'bio': {'$first': '$bio'}, 'address': {'$first': '$address'}, 'postal_code': {'$first': '$postal_code'}, 'phone': {'$first': '$phone'}, 'website': {'$first': '$website'}, 'locale': {'$first': '$locale'}, 'create_time': {'$first': '$create_time'}, 'login_time': {'$first': '$login_time'}, 'groups': {'$first': '$groups'}, 'privileges': {'$first': '$privileges'}, 'username_hash': {'$first': '$username_hash'}, 'email_hash': {'$first': '$email_hash'}, 'phone_hash': {'$first': '$phone_hash'}, 'status': {'$first': '$status'}, 'attrs': {'$first': '$attrs'}, '_id': '$_id'}}, {'$sort': {'_id': -1}}].
2019-05-18 12:32:23,825  [DEBUG]  Testing sessions collection.
2019-05-18 12:32:23,825  [DEBUG]  Calling: <class 'modules.core.session.Session'>.read, with sid:None, query:{'_id': {'val': 'f00000000000000000000012'}}, doc.keys:dict_keys([])
2019-05-18 12:32:23,826  [DEBUG]  testing args, list: query, args: {'_id': {'val': 'f00000000000000000000012'}}
2019-05-18 12:32:23,826  [DEBUG]  testing args, list: doc, args: {}
2019-05-18 12:32:23,826  [DEBUG]  attempting to parse query: {'_id': {'val': 'f00000000000000000000012'}}
2019-05-18 12:32:23,828  [DEBUG]  final query: Collection(Database(MongoClient(host=['localhost:27017'], document_class=dict, tz_aware=False, connect=True, ssl=False), 'limp_data'), 'sessions'), [{'$match': {'$or': [{'__deleted': {'$exists': False}}, {'__deleted': False}]}}, {'$match': {'_id': ObjectId('f00000000000000000000012')}}, {'$group': {'user': {'$first': '$user'}, 'host_add': {'$first': '$host_add'}, 'user_agent': {'$first': '$user_agent'}, 'timestamp': {'$first': '$timestamp'}, 'expiry': {'$first': '$expiry'}, 'token': {'$first': '$token'}, '_id': '$_id'}}, {'$sort': {'_id': -1}}].
2019-05-18 12:32:23,834  [DEBUG]  Calling: <class 'modules.core.user.User'>.read, with sid:None, query:{'_id': {'val': ObjectId('f00000000000000000000011')}, '$limit': 1}, doc.keys:dict_keys([])
2019-05-18 12:32:23,835  [DEBUG]  testing args, list: query, args: {'_id': {'val': ObjectId('f00000000000000000000011')}, '$limit': 1}
2019-05-18 12:32:23,836  [DEBUG]  testing args, list: doc, args: {}
2019-05-18 12:32:23,836  [DEBUG]  attempting to parse query: {'_id': {'val': ObjectId('f00000000000000000000011')}, '$limit': 1}
2019-05-18 12:32:23,838  [DEBUG]  final query: Collection(Database(MongoClient(host=['localhost:27017'], document_class=dict, tz_aware=False, connect=True, ssl=False), 'limp_data'), 'users'), [{'$match': {'$or': [{'__deleted': {'$exists': False}}, {'__deleted': False}]}}, {'$match': {'_id': ObjectId('f00000000000000000000011')}}, {'$group': {'username': {'$first': '$username'}, 'email': {'$first': '$email'}, 'name': {'$first': '$name'}, 'bio': {'$first': '$bio'}, 'address': {'$first': '$address'}, 'postal_code': {'$first': '$postal_code'}, 'phone': {'$first': '$phone'}, 'website': {'$first': '$website'}, 'locale': {'$first': '$locale'}, 'create_time': {'$first': '$create_time'}, 'login_time': {'$first': '$login_time'}, 'groups': {'$first': '$groups'}, 'privileges': {'$first': '$privileges'}, 'username_hash': {'$first': '$username_hash'}, 'email_hash': {'$first': '$email_hash'}, 'phone_hash': {'$first': '$phone_hash'}, 'status': {'$first': '$status'}, 'attrs': {'$first': '$attrs'}, '_id': '$_id'}}, {'$sort': {'_id': -1}}, {'$limit': 1}].
2019-05-18 12:32:23,843  [DEBUG]  Testing groups collection.
2019-05-18 12:32:23,843  [DEBUG]  Calling: <class 'modules.core.user.Group'>.read, with sid:None, query:{'_id': {'val': 'f00000000000000000000013'}}, doc.keys:dict_keys([])
2019-05-18 12:32:23,844  [DEBUG]  testing args, list: query, args: {'_id': {'val': 'f00000000000000000000013'}}
2019-05-18 12:32:23,844  [DEBUG]  testing args, list: doc, args: {}
2019-05-18 12:32:23,845  [DEBUG]  attempting to parse query: {'_id': {'val': 'f00000000000000000000013'}}
2019-05-18 12:32:23,848  [DEBUG]  final query: Collection(Database(MongoClient(host=['localhost:27017'], document_class=dict, tz_aware=False, connect=True, ssl=False), 'limp_data'), 'groups'), [{'$match': {'$or': [{'__deleted': {'$exists': False}}, {'__deleted': False}]}}, {'$match': {'_id': ObjectId('f00000000000000000000013')}}, {'$group': {'user': {'$first': '$user'}, 'name': {'$first': '$name'}, 'bio': {'$first': '$bio'}, 'privileges': {'$first': '$privileges'}, 'attrs': {'$first': '$attrs'}, '_id': '$_id'}}, {'$sort': {'_id': -1}}].
2019-05-18 12:32:23,853  [DEBUG]  Testing app-specific groups collection.
2019-05-18 12:32:23,853  [DEBUG]  Testing data indexes
2019-05-18 12:32:23,854  [DEBUG]  Testing docs.
2019-05-18 12:32:23,855  [DEBUG]  Loaded modules: {'diff': {'user': 'id', 'module': 'str', 'doc': 'id', 'vars': 'attrs', 'remarks': 'str', 'create_time': 'time'}, 'notification': {'user': 'id', 'create_time': 'time', 'notify_time': 'time', 'title': 'str', 'content': 'id', 'status': ('new', 'snooze', 'done')}, 'session': {'user': 'id', 'host_add': 'ip', 'user_agent': 'str', 'timestamp': 'time', 'expiry': 'time', 'token': 'str'}, 'setting': {'var': 'str', 'val': 'any', 'type': ('global', 'user'), 'user': 'id'}, 'group': {'user': 'id', 'name': {'ar_AE': 'str', 'en_AE': 'str'}, 'bio': {'ar_AE': 'str', 'en_AE': 'str'}, 'privileges': 'privileges', 'attrs': 'attrs'}, 'user': {'username': 'str', 'email': 'email', 'name': {'ar_AE': 'str', 'en_AE': 'str'}, 'bio': {'ar_AE': 'str', 'en_AE': 'str'}, 'address': {'ar_AE': 'str', 'en_AE': 'str'}, 'postal_code': 'str', 'phone': 'phone', 'website': 'uri:web', 'locale': 'locales', 'create_time': 'time', 'login_time': 'time', 'groups': ['id'], 'privileges': 'privileges', 'username_hash': 'str', 'email_hash': 'str', 'phone_hash': 'str', 'status': ('active', 'banned', 'deleted', 'disabled_password'), 'attrs': 'attrs'}, 'blog': {'user': 'id', 'status': ('scheduled', 'draft', 'pending', 'rejected', 'published'), 'title': {'ar_AE': 'str', 'en_AE': 'str'}, 'subtitle': {'ar_AE': 'str', 'en_AE': 'str'}, 'permalink': 'str', 'content': {'ar_AE': 'str', 'en_AE': 'str'}, 'tags': ['str'], 'cat': 'id', 'access': 'access', 'create_time': 'time', 'expiry_time': 'time'}, 'blog_cat': {'user': 'id', 'title': {'ar_AE': 'str', 'en_AE': 'str'}, 'desc': {'ar_AE': 'str', 'en_AE': 'str'}}, 'staff': {'user': 'id', 'photo': 'file', 'name': {'ar_AE': 'str', 'en_AE': 'str'}, 'jobtitle': {'ar_AE': 'str', 'en_AE': 'str'}, 'bio': {'ar_AE': 'str', 'en_AE': 'str'}, 'create_time': 'create_time'}}
2019-05-18 12:32:23,860  [DEBUG]  Config has attrs: {'__module__': 'config', 'debug': True, 'test': None, 'test_flush': False, 'test_force': False, 'tests': {}, 'data_driver': 'mongodb', 'data_server': 'mongodb://localhost', 'data_name': 'limp_data', 'data_ssl': False, 'data_ca_name': None, 'data_ca': None, 'data_azure_mongo': False, 'sms_auth': {}, 'email_auth': {}, 'locales': ['ar_AE', 'en_AE'], 'locale': 'ar_AE', 'events': {}, 'templates': {}, 'l10n': {}, 'admin_username': '__ADMIN', 'admin_email': 'ADMIN@LIMP.MASAAR.COM', 'admin_phone': '+971500000000', 'admin_password': '__ADMIN', 'anon_token': '__ANON_TOKEN_f00000000000000000000012', 'anon_privileges': {}, 'groups': [], 'default_privileges': {}, 'data_indexes': [], 'docs': [], 'realm': False, 'config_data': <classmethod object at 0x000001445D805588>, 'compile_anon_user': <classmethod object at 0x000001445D8055C0>, 'compile_anon_session': <classmethod object at 0x000001445D805668>, '__dict__': <attribute '__dict__' of 'Config' objects>, '__weakref__': <attribute '__weakref__' of 'Config' objects>, '__doc__': None}
======== Running on http://0.0.0.0:8081 ========
(Press CTRL+C to quit)
```
Let's go through the main points:
1. LIMPd checks if app is running in [realm](/realm.md) mode.
2. LIMPd checks if app is running on Azure by confirming `data_azure_mongo` mode.
3. LIMPd checks `users` collection, and creates `ADMIN` and `ANON` users if not present.
4. LIMPd checks `sessions` collection, and creates `ANON` session required to receive and accept calls from non-authenticated users.
5. LIMPd checks `groups` collection, and creates `DEFAULT` group required to set the `default_privileges` of the users.