[Back to Index](/README.md)

# Quick Start
> Make sure you have MongoDB daemon working before proceeding. The daemon should accept connections on the hostname `localhost` on the default port `27017`. There should be no admin user created in order to allow LIMPd to create the database on your behalf. If any of these conditions don't apply in your case, go to the full [tutorial](/docs/tutorial.md) which lets you create a package with the ability to connect to any `data_server`.

To begin with LIMP, clone this repo in your working directory. Next, clone [LIMP Sample App](https://github.com/masaar/limp-sample-app) into the `modules` folder, like:
```bash
git clone https://github.com/masaar/limp
cd limp/modules
git clone https://github.com/masaar/limp-sample-app
```

## Install Dependencies
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
When LIMPd runs, it connects to the `data_server` specified in https://github.com/masaar/limp-sample-app/__init__.py#L9 and then attempts to access https://github.com/masaar/limp-sample-app/__init__.py#L15 database. This behaviour is introduced in LIMPd for two reasons:
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
1. LIMPd checks if app is running in [realm](/docs/realm.md) mode.
2. LIMPd checks if app is running on Azure by confirming `data_azure_mongo` mode.
3. LIMPd checks `users` collection, and creates `ADMIN` and `ANON` users if not present.
4. LIMPd checks `sessions` collection, and creates `ANON` session required to receive and accept calls from non-authenticated users.
5. LIMPd checks `groups` collection, and creates `DEFAULT` group required to set the `default_privileges` of the users.
6. LIMPd checks loaded config `groups` and creates them.
7. LIMPd checks loaded config `data_indexes` and creates them.
8. LIMPd checks loaded config `docs` and creates them.
9. Once all previous checks are done, LIMP would be ready ro serve connections on `http://localhost:8081` for `HTTP/1 GET` interface, and `ws://localhost:8081/ws` for `HTTP/2 Websocket` interface.

# Interacting with LIMP
To start interacting with `limp-sample-app` you just run, go to [LIMP Sandbox on Github](https://masaar.github.io/limp-sandbox/dist/limp-sandbox/). Which is a tool we originally built to test early versions of [LIMP SDK for Angular](https://github.com/masaar/ng-limp), but continued to be develop as standalone sandbox playground.

To begin using LIMP Sandbox, from first panel `SDK Init` click on `init()` button, which would connect to LIMP on the specified `API URI` using `API Anon Token`. Note that in Firefox we observed the behaviour where the browser would refuse to connect to local websockets served over the insecure `ws` protocol. If you are on Firefox, use any Chromium-based browser instead. If you see a successful connection message in the output area then, congrats! Your setup is working. Then you can start by sending an `auth`entication call using the default credentials for the `ADMIN` user using:
```
ADMIN@LIMP.MASAAR.COM
__ADMIN
```
You should see a new message in the output indicating that you were 'authed' as well as the session data. Following you can make some calls to your app using the `SDK Call` panel. For instance you can query all the users by passing the following values:
```
endpoint: user/read
query: []
doc: {}
```
This should give you additional messages in the output with two users: `ADMIN` and `ANON` users. To query a specific user, pass its `_id` value as a query param `_id`.

Since you are using `limp-sample-app` you should explore the following modules and endpoints:

## Introduction
Our `limp-sample-app` is an app representing a company website. It has a blog that is served and managed using `Blog` and `BlogCat` modules, as well as staff directory served and managed using `Staff` module.

## Staff
To begin with this module, we would explore the four operations of `CRUD`:

### Create
To create a new staff doc, or any docs at all in the LIMP ecosystem, you call the module `create` method using the endpoint `staff/create`.

Start by setting `Endpoint` in `SDK Call` to `staff/create`. Next Start adding the following `doc` attrs using the `+` button next to `Doc`. LIMP Sandbox has the ability to allow developers to add multiple attrs at once, either in the `doc` or `query` object. After you click on `+` button you would be greeted with a prompt box asking you the names of the attrs you want to add. Copy and paste in the prompt box the following: `photo,name,jobtitle,bio` and then click on `Ok`. You would notice new four fields are now present under the `Doc` section of `SDK Call` panel.

Change attr `photo` type to `file` from the select menu before the text input. All other fields should be changed to type `locale`. These types are just example of how much LIMP is powerful is it allows you to deal with all data types without being worried at all about how your app has to deal with them. In part this is possible because `HTTP/2 Websocket` protocol allows typed-JSON data to be transmitted bi-directionally, but also because LIMP has sophisticated workflow to handle data types.

Once you change the types you would notice `photo` attr field is now a file input, while other attrs are having two input fields each; `val.ar_AE` and `val.en_AE`. Since LIMP was developed by Masaar which is serving customers with multi-language requirements, this feature was built right in the core of LIMP. You can learn more about such features by referring to [Apps Localisation](/apps-localisation.md). Now let's create the first staff by inputting some data in all the attrs, and then click on `call()`. Make sure you have already been `auth`enticated as `ADMIN` as currently there's no other user which has the [privilege](/docs/tutorial.md#privileges) to create staff docs. If the call is successful you would get `Created 1 docs.` message. Repeat the same steps again with other set of details to create another staff doc.

### Read
Similar to `create` operation, LIMP follows and has `read` method on any module which had it enabled. Set `Endpoint` to `staff/read`, remove all the doc attrs and click on `call()`. You should receive `Found 2 docs.` message response. If you attempt to expand the JSON tree viewer, you would find both the docs in `args.docs`. That's how LIMP messages are always structured--Any matched data is always sent as part of the `args` object in the response. Now, to read specifically either of the staff docs, all you have to do is click on `+` button next to `Query` and type `_id` in the prompt box. This would create a `query` object arg `_id` that you see present under `Query`. Copy one of the `_id`s of the two docs and paste it in the `_id` text input, and click `call()`. If you copied that correctly you should receive `Found 1 docs.` message response with the details of that doc. Now you know how to query all docs in any module, or selectively query them. You can read more about [query object](/docs/tutorial.md#query-object) in the tutorial.

One last thing, we uploaded a photo for the staff, so how can we get it? For many technical reasons we resided on stripping any files from the response of any call. And, to get those files `HTTP/1 GET` interface is present. In our `Staff` module case you have the following link scheme available:
```
http://localhost:8081/staff/retrieve_file/{_id}/photo;{file_name}
```
This scheme is a public scheme available for any module to use. You can learn more about it in [retrieve_file method](/docs/tutorial.md#retrieve_file-method) section in the tutorial. For instance, copy either of the `_id` of the two created docs, and replace `{_id}` with that value, and similarly replace `{file_name}` with the photo file name. This scheme checks the file name when retrieving the photo, so if the name is not matching you would get `{"status": 404, "msg": "Requested content not found."}` in your browser. If the values are correct you would be presented with the photo you uploaded.

### Update
To update either of the staff docs simply use the LIMP ecosystem `update` method--Use the following details in `SDK Call` panel:
```
endpoint: staff/update
query: [{_id: 'staff doc _id'}]
doc: {attr_name: 'new_value'}
```
If the previous snippet is not clear enough, the idea is you can `update` any doc using any module `update` method, by simply passing `_id` of the doc you are looking to update and the attrs value you would like to change. Notice that you don't have to send the full doc again, just the attrs you want to change its value.

### Delete
To delete either of the docs your call should be:
```
endpoint: staff/delete
query: [{_id: 'staff doc _id'}]
```

## Blog
Blog and BlogCat module are having the same identical `read`, `create`, `update` and `delete` methods to both modules. The only difference here is that `Blog` and `BlogCat` modules are linked--Every blog doc is linked to a blog_cat doc. It's the same structure you get on any blogging platform and/or software. For that you need to create the blog_cat first, take its `_id` and give it to a blog you want to create.

For starter create your blog_cat using the following call:
```
endpoint: blog_cat/create
doc: title[;locale title], desc[;locale desc]
```
Keep the `_id` of this category handy.

Then, let's create a blog doc, using the call:
```
endpoint: blog/create
doc: {title:'locale title', content:'locale content', cat:'blog cat _id'}
```
If the `_id` is wrong by any chance, your would get an error response telling you `Invalid BlogCat`. If everything is good you would get `Created 1 docs.` response.

Now try to read the blog you created using endpoint `blog/read` with no `query` or `doc` args. What you would get is what you assume the blog doc, but have a deep look at `cat` attr. What do you get? Rather than the `_id` of the blog_cat, LIMP dynamically extended this attr and set it to the blog_cat doc value so you can easily get the blog_cat name and desc to present in your app. Thanks to our [extns](/docs/api-call.md#extns) workflow, you can easily extend any attr in your module using any other module doc, simply by having its `_id` set in its value.

This wraps up the quick start guide. You can explore the `limp-sample-app` source code and fiddle with it to get some interesting new creations of yours. Or, continue to our full and extended [tutorial](/docs/tutorial.md).