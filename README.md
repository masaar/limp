# LIMP

LIMP is a backend framework that is designed for use by Masaar for rapid app development. It uses `HTTP/2 websocket` as primary protocol of communication with clients, however it also provides an `HTTP/1 GET` interface for additional communication windows.

# Dependencies
LIMP is Python based. It's tested in small number of environments running Python 3.5+.
Since LIMP is orignially built for Masaar use-cases, it's based on `MongoDB` the database engine of choice by Masaar, as well as it requires `Twilio` SDK to be installed even if you are not planning to use their platform.

The current list of requirements is: https://github.com/masaar/limp/blob/master/requirements.txt.

# Quick Start
```
Make sure you have MongoDB daemon working before proceeding.
```

## Setting-up LIMP
To start a new LIMP app, all you need is to clone this repository and then clone https://github.com/masaar/limp-sample-app inside `modules` folder. Then run the following command (make sure your default `python` command is set to version 3.5+ and not 2.x):
```
python limpd.py --env dev --debug
```
This command would then connect to the database named in https://github.com/masaar/limp-sample-app/blob/master/__init__.py#L15 on the server https://github.com/masaar/limp-sample-app/blob/master/__init__.py#L9. If you need to use different settings please change the previously referred values. After succeful connection, LIMPd would attempt to create the necessary collections and documents required for its basic functionalities.

## Interacting with LIMPd
To start interacting with the app you created, simply clone https://github.com/masaar/limp-sandbox and run it. You can then see the 'LIMP Sandbox' interface. If you see a succeful connection message in the output area then, congrats! your setup is working. Then you can start by `auth`entication call using the default credentials for the superadmin user using:
```
ADMIN@LIMP.MASAAR.COM
__ADMIN
```
You should see a new message in the output indicating that you were 'authed' as well as the session data. Following you can make some calls to your backend using the 'call()' button. For instance you can query all the users by passing the following values:
```
endpoint: user/read
query: {}
doc: {}
```
This should give you additional message in the output with two users' superadmin and anonymous user. To query specific user pass its '_id' value as a query param like:
```
query: {"_id":{"val":"ID_GOES_HERE"}}
```
If you are running `limp-sample-app` you can also use the sample tools available in the sandbox, for starter create a `blog_cat`, and then copy its '_id' and then create a `blog` bound to the same `blog_cat`. You can see all the queries you are making as well as the output you receive from LIMPd.

## Query Object
The call `query` object is the most essential object. Although, you need to specify an `endpoint` to make any call, `query` is the object that allows you to get access to any specific data you need. The `query` object looks like this.:
```typescript
{
	[key: String]?: {
		val: String || Array<String>;
		$oper: '$gt' || '$lt' || '$bet' || '$not';
		val2: String;
	},
	$search?: String;
	$sort?: { [key: String]: 1 || -1 };
	$skip?: Number;
	$limit?: Number;
	$extn?: Boolean;
}
```
Any value passed in the query obejct, that's not from the [magic attrs](#limp-magic-attrs), should be passed in the form of `ATTR: { val: VALUE }`. This allows for unirformity of any type of query attribute being passed. By default, passing an attribute means search for equals to it, however, by passing `$oper` you can choose from `$gt`, `$lt`, `$bet`, and `$not`. Choosing `$bet` forces the use of `val2` which is the ceil of the search values between `val` and `val2`.

### LIMP Magic Attrs
Additional available query attributes are the magic methods, which have common form and unique use cases. Which are:

#### #search
You can use this attr to pass on any string value to search for matching results in the data collection. `$search` assumes there are already the necessary requirements for it to perform in the database being used, such as text indexes.

#### $sort
This self-descriptive magic attr allows you to pass any number of attributes names with their value being `1` or `-1` to determine the requested order of matched data.

#### $skip
...

#### $limit
...

