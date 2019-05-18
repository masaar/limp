# LIMP
LIMP is a backend framework that is designed for use by Masaar for rapid app development. It uses `HTTP/2 websocket` as primary protocol of communication with clients. However, it also provides an `HTTP/1 GET` interface for additional communication windows.

# Features
## Modern
LIMP is based on modern approaches of apps development. It enabled both backend developers and front-end developers with set of tools to acheive better and more from very simple and powerful set of tools.

## Multi-Environment Ready
LIMP gives the developers the ability to get started with single app that is having the ability to run the exact same app on different [environements](#package-configuration) without any custom configurations.

## Test-Driven Development Out-of-the-Box
That's correct! You can now develop your app and [test](#limp-tests-workflow) it with minimal set of instructions in [under 5 minutes](#5min-app).

## Easy to Install, Upgrade and deploy
LIMP has simple workflow to [set it up](#setting-up-limp). Upgrading it is also as simple as pulling latest version of LIMP from this repository, as well as the latest version of the packages your app uses for its functionalities. Deploying is as a simple as creating a [Docker](https://www.docker.com).

# Docs Index
[Dependencies](/docs/dependencies.md)
[Quick Start](/docs/quick-start.md)

## Query Object
The call `query` object is the most essential object. Although, you need to specify an `endpoint` to make any call, `query` is the object that allows you to get access to any specific data you need. The `query` object looks like this.:
```typescript
{
	[attr: String]?: {
		val: String | Array<String>;
		oper: '$gt' | '$lt' | '$bet' | '$not' | '$in' | '$all';
		val2: String;
	},
	$search?: String;
	$sort?: { [attr: String]: 1 | -1 };
	$skip?: Number;
	$limit?: Number;
	$extn?: Boolean;
}
```
Any value passed in the query obejct, that's not from the [magic attrs](#limp-magic-attrs), should be passed in the form of `ATTR: { val: VALUE }`. This allows for uniformity of any type of query attribute being passed. By default, passing an attribute means searching for matches to it. However, by passing `oper` you can choose from `$gt`, `$lt`, `$bet`, `$not`, `$in` and `$all`. Choosing `$bet` forces the use of `val2` which is the ceil of the search values between `val` and `val2`.

### LIMP Magic Attrs
Additional available query attributes are the magic methods which have common form and unique use cases. Which are:

#### $search
```typescript
{ $search: str; }
```
You can use this attr to pass on any string value to search for matching results in the data collection. `$search` assumes there are already the necessary requirements for it to perform in the database being used, such as text indexes.

#### $sort
```typescript
{ $sort: { [attr: string]: 1 | -1  }; }
```
This self-descriptive magic attr allows you to pass any number of attributes names with their value being `1` or `-1` to determine the requested order of matched data.

#### $skip
```typescript
{ $skip: int; }
```
This self-descriptive magic attr allows you to pass an `int` to determine the number of docs to skip of matched data.

#### $limit
```typescript
{ $limit: int; }
```
This self-descriptive magic attr allows you to pass an `int` to determine the number of docs to limit the number of matched data to.

#### $extn
```typescript
{ $extn: false | Array<str>; }
```
Setting this magic attr to false, would result in the data documents being matched to not get [extended](#extns). This can be used in scenarios to limit the data transferred if the piece of info you are looking for is essentially not in the extended data, but rather in the original data.

You can also pass an array of strings representing names of attrs you want only to be extended. For instance, if you are dealing with a module that has 4 attrs getting extended while you only require one of them to be extended you can set `$extn` to `['attr-to-be-extended']` and the other attrs would return only the `_id` of the extn docs, while `attr-to-be-extended` would be extended.

#### $attrs
Another data control magic attr is `$attrs` which allows you to send array of strings of the names of the attrs you only want LIMP to send as part of the matching response.

# Building an App with LIMP
Our `limp-sample-app` gives a good starting point. However, there's more than that.

The project consists of one package app. To understand the app structure you need to learn the following:

## Packages
A package is a folder with number of python files containing LIMP modules. The package has a distinguishing `__init__.py` file (which is also a requirement of Python packages) that sets the configurations of a package. An app in the LIMP eco-system could be the results of multiple packages. That's one reason to allow LIMP structure to have more than a single package with the ability to manage which to include in the launching sequence using LIMP CLI interface.

If your package uses any extra Python libs other than [dependecies](#Dependencies) of LIMP, then you can add your `requirements.txt` file with those libs and it would be installed with LIMP dependencies when running [Setting-up LIMP](#setting-up-limp).

## Modules
A LIMP module is a single class in a Python file inside a LIMP package inheriting from LIMP's built-in `BaseModule` class. The `BaseModule` singletons all LIMP modules and provides them with access to the unified internal API for exchanging data.

A module is essentially a definition of a data-type with number of typed-[attrs](#attrs) that can be set as `optional_attrs` and/or auto-extended by documents from the same and/or another module using the `extns` instructions. A module as well defines all its `methods` that any client could call. By default the `CRUD` methods, `read`, `create`, `update`, `delete` are available for all of the modules by simply defining them. Additional methods can be defined either for use by the `GET` interface or more often the `websocket` interface, using some additional instructions passed. A method can set the permissions checks required for an agent to pass before the agent being allowed to access the called method.

## Package Configuration
Every LIMP package can be given various range of configurations to facilitate faster app setup in any given environment.

The available configuration options for every package are:
1. `envs`: An environment projection object. This can be used to create environmental configuration variables per need. For instance, `limp-sample-app` has the following `envs` value. This means, LIMP has two options at least that can be passed to the configuration mechanism, either `dev` or `prod` environment. The environment of choice can be set at the time lf launch using LIMP CLI interface. All configuration options can be passed as static values or as environments variables:
```
{
	'dev':{
		'data_server':'mongodb://localhost'
	},
	'prod':{
		'data_server':'mongodb://remotehost'
	}
}
```
1. `debug`: The flag of whether debug options are active or not. It's not supposed to be set by a package, rather by the CLI. Default `False`.
2. `test`: The flag whether `test` mode is active 
3. `test_flush`
4. `test_force`
5. `tests`
6. `data_driver`: Data driver of choice. It is always set to 'mongodb' by omitting a value due to the fact LIMP currently does not support any other drivers.
7. `data_server`: Data server to connect to. Default `'mongodb://localhost'`
8. `data_name`: Database name to connect to. Default `'limp_data'`.
9. `data_ssl`
10. `data_ca_name`
11. `data_ca`
12. `data_azure_mongo`
13. `sms_auth`: Twilio `sid`, `token`, and `number` values to access their API.
14. `email_auth`: `server`, `username` and `password` of the default email account to send notifications from.
15. `locales`: Python list of locales used by the package. The form of the locale used in LIMP is `lang_COUNTRY`. Default `['ar_AE', 'en_AE']`.
16. `locale`: Default locale of the app. It should be one of the values passed in `locales`. Default `ar_AE`.
17. `events`: ...
18. `templates`: ...
19. `l10n`: App-specific locale dictionary.
20. `admin_username`: Superadmin username. Default `__ADMIN`.
21. `admin_email`: Superadmin email. Default `ADMIN@LIMP.MASAAR.COM`
22. `admin_phone`: Superadmin phone. Default `'+971500000000'`
23. `admin_password`: Superadmin password. Default `'__ADMIN'`
24. `anon_token`: Anon Token. Default `'__ANON'`
25. `anon_privileges`
26. `groups`: App-specific users groups to create.
27. `default_privileges`
28. `data_indexes`: App-specific data indexes to create for data collections.
29. `docs`
30. `realm`

## Module Elements
...

### collection
...

### attrs
...

### optional_attrs
...

### extns
...

### methods
...

# LIMP Tests Workflow

# Building an SDK for LIMP
LIMP currently only has an Angular SDK. We are working with other developers to provide React, React Native, Java and Swift SDKs. However, if you are in need of creating your SDK for any reason, here are the things you need to know:
1. You need to start with a websocket client, connecting to `ws[s]://IP_OR_HOST[:PORT]/ws`.
2. LIMPd would respond with the following:
```
{ "status": 200, "msg": "Connection established." }
```
3. Your calls to LIMP should have the following structure (Typescript-annotated interface):
```typescript
{
	call_id?: String; // [DOC] A unique token to distinguish which responses from LIMPd belong to which calls.
	endpoint?: String; // [DOC] The endpoint you are calling, it's in the form of 'MODULE/METHOD'.
	sid?: String; // [DOC] The session ID you are currently on.
	query?: any; /*
	[DOC] The query object which is in the form of
	{ [attr: String]?: {
		val: String | Array<String>;
		oper: '$gt' | '$lt' | '$bet' | '$not';
		val2: String; },
	  $search?: String; $sort?: { [attr: String]: 1 | -1 }; $skip?: Number; $limit?: Number; $extn?: Boolean; }
	*/
	doc?: any; // [DOC] The doc object is the raw values you are passing to LIMPd. It's should comply with the module `attrs` you are calling.
}
```
4. The call should be tokenised using `JWT` standard with the following header, using the session token, or '__ANON' if you have not yet been authenticated:
```
{ alg: 'HS256', typ: 'JWT' }
```
5. To authenticate the user for the current session you need to make the following call:
```typescript
{
	call_id: String;
	endpoint: 'session/auth';
	sid: 'f00000000000000000000012';
	doc: { [key: 'username' | 'email' | 'phone']: String, hash: String; }
}
/*
[DOC] You can get the hash of the auth method of choice from 'username', 'email', or 'phone' by generating the JWT of the following obejct:
{
	hash: [authVar: String; authVal: String; password: String;];
}
signed using 'password' value
*/
```
6. To re-authenticate the user from the cached credentials, in a new session, you can make the following call:
```typescript
{
	call_id: String;
	endpoint: 'session/reauth';
	sid: 'f00000000000000000000012';
	query: { _id: { val: String; }; hash: { val: String; } }
}
/*
[DOC] You can get the hash to reauth method by generating the JWT of the following obejct:
{
	token: String;
}
signed using cached token value
*/
```
7. Files can be pushed as part of the `doc` object in the call. The files or file should be pushed into the specific `attr` with a list or array of objects representing a file per LIMP specs, which is given below. It should have the following self-descriptive keys `name`, `type`, `size`, `lastModified` and `content`. Since sending binary to websocket is not a good idea in mixed encoded content, the decided convention was to send the `ByteArray` of the binary data in the `content` attribute. LIMP Angular SDK has perfect async implementation for this using native HTML5 APIs:
```typescript
Array<{
	name: String;
	type: String;
	size: Number;
	lastModified: Number;
	content: Int8Array;
}>
```

# Technical Sepcs
LIMP is using `aiohttp` Python framework. It handles both `websocket` and `GET` connectinos using two different separate functions both located in `limpd.py`. LIMP uses a group of techniques to:
* Instead of using nested git structure, LIMP repo ignores all folders in `modules` folder except `core` folder, making it possible to include unlimited number of LIMP packages and keep LIMP local repo up-to-date without touching your files.
* Auto load all LIMP packages and modules located in `modules` folder.
* Scaffold all modules attributes and methods and abstract them unto class methods and attributes.
* Set required attributes for cross-module communication.
* LIMP implements methods that require the client to generate authentication hashes to make sure no passwords are being transmitted in an insecure way. This results in the users password being unrecoverable if lost.
* LIMP implements JWT for data transfer between both sides in order to add a layer of security.
By default, all calls to and from LIMP are tokenised using `JWT` or `JSON Web Token` standard. Once a connection is established with LIMPd, a connection-specific session attribute is set in the loop handling the connection. By default, it uses the anonymous session to handle all the calls, thus requiring all the calls to be signed using '__ANON' session token. However, any call related to authenticating the user and/or session are not tokenised in order not to result in a cyclic effect by signing a session request with a token that is not the same used by the connection on LIMPd-side.

# CLI Interface
```
usage: limpd.py [-h] [--version] [--install-deps] [--env ENV] [--debug]
                [--packages PACKAGES] [-p PORT] [--test TEST] [--test-flush]
                [--test-force]

optional arguments:
  -h, --help            show this help message and exit
  --version             Show LIMP version and exit
  --install-deps        Install dependencies for LIMP and packages.
  --env ENV             Choose specific env
  --debug               Enable debug mode
  --packages PACKAGES   List of packages separated by commas to be loaded
  -p PORT, --port PORT  Set custom port [default 8081]
  --test TEST           Run specified test.
  --test-flush          Flush previous test data collections
  --test-force          Force running all test steps even if one is failed
  ```