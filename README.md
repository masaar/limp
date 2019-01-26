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
To start a new LIMP app, all you need is to clone this repository and then clone https://github.com/masaar/limp-sample-app inside `modules` folder. Then run the following command (make sure your default `python` command is set to version 3.5+ and not 2.x):
```
python limpd.py --env dev --debug
```
This command would then connect to the database named in https://github.com/masaar/limp-sample-app/blob/master/__init__.py#L15 on the server https://github.com/masaar/limp-sample-app/blob/master/__init__.py#L9. If you need to use different settings please change the previously referred values. After succeful connection, LIMPd would attempt to create the necessary collections and documents required for its basic functionalities.

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