#### $extn
Setting this magic attr to false, would result in the data documents being matched to not get [extended](#extns). This can be used in scenarios to limit the data transferred if the piece of info you are looking for is essentially not in the extended data, but rather in the original data.

# Building an App with LIMP
Our `limp-sample-app` gives a good starting point. However, there's more than that.

The project consists of one package app. To understand the app structure you need to learn the following:

## Packages
A package is a folder with number of python files containing LIMP modules. The package is having a distinguishing `__init__.py` file (which is also a requirement of Python packages) that sets the configurations of a package. An app in the LIMP eco-system could be the results of multiple packages that's one reason to allow LIMP structure to have more than a single package with the ability to manage which to include in the launching sequence using LIMP CLI interface.

## Modules
A LIMP module is a single class in a Python file inside a LIMP package inheriting LIMP built-in `BaseModule` class. The `BaseModule` singletones all LIMP modules and provides them with access to the unified internal API for exchanging data.

A module is essentially a definition of a data-type with number of typed-`attrs` that can be set as `optional_attrs` and/or auto-extended by documents from the same and/or another module using the `extns` instructions. A module as well defines all its `methods` that any client could call. By default the `CRUD` methods, `read`, `create`, `update`, `delete` are available for all of the modules by simply defining them. Additional methods can be defined either for use by the `GET` interface, or more usual `websocket` interface using some additional instructions passed. A method can set the permissions checks required for an agent to pass before the agent being allowed to access the called method.

## Package Configuration
Every LIMP package can be given various range of configurations to facilitate faster app setup in any given environment.

The available configuration options for every package are:
1. `envs`: An environment projection object. This can be used to create environmental configuration variables per need. For instance, `limp-sample-app` has the following `envs` value. This means, LIMP has two options at least that can be passed to the configuration mechanism, either `dev` or `prod` environment. The environment of choice can be set at the time lf launch using LIMP CLI interface. All configuration options can be passed as static values or as environmental variables:
```
{
	'dev':{
		'data_server':'mongodb://localhost'
	},
	'prod':{
		'data_server':'mongodb://localhost'
	}
}
```


2. `debug`: The flag of whether debug options are active or not. It's not supposed to be set by a package, rather by the CLI. Default `False`.
3. `data_driver`: Data driver of choice. It has to be always set to 'mongodb' by not setting any value due to the fact LIMP currently does not support any other drivers.
4. `data_server`: Data server to connect to. Default `'mongodb://localhost'`
5. `data_port`: Data server port is listening on. Default `27017`.
6. `data_name`: Database name to connect to. Default `'limp_data'`.
7. `sms_auth`: Twilio `sid`, `token`, and `number` values to access their API.
8. `email_auth`: `server`, `username` and `password` of the default email account to send notifications from.
9. `locales`: Python list of locales used by the package. The form of the locale used in LIMP is `lang_COUNTRY`. Default `['ar_AE', 'en_AE']`.
10. `locale`: Default locale of the app. It should be one of the values passed in `locales`. Default `ar_AE`.
11. `events`: ...
12. `templates`: ...
13. `l10n`: App-specific locale dictionary.
14. `admin_username`: Superadmin username. Default `__ADMIN`.
15. `admin_email`: Superadmin email. Default `ADMIN@LIMP.MASAAR.COM`
16. `admin_phone`: Superadmin phone. Default `'+971500000000'`
17. `admin_password`: Superadmin password. Default `'__ADMIN'`
18. `anon_token`: Anon Token. Default `'__ANON'`
19. `groups`: App-specific users groups to create.
20. `data_indexes`: App-specific data indexes to create for data collections.

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


# Building an SDK for LIMP
LIMP is currently having only Angular SDK. We are working with other developers in providing `react`, `react-native`, `Java` and `Swift` SDKs. However, if you are in need of creating your SDK for any reason, here are the things you need to know:
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
	{ [key: String]?: {
		val: String || Array<String>;
		$oper: '$gt' || '$lt' || '$bet' || '$not';
		val2: String; },
	  $search?: String; $sort?: { [key: String]: 1 || -1 }; $skip?: Number; $limit?: Number; $extn?: Boolean; }
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
	doc: { [key: 'username' || 'email' || 'phone']: String, hash: String; }
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
7. Files can be pushed as part of the `doc` object in the call. The files or file should be pushed into the specific `attr` with a list or array of objects representing a file per LIMP specs, which is given below. It should have the following self-descreptive keys `name`, `type`, `size`, `lastModified` and `content`. Since sending binary to websocket is not a good idea in mixed encoded content, the decided conviction was to send the `ByteArray` of the binary data in the `content` attribute. LIMP Angular SDK has perfect async implementation for this using native HTML5 APIs:
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
* LIMP implements methods that require the client to generate authenitcation hashes to make sure no password are being transmistted in any unsecure method. This results in the users password being unrecoverable if lost.
* LIMP implements JWT for data transfer between both sides in order to add a layer of security.
By default, all calls to and from LIMP are tokenised using `JWT` or `JSON Web Token` standard. Once a connection is established with LIMPd, a connection-specific session attribute is set in the loop handling the connection. By default, it uses the anonymous session to handle all the calls, thus requiring all the calls to be signed using '__ANON' session token. However, any call related to authenticating the user and/or session are not tokenised in order not to result in a cyclic effect by signing a session request with a token that is not the same used by the connection on LIMPd-side.

# CLI Interface
```
usage: limpd.py [-h] [--version] [--env ENV] [--debug] [--packages PACKAGES]
                [-p PORT]

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --env ENV             Choose specific env
  --debug               Enable debug mode
  --packages PACKAGES   Specify list of packages separated by commas to be
                        loaded only.
  -p PORT, --port PORT  Set custom port [default 8081]
  ```
