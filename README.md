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

## Setting Up LIMP
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
	call_id?: string; // [DOC] A unique token to distinguish which responses from LIMPd belong to which calls.
	endpoint?: string; // [DOC] The endpoint you are calling, it's in the form of 'MODULE/METHOD'.
	sid?: string; // [DOC] The session ID you are currently on.
	query?: any; /*
	[DOC] The query object which is in the form of
	{ [key: string]?: {
		val: string || Array<string>;
		$oper: '$gt' || '$lt' || '$bet' || '$not';
		val2: string; },
	  $search?: string; $sort?: { [key: string]: 1 || -1 }; $skip?: number; $limit?: number; $extn?: boolean; }
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
	call_id: string;
	endpoint: 'session/auth';
	sid: 'f00000000000000000000012';
	doc: { [key: 'username' || 'email' || 'phone']: string, hash: string; }
}
/*
[DOC] You can get the hash of the auth method of choice from 'username', 'email', or 'phone' by generating the JWT of the following obejct:
{
	hash: [authVar: string; authVal: string; password: string;];
}
signed using 'password' value
*/
```
6. To re-authenticate the user from the cached credentials, in a new session, you can make the following call:
```typescript
{
	call_id: string;
	endpoint: 'session/reauth';
	sid: 'f00000000000000000000012';
	query: { _id: { val: string; }; hash: { val: string; } }
}
/*
[DOC] You can get the hash to reauth method by generating the JWT of the following obejct:
{
	token: string;
}
signed using cached token value
*/
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
