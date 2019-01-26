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
To start interacting with the app you created, simply clone https://github.com/masaar/limp-sandbox and run it. You can then see the 'Dynamic API' interface. If you see a succeful connection message in the output area then, congrats! your setup is working. Then you can start by `auth`entication call using the default credentials for the superadmin user using:
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

# Technical Sepcs
LIMP is using `aiohttp` Python framework. It handles both `websocket` and `GET` connectinos using two different separate functions both located in `limpd.py`. LIMP uses a group of techniques to:
* Auto load all LIMP packages and modules located in `modules` folder.
* Scaffold all modules attributes and methods and abstract them unto class methods and attributes.
* Set required attributes for cross-module communication.
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
