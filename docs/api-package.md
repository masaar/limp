# LIMP Package
Technically, a LIMP package is a Python package. However, what is super to regular Python package, is LIMP package has the following elements:
1. Config: Every package in LIMP has to define a `config` method that returns LIMP `Config` matching dict. More on this in the section [Package Config](#package-config).
2. Dependencies: LIMP package can define extra `requirements.txt` file including all the package dependencies which then be installed using [install dependencies](/docs/quick-start#install-dependencies).
3. Modules: What is more essential to the package than the other two elements is the presence of modules. More on modules in the [full API reference of modules](/docs/api-module.md).

Since elements #2 and #3 are out of the scope of the doc, the following is only reference to element #1. Config.

## Package Config
Every LIMP package can be given various range of configurations to facilitate faster app setup in any given environment.

Some of the config attrs are available but not supposed to be set using a package config, which are:
### `debug`:
The flag of whether debug options are active or not. It's not supposed to be set by a package, rather by the CLI. Default `False`.

### `test`:
The flag whether `test` workflow is active or not. If it's active it should be string representing the test name. It's not supposed to be set by a package, rather by the CLI. Default `False`.

### `test_flush`
The flag whether `test` workflow should flush and drop the previous test collections or simply continue with them. It's not supposed to be set by a package, rather by the CLI. Default `False`.

### `test_force`
The flag whether `test` workflow should break or force testing all steps after first failure. It's not supposed to be set by a package, rather by the CLI. Default `False`.

These config attrs are still available at public level so that your app can access them for various reasons and scenarios. For instance, your app can check whether `debug` options are active and print additional verbose messages, or whether `test` workflow is active and skip sending emails or SMSs as part of the modules methods.

The available configuration options for every package are:
### `envs`
An environment projection object. This can be used to create environment config variables per need. For instance, all the package config attrs can be reused in every `env` defined in `envs`. The most essential use-case here is using two set of `data_*` config attrs set among two `envs`; `dev` and `prod`:
```python
{
	'dev':{
		'data_server':'mongodb://localhost'
	},
	'prod':{
		'data_server':'mongodb://remotehost'
	}
}
```
Such feature allow the developers of the app to develop in their development `env` and then deploy the app to their `prod` host, and it would still work without a single change to any of the package or app config. Default `{}`.

### `tests`
The `test` workflow tests. Learn more about the workflow and how to make use of the TDD-approach in LIMP in the reference of [tests in LIMP](/docs/tests.md). Default `{}`.

### `data_driver`
Data driver of choice. It is always set to `'mongodb'` by omitting a value due to the fact LIMP currently does not support any other drivers.

### `data_server`
Data server to connect to. Usually it's string, however, if you are connecting to MongoDB ReplicaSet with multiple servers you can specify this attr as a list of strings each representing a different server. LIMP would automatically detect this and attempt to connect to the servers one by one until one is connected successfully. Default `'mongodb://localhost'`.

### `data_name`
Database name to connect to. Default `'limp_data'`.

### `data_ssl`
Boolean flag on whether to use secure `SSL` connection or not. Default `False`,

### `data_ca_name`
Name of the CA certificate to use while connecting to `data_server`. The certificate would be dynamically created at runtime in `certs` folder in your app root. This folder is not tracked by LIMP Git repo, which is the reason you don't see it in your cloned repo. Default `False`.

### `data_ca`
CA certificate usage flag and body. If it's set, the `data` connection with `data_server` would be constructed with this CA file, as `data_ca_name`. For this, if `data_ca` is having any truth-matching value, `data_ca_name` should also be present and valid. In Python, you should paste your certificate as-is including the line breaks. For that you need to make sure you are using the multi-line string. Make sure you don't add any wrong indentations when pasting the certificate body. This config attr was added to support IBM Cloud Databases for MongoDB which requires a CA certificate for connection. Default `False`.

### `data_azure_mongo`
Microsoft's Azure-specific MongoDB-in-sharded mode (or, [database throughput](https://docs.microsoft.com/en-us/azure/cosmos-db/how-to-provision-database-throughput)). The problem with databases created under this mode in Azure is the developer need to execute MongoDB command `shardCollection` to create the collection with assignment of `hashed_key` at the time of creation. For that, we introduced this config attr that you can set to `True` to do this on your behalf for all the collections of all the modules of the current loaded app. Default `False`.

### `sms_auth`
Dict with the attrs of Twilio `sid`, `token`, and `number` values to access their API. Default `{}`.

### `email_auth`
Dict with `server`, `username` and `password` of the default email account to send notifications from. Default `{}`.

### `locales`
Python list of locales used by the package. The form of the locale used in LIMP is `lang_COUNTRY`. Default `['ar_AE', 'en_AE']`.

### `locale`
Default locale of the app. It should be one of the values passed in `locales`. Default `ar_AE`.

### `l10n`
App-specific locale dictionary. Default `{}`.

### `admin_username`
`ADMIN` username. Default `__ADMIN`.

### `admin_email`
`ADMIN` email. Default `ADMIN@LIMP.MASAAR.COM`

### `admin_phone`
`ADMIN` phone. Default `'+971500000000'`

### `admin_password`
`ADMIN` password. Default `'__ADMIN'`

### `anon_token`
`ANON_TOKEN`. Default `'__ANON_TOKEN_f00000000000000000000012'`

### `anon_privileges`
`ANON` user privileges. These are the privileges that any anonymous user of the app would have. Learn more about privileges from the reference of [LIMP privileges](/docs/api-privilege.md). Default `{}`.

### `groups`
App-specific users groups to create. This is a list of docs, each representing a group. Default `[]`.

### `default_privileges`
`DEFAULT` group privileges. These are the privileges that all your app users would have. Learn more about privileges from the reference of [privileges in LIMP](/docs/api-privilege.md). Default `{}`.

### `data_indexes`
List of app-specific data indexes to create for data collections. This is an array of all the indexes you want to create for your app to function. For instance, to create a MongoDB `$text` index on collection `staff` you can set `data_indexes` to:
```python
[
	{
		'collection': 'staff',
		'index': [( '$**', 'text' )]
	}
]
```
Notice that the name you are passing is the `collection` name and not the module name. Also, the `index` attr is the native `index` format you pass to your MongoDB driver. Default `[]`.

### `docs`
List of app-specific docs to create for the app functionalities. Every list item is a dict with two attrs; `module` and `doc`. The docs would be created using LIMP [base methods](/docs/api-module.md#base-methods). For instance, to create `setting` doc in your app you should set `docs` to:
```python
[
	{
		'module':'setting',
		'doc':{
			'_id':ObjectId('f00000000000000000000091'),
			'var':'company_name',
			'val':{
				'ar_AE':'أكمي',
				'en_AE':'ACME'
			},
			'type':'global'
		}
	}
]
```

### `realm`
Flag to set the app to run in Realm mode. This is an advanced use-case of LIMP that has very specific scenario. Learn more about this mode in the [full reference of Realm mode](/docs/api-realm.md)