# LIMP
LIMP is a backend framework that is designed for use by Masaar for rapid app development. It uses `HTTP/2 websocket` as primary protocol of communication with clients. However, it also provides an `HTTP/1 GET` interface for additional communication windows.

# Features
## Modern
LIMP is based on modern approaches of apps development. It enabled both backend developers and front-end developers with set of tools to achieve better and more from very simple and powerful set of tools.

## Multi-Environment Ready
LIMP gives the developers the ability to get started with single app that is having the ability to run the exact same app on different [environments](#package-configuration) without any custom configurations.

## Test-Driven Development Out-of-the-Box
That's correct! You can now develop your app and [test](#limp-tests-workflow) it with minimal set of instructions in [under 5 minutes](#5min-app).

## Easy to Install, Upgrade and deploy
LIMP has simple workflow to [set it up](#setting-up-limp). Upgrading it is also as simple as pulling latest version of LIMP from this repository, as well as the latest version of the packages your app uses for its functionalities. Deploying is as a simple as creating a [Docker](https://www.docker.com).

## Multi-language and Localisation-ready
Yes! No more dealing with custom handlers for multi-language apps. Your app is multi-language out-of-the-box. Not only this, but your app can keep adding locales and change them along the way. This is a paradise for developers working on global scale apps.

# Docs Index
* [Dependencies](/docs/dependencies.md)
* [Quick Start](/docs/quick-start.md)
* [Tutorial](/docs/tutorial.md)
* [Tests Workflow](/docs.tests.md)
* API References:
  * [Call](/docs/api-call.md)
  * [Package](/docs/api-package.md)
  * [Module](/docs/api-module.md)
  * [Realm Mode](/docs/api-realm.md)
* [Building SDK](/docs/build-sdk.md)
* [Technical Specs](/docs/technical.md)
* [CLI Interface](/docs/cli.md)


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
24. `anon_token`: Anon Token. Default `'__ANON_TOKEN_f00000000000000000000012'`
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