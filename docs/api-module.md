[Back to Index](/README.md)

# LIMP Module
In LIMP ecosystem, modules are the brains of your app. It's where all your business logic goes. Unlike, MVC architecture, LIMP takes care of everything on your behalf and you only have to define modules that serve as:
1. Data Types (or Models): Every module is a standalone data type. It has its attrs and data extending config.
2. Controllers: Every module has its set of methods. In most cases, you just need to define the base methods and get to go. But, you also can define unlimited number of methods to serve your business logic.
3. Access Control Definitions: That's correct. Every module has its own set of permissions that you can define according to your needs. You can even extend this way beyond you can imagine.

For this, LIMP ideology is to compose modules that are totally standalone in logic, however they can be connected to other modules either by `extns` or by internal calls. These modules should share the same purpose in a single package.

To start building your first module you need to know the elements of the module. To make sure the elements are reflecting correctly on you, we are providing a boilerplate that you can compare to, and as well built upon it:
```python
from base_module import BaseModule

class BoilerplateModule(BaseModule):
	collection = 'boilerplates_modules'
	attrs = {
		'user':'id',
		'file_attr':'file',
		'locale_attr':'locale',
		'locales_attr':'locales',
		'str_attr':'str',
		'int_attr':'int',
		'datetime_attr':'datetime',
		'date_attr':'date',
		'time_attr':'time',
		'str_list_attr':['str'],
		'attrs':'attrs',
		'id_attr':'id',
		'create_time':'datetime'
	}
	diff = True
	extns = {
		'user':['user', ['*']]
	}
	methods = {
		'read':{
			'permissions':[['admin', {}, {}], ['*', {}, {}]]
		},
		'create':{
			'permissions':[['create', {}, {}]]
		},
		'update':{
			'permissions':[['admin', {}, {}], ['update', {'user':'$__user'}, {'user':None}]],
			'query_args':['_id']
		},
		'delete':{
			'permissions':[['delete', {}, {}]],
			'query_args':['_id']
		},
		'retrieve_file': {
			'permissions': [['*', {}, {}]],
			'query_args': ['_id', 'var'],
			'get_method': True
		}
	}
```
The previous boilerplate is a full-fledged module. It actually functions 100% without a single line change. However, to make this boilerplate yours you need to know the following:

## Module Name
Modules names in LIMP are essential. They are identifier that you would use to call and extend modules with each other. The naming scheme you have to follow is `CamelCase`. Make sure you capitalise the first letter as the usual Python standard is `camelCase`, which is not the case here. This has a legacy reason from previous versions of LIMP and it continues to live on it. The module name however, gets converted to `snake_case` as part of its initialisation. The `snake_case` is what you have to use when calling and extending to the module. As you noticed, the name of our boilerplate is `BoilerplateModules` which means when calling it or extending to it you need to use `boilerplate_module`. One last thing is the modules names are always singular, whether the name makes sense or not. The idea is a module is a representation of a data type, and data types are always singular.

## `collection`
The `collection` attr is the name of the collection you are saving the docs of this module in. This is an optional attr. Meaning, You can skip it. However, if you skip `collection` it defaults to `False` which results in the module be converted to `Service Module`. A service module is a module that has number of methods that are, either:
1. **Proxy to Another Module**: A very common use-case for service modules is creating a service module to provide proxy access to [`User` module](/docs/api-user-session.md).
2. **Shared Methods**: Another interesting use-case for service modules is creating a module that has set of methods that are common and shared for reuse by other modules.

Technically, nothing changes in the module itself between `Regular Module` and `Service Module`, thus if at any point you realised you need to swap between the both, you can simply do the necessary change to `collection` attr accordingly. The only difference is a `Service Module` has bo access to the base methods, which would be explained later in this doc.

The convention of the `collection` value is it should be the `snake_case` plural form of the module name. If the module name is two words or more, the `collection` name shall be the plural form of every word in the module name. For instance our `BoilerplateModule` has the `collection` set to (Do this:) `boilerplates_modules` rather than (Don't do this:) `boilerplate_modules` or `boilerplates_module`.

## `attrs`
The `attrs` attr is a dict representing the attrs every doc in your module collection should have, and the associated types. LIMP is type-driven. This means, you can simply defined every type you expect for your module `attrs` and LIMP would take the burden on checking the types, or convert them if required. The List of available types are:
1. **`any`**: This means your attr can have any type, ultimately skipping type-check on it altogether.
2. **`id`**: This means your attr is `BSON ObjectId` or any matching type. This is usually the type you set for your attr that has the `_id` value of another doc from the same module or another. Since this is a binary type that you can't send via LIMP SDKs. LIMP base methods convert your front-end app sent value as `str` to `ObejctId`.
3. **`str`**: Self-descriptive string type. Accepts anything that is a string.
4. **`int`**: Self-descriptive integer type. Accepts anything that is an integer.
5. **`bool`**: Self-descriptive boolean type. Accepts anything that is a boolean.
6. **`locale`**: As part of the built-in multi-language support. An attr in LIMP module can be set to `locale` to specify that it accepts multiple value, each repressing a supported language in your app.
7. **`locales`**: Another aspect of the built-in multi-language support is the `locales` type. This is a dynamic type that gets converted to a tuple with its values set to the locales your app supports. This is essentially a type that you can use to determine the language or locale of specific item or doc.
8. **`email`**: Self-descriptive email type. Accepts a string that matches the regexp `r'[^@]+@[^@]+\.[^@]+'` in Python.
9. **`phone`**: Self-descriptive phone type. Accepts a string that matches the regexp `r'\+[0-9]+'` in Python.
10. **`uri:web`**: Self-descriptive web URI type. Accepts a string that matches the regexp `r'https?:\/\/(?:[\w\-\_]+\.)(?:\.?[\w]{2,})+$'` in Python.
11. **`datetime`**: Self-descriptive datetime type. Accepts Python ISO format `datetime` value which matches the regexp `r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{6})?$'`.
12. **`date`**: Self-descriptive date type. Accepts Python ISO format `date` value `r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'`.
13. **`time`**: Self-descriptive time type. Accepts Python ISO format `time` value which matches the regexp `r'^[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]{6})?)?$'`.
14. **`file`**: Self-descriptive file type. Accepts a Python dict that has the file attrs as required by LIMP which are: `name`, `size`, `type`, `lastModified` and `content`. You can append to it a comma-separated list of MIME types allowed within square brackets for additional control on allowed files. You can use wild-card `*` as second part of the MIME type to allow all subtypes, for instance you can set the attr to `file[image/*,video/*]` to allow all files which are `image` and `video`, or to `file[image/jpeg]` to allow only JPEG images.
15. **`geo`**: A GeoJSON-compatible type. This is essentially for use with MongoDB `$geo` features.
16. **Tuple**: Tuple type is the native Python tuple type. This is used to define set of options for the attr. Any other value not from the tuple would be considered wrong value. For instance, a `shipment` module with attr `status` can have the type tuple as `('at-warehouse', 'shipped', 'received', 'cancelled')`.
17. **List**: A list of other type. For instance, your `blog` module, can have the `tag` attr set to `['str']` to flag that it accepts list of strings. You can pass more than one type in the list to allow multiple types.
18. **`attrs`**: A type representing either a Python list or Python dict. This is used when you need complex data types of your definition. You would have to type-check attrs set to `attrs` by yourself.
19. **Dict**: Dict type is the native Python dict type. You can use this as a value if you want more control over `attrs` type. With this you can pass child attrs and their respective types from native types as well as [app-specific attrs types](/docs/api-package.md#types).
20. **App-specific attrs types**: You can always extend the list 

### Special Attrs
Another aspect of `attrs` is that it has set of special attrs. These attrs value get dynamically set whether the user passed them or not; which are:
1. `user`: If attr `user` is defined in the `attrs` dict, it would be auto populated with the current session user `_id`. This basically sets a user as the owner of the doc.
2. `create_time`: If attr `create_time` is defined in the `attrs` dict, it would be auto populated with the time of passing the doc for insertion to the [Data Controller](/docs/data-drivers.md).

## `diff`
Just like the regular diff tool, LIMP has built-in diff workflow. If you set `diff` to `True`, any update on a doc in the module would be `diff`'ed and a `Diff` module doc would be created in reference to the original values before the change. Pay attention to this *`Diff` module doc is a representation of the original values before the `update` operation*. With this in mind, you can create a changes-tree of any doc in any module that has diff workflow enabled. 

`diff` attr also allows you to selectively *exclude* specific attrs from the diff workflow handling. For instance, your `Blog` module can have attr `views` that gets increased by one every time blog doc is read. You don't want to record a diff workflow on the `views` getting increased by `1`, as this would fill your database with huge nonsense docs in your `Diff` module collection. The attrs you want to exclude can be added to a list and set `diff` to that list, e.g. `['views']`.

## `optional_attrs`
Attrs that are defined in `attrs` are the attr that are going to be required to create a doc and they are the same attrs that are going to be matched for update. However, in the simplest cases you might want to problematically set a value of one of the attrs, rather than asking a use for it. 

## `extns`
The ability to extend data with data from other modules without the need to reinvent the wheel (aka create our own database system which we actually attempted to at some point) was always in our mind. one of the biggest wins of the fourth generation of LIMP was the ability to achieve a simple workflow for this. What we introduced was the extensions concept, which allows a developer to specify any of the module `attrs` as an attr that gets extended by another doc from the same module or another.

Since this is a crucial feature of LIMP we are going to shed more light on it. Let's assume we are having an [real] library app. This library would have a `Shelf` module with all the shelves in the library. Another module would be `Book`. The modules look like this (this is a snippet and not working modules):
```python
# Shelf attrs:
attrs = {
	'user':'id',
	'number':'str',
	'type':('fiction', 'non-fiction', 'mixed'),
	'create_time':'datetime'
}

# Book attrs:
attrs = {
	'user':'id',
	'title':'str',
	'author':'str',
	'type':('fiction', 'non-fiction'),
	'release_time':'datetime',
	'shelf':'id',
	'create_time':'datetime'
}
```
As you notice with the `Book` module, we are having attr `shelf`, which is self-descriptively the shelf `_id`. What extensions workflow and `extns` in module allow you to do is to specify an attr and LIMP would take care on your behalf the extending of the attr into the full doc it's pointing at. To get the results explained here set `extns` to:
```python
extns = {
	'shelf':['shelf', ['number']]
	# 'attr':['module', ['module_attr_1', 'module_attr_2', ..., 'module_attr_n']]
	# 'attr':['module', ['*']]
}
```
Adding attr `shelf` to `extns` dict would results in every `shelf` attr in any doc read by this module to be extended by the doc with the same `_id` from the module `shelf`. Remember, key is the local attr name, and first element of the value list is the module name. Another attr you have to set is a nested list as second element at index 1, which is the attrs you would like to be retrieved as part of the extension workflow. That's right, you can specify which `attrs` of module `Shelf` to be kept by specifying in the list, however if you are looking at the whole doc you can simply set the list to `['*']`.

Extensions workflow has also dynamic module detection--If your module is extending an attr based on another attr value, say you are having another module which is `Store`, for books not displayed on shelves, then you can add a `type` attr which is set to tuple type `('shelf', 'store')`. You then can change the `extns` module to `$__doc.type` which would result in the `shelf` attr be dynamically extended with doc from either `Shelf` or `Store` based on the value of the `type` attr in every doc.

## `privileges`
Every module gets by default 5 privileges which are `read`, `create`, `update`, `delete`, and `admin`. These are simply placeholders that you can decide what each means based on your requirement. However, if you need extra you need to define the `privileges` and add all the privileges you are looking at having in your module. For instance, if you are working on `Application` module in some gov entity. You can have a `sign` privilege given to some users and not the others. And to have that privilege added to the module you need to set `privileges` to:
```python
privileges = ['read', 'create', 'update', 'delete', 'admin', 'sign']
```

## `methods`
The actual home of the functionalities of your modules are the `methods`. In LIMP ecosystem, everything was built on the concept of DRY, this means even at the level of methods we attempted to make sure a developer doesn't have to repeat himself in writing any extra line of code repeating a similar behaviour. This is why you would mostly only define your methods as set of strings in nested lists in order to define them. Let's take a look at how to define a method for the module:
```python
methods = {
	'method_name':{
		'permissions':[['permission_name', {}, {}], ['another.permission_name', {'query':{'val':'args'}}, {'doc':'args'}]]
	}
}
```

So to define a method in your module you need to add it as a key to `methods`. With this you already have a defined method that can be accessed from any other module or via the API. However, to make correct use of `methods` your need to know the following attrs as well:

### `permissions`
Every method should define a set of `permissions` to access it. The idea behind the `permissions` current form was the necessity to find a built-it access control system without the need to write a lot of lines in every module.

To understand how the the permissions workflow goes, you need to know how does LIMP try and access a specific method, which goes:
1. LIMP gets either an internal or external method call to a `method` in a `module`.
2. LIMP attempts to find whether `method` exist on `module` or not.
3. If it exists, LIMP tries and match the `method` `permissions` to the current user privileges, like:
   1. LIMP takes every set of permissions.
   2. It checks on the privilege set as the first element of the permission set.
   3. If the user doesn't have the privilege the set would be ignored and LIMP would move to next set.
   4. If LIMP failed to match any of the `permissions` set with the user privileges, error `403 FORBIDDEN` would be returned.
   5. In the event of at least on of the user having one of the privileges set in the `permissions` sets, user would be granted access to the method.
   6. If user is granted access and second element which is the `query` args, having a value, LIMP would update the current request with the values from `query` dict.
   7. If user is granted access and third element which is the `doc` args, having a value, LIMP would update the current request with the values from `doc` dict.
   8. Call would be forwarded to the `method`.
4. Whatever is the returned value, whether it's from LIMP itself as `403 FORBIDDEN` or other results from the `method` itself it would be returned.

This structure allows developers to control what docs in the collection every user can access based on their privileges. For example, our `Blog` module in `limp-sample-app` does use the following to allow users to only update their own blog posts, however allow admin to update any:
```python
permissions= {
	'update':{
		'permissions':[['admin', {}, {}], ['update', {'user':'$__user'}, {'user':None}]],
		'query_args':['_id']
	}
}
```
The workflow here, does grant access to to users with either `admin` or `update` privileges of module `blog` to access the method `update`. What makes all the difference is users with `update` privilege but not `admin` would have their call `query.user` arg updated to only be able to update blog posts that they created, and it would set `doc.user` to `None` to ultimately deny them from changing the user as well. If you want to grant access to all, set privilege to `*`.

Basically, you can set `query` and `doc` parts of the permission set to any value of your need but you have also the ability to set either of them to `$__user` where LIMP would dynamically change it to the current session user `_id`.

### `query_args`
Another aspect of controlling the access to any method is `query_args`. Using `query_args` you can define which are the required attrs you want to get passed as part of the call. There are two ways to define a required attr:
1. Required Attr: You define a required attr by adding the attr name to `query_args` list.
2. Optional Attrs Set: If your method serves more than one purpose and require attrs based on different purposes, then this is your friend. Add all the attrs where you require at least one of as a `tuple` to `query_args`, like `('attr2', 'attr3', 'attr4')`. LIMP would check the set for at least one of the attrs being present in the call.

For instance, setting `query_args` to the following sample:
```python
query_args = ['req_attr', 'another_req_attr', ('optional_attr', 'another_optional_attr', 'last_optional_attr')]
```
The previous would result in the call only be accepted if its `query` args are:
1. Having `req_attr` present.
2. Having `another_req_attr` present.
3. Having either `optional_attr`, `another_optional_attr` or `last_optional_attr` present.

If any of the previous conditions are not failed on the call `query` args, error `400 MISSING ATTR` would be returned.

This method attr is optional and it's not required to having it present if you don't need it.

### `doc_args`
Similar to `query_args` but applies to call `doc`.

### `get_method`
A boolean attr to determine whether the method is available as the default `HTTP/2 Websocket` or the other `HTTP/1 GET` option. Methods with `get_method` set to true are expected to be:
1. Files Retrievers: If you have a file in your doc and you want to return it to the front-end or provide it as-is over the `HTTP/1 GET` interface for end-user download or view, then you have to use `get_method` mode. Binary content is not supported over `HTTP/2 Websocket` interface.
2. Quick User Actions: This is a good option for scenarios where you need to give users quick actions. For instance, verifying the email address is usually available via a link in the message sent to the email. This link can be the `HTTP/1 GET` method URI with the instructions to verify the email of the user. More on how to handle different scenarios in [Module Methods](#module-methods).

This method attr is optional and it's not required to having it present if you don't need it.

## Module Methods
Now that we defined all the required module attrs. We need to start making use of this module. To achieve that we need to write our own Python methods in the module class. The module method is a regular Python class method with the following signature:
```python
def method_name(self, skip_events=[], env={}, session=None, query=[], doc={}):
	pass
```
You should always use this signature and not any other, even with a slight change. The reason is LIMP doesn't call the methods directly, rather it calls the methods via an abstracted workflow within an object ([`BaseMethod`](https://github.com/masaar/limp/base_module.py#L370)) that handles required checks before making the actual call.

Your method should always return the following dict structure:
```python
results = {
	{
		'status':400, # HTTP status code. Always an int.
		'msg':'Invalid doc passed as ref.', # Human-readable text message.
		'args':{'code':'PACKAGE_MODULE_INVALID_REF'} # Other attrs.
	}
}
```
The `code` in `args` is a must in the event of non-successful `200` or `204` results `status`. It is a more formal way of delivering the error message to the front-end app that can then convert it to a proper message to show to the end-user. However, even in the event of a successful call, you still need to return `args` attr even if empty.

Let's take the following service module as an example:
```python
from base_module import BaseModule

class Math(BaseModule):
	methods = {
		'add':{
			'permissions':[['*', {}, {}]],
			'doc_args':['no1', 'no2']
		}
	}

	def add(self, skip_events=[], env={}, session=None, query=[], doc={}):
		results = {
			'status':200,
			'msg':'Successfully added two numbers.',
			'args':{'total':doc['no1'] + doc['no2']}
		}
		return results
```
The module is a service module because it doesn't have a `collection` attr, also `attrs` are missing completely meaning this is a service module of second condition *Shared Methods* and not *Proxy Module*. The rest is self-descriptive. The only thing you need to pay attention to is the form of `results` returned by the method `add`.

### Interaction with `query` and `doc`
In methods, you have access to both `query` and `doc` objects, to interact with them and manipulate the values per requirement. As we explored in the reference of [Query object](/docs/api-call.md#query-object), `query` object is a list-wrapper. This means you can access `query` attrs like a list, whether they were available in top-level or in deep-deep-level. For instance, the following query:
```python
[
	{
		'attr1':'conditionVal1',
		'__or1':[
			{'attr2':'conditionVal2'},
			{'attr3':'conditionVal3'}
		],
		'__or2':[
			{'attr2':'conditionVal4'},
			{'attr3':'conditionVal5'}
		]
	},
	{
		'$skip':5,
		'$limit':20
	}
]
```
When interacting with it, you can extract any of the attrs using Python list indices, like `query['attr2']`, which would result in:
```python
['conditionVal2', 'conditionVal4']
```
What you are getting here is not a regular Python list, it's `QueryAttrList` object which is another Python list wrapper. Every time you extract a `query` attr, you get an instance of this object as a list with all the possible values from the `query` object available as items in this object list. That's why you are getting two different values from different levels from the `query` object. This process allows developers to find any attr without having to loop over `query` object every time. Values of the `query` attrs can be updated or deleted when needed. You can update any condition value by passing it's index in `QueryAttrList` object. The same applies for deletion of any attr. If you need to update all the values of any `query` attr, or delete the attr altogether set index of the `QueryAttrList` to `*`, for example:
```python
# Single query attr delete, update:
del query['attr2'][1] # Delete only second value of attr 'attr2'
query['attr2'][0] = 'conditionVal6' # Update only first value of attr 'attr2'

# Multiple (all) query attr delete, update:
del query['attr2']['*'] # Delete all values of query attr 'attr2'
query['attr2']['*'] # Update all values of query attr 'attr2'
```

The previous applies only to regular attrs--[Special attrs](/docs/api-call.md#query-special-attrs) can only have one value at any given time in `query`, thus when you extract a special attr you get the actual value and not `QueryAttrList` object.

Unlike `query` object, `doc` object is a regular Python dict which can be interacted with accordingly.

## Base Methods
This is great so far. But, how can we handle more complicated methods? Essentially, how can we execute the `CRUD` operations for a module? Continuing on the DRY standard we adapted in many versions of LIMP in development, we were able to introduce what we call `Base Methods`. Base Methods are set of methods, 5 in count, that provide the essential `CRUD` functionalities to any module. They can be found in [`BaseModule` class](https://github.com/masaar/limp/base_module.py). The idea is to allow any developer to carry on the `CRUD` operations without the need to rewrite the same piece of instructions again again.

Let's take another look at our `Staff` module in `limp-sample-app`:
```python
from base_module import BaseModule

class Staff(BaseModule):
	collection = 'staff'
	attrs = {
		'user':'id',
		'photo':'file',
		'name':'locale',
		'jobtitle':'locale',
		'bio':'locale',
		'create_time':'create_time'
	}
	diff = True
	extns = {
		'user':['user', ['*']]
	}
	methods = {
		'read':{
			'permissions':[['admin', {}, {}], ['*', {}, {}]]
		},
		'create':{
			'permissions':[['create', {}, {}]]
		},
		'update':{
			'permissions':[['admin', {}, {}], ['update', {'user':'$__user'}, {'user':None}]],
			'query_args':['_id']
		},
		'delete':{
			'permissions':[['delete', {}, {}]],
			'query_args':['_id']
		},
		'retrieve_file': {
			'permissions': [['*', {}, {}]],
			'query_args': ['_id', 'var'],
			'get_method': True
		}
	}
```
If you finished the [quick start guide](/docs/quick-start.md) you would have been successfully able to create and read staff docs. But, where are the actual instructions to do so? This is the magic of Base Methods. The methods are defined in the `BaseModule` class itself, making them available to any module to use, however a call can only reach them if they are defined in the `methods` module attr, since only methods defined in there are available for calls. This allows us to provide open book `CRUD` methods, without forcing developers to break DRY standard. Additionally, we still give users all the power to decide who can access every method by setting custom `permissions`, `query_args`, and `doc_args` to every of the following Base Methods:
1. `read`.
2. `create`.
3. `update`.
4. `delete`.

So, once any of these methods are defined in `methods` it would be available for calls and all the Data Object calls would be taken care on behalf of you.

### 5. `retrieve_file`
Did we miss anything? No, we didn't but we intentionally left the last method. If you were counting with us, we mentioned that we are having 5 Base Methods. The fifth is `retrieve_file`. This method is also defined in `Staff` module. It's a `HTTP/1 GET` Base Method that allows front-end developers and end-users from getting binary data from any doc.

If you recall the [`Read` operation section in quick start](./quick-start.md#read) where we accessed the staff photo from the URI:
```
http://localhost:8081/{module}/retrieve_file/{_id}/{attr_name};{file_name}
```
This URI is the representation of our `retrieve_file` method. The method finds a doc with the `_id` in request, extracts attr `attr_name` and matches the file name from the doc with the request `file_name`. If things are positive the file would be returned as part of the response body, ultimately allowing users to view it if it's a photo, or download it if it's a non-stream type.

### CRUD Events
The Base Methods were designed in order to give us maximum reuse percentage without an extra line of code, or a single duplicated one. But, although we were as much careful in designing them, the chance is a developer still requires some custom handling of the `CRUD` operations. That's where the `pre_*` and `on_*` methods stand helpful.

Each one of `read`, `create`, `update`, `delete` has its own `pre` and `on` Python class method as event handler. Basically before calling any of the previous methods, LIMP would attempt to call `pre` event of the operation method, and once the operation method is also done, the `on` event of the operation method would be called.

Let's go back to our `Blog` module from `limp-sample-app`:
```python
class Blog(BaseModule):
	collection = 'blogs'
	attrs = {
		'user':'id',
		'status':('scheduled', 'draft', 'pending', 'rejected', 'published'),
		'title':'locale',
		'subtitle':'locale',
		'permalink':'str',
		'content':'locale',
		'tags':['str'],
		'cat':'id',
		'access':'access',
		'create_time':'datetime',
		'expiry_time':'datetime'
	}
	diff = True
	optional_attrs = ['subtitle', 'tags', 'permalink', 'access', 'expiry_time']
	extns = {
		'user':['user', ['*']],
		'cat':['blog_cat', ['*']]
	}
	methods = {
		'read':{
			'permissions':[['read', {}, {}], ['*', {'__OR:expiry_time':{'val':'$__time', 'oper':'$gt'}, '__OR:user':'$__user', 'access':'$__access'}, {}]]
		},
		'create':{
			'permissions':[['admin', {}, {}], ['create', {}, {}]]
		},
		'update':{
			'permissions':[['admin', {}, {}], ['update', {'user':'$__user'}, {'user':None}]],
			'query_args':['_id']
		},
		'delete':{
			'permissions':[['admin', {}, {}], ['delete', {'user':'$__user'}, {}]],
			'query_args':['_id']
		}
	}

	def pre_create(self, skip_events, env, session, query, doc):
		blog_cat_results = self.modules['blog_cat'].methods['read'](skip_events=[Event.__PERM__], env=env, session=session, query={'_id':{'val':doc['cat']}})
		if not blog_cat_results.args.count:
			return {
				'status':400,
				'msg':'Invalid BlogCat.',
				'args':{'code':'LIMP-SIMPLE-APP_INVALID_CAT'}
			}
		if 'subtitle' not in doc.keys(): doc['subtitle'] = {locale:'' for locale in Config.locales}
		if 'permalink' not in doc.keys(): doc['permalink'] = re.sub(r'\s+', '-', re.sub(r'[^\s\-\w]', '', doc['title'][Config.locale]))
		if 'tags' not in doc.keys(): doc['tags'] = []
		return (skip_events, env, session, query, doc)
```
If you notice we are have a `pre_create` method defined. This is `pre` event handler for operation `create` method. The `pre` event method here does few things:
1. It checks first if the provided `cat` attr is a valid `blog_cat` doc.
2. Add blank `locale` attr `subtitle` if it wasn't provided by the call `doc`.
3. Create `permalink` for the blog doc if none provided by the call `doc`.
4. Set `tags` attr to empty list if no tags were provided by the call `doc`.

As you can see, `pre` event handler was able to manipulate the actual call `doc`. This is correct. `pre_*` methods are having full access to the call args. This allows developers to cherrypick how they want to deal with their `CRUD` operations, before they get called. A `pre` event is having the following signature and it should return the same params passed:
```python
def pre_(self, skip_events, env, session, query, doc):
	return (skip_events, env, session, query, doc)
```
Any failure in defining or returning the correct params would cause a `500 SERVER ERROR`.

The other part of the story, `on` event. The `on` event, has exactly the same purpose and role. The only difference is it gets called after the `CRUD` operation, whether successful or not. A good example of `on` event is sending an email notification after blog doc was created by non-admin user.

Another difference of `on` event is that it has `results` of the `CRUD` operation passed as first param, ultimately to give developers access to the operation result and act on it. The signature and return structure are:
```python
def on_(self, results, skip_events, env, session, query, doc):
	return (results, skip_events, env, session, query, doc)
```

### Delete Strategy
By default, LIMP doesn't delete any doc from any collection of any module. The `delete` operation simply flags a doc as `__deleted`, which the default [`Data Controller and Drivers`](/docs/data-drivers.md) read query then ignores. This behaviour was introduced to allow developers to develop apps that can delete data on two levels:
1. Flagging docs as `__deleted` ultimately making it impossible for LIMP methods to access these docs, yet keep them present in their own collections.
2. Forcing the `delete` operation of specific docs completely from the database of the app.

This is helpful when you have an advanced app with possibility that users might request recovery of deleted docs. Although, this is not a backup system, nor should it ease your standards on having a separate backup system, but having the required doc in place and simple marked `__deleted` and being able to recover it by removing the `__deleted` attr from the doc in the database collection should be a huge convenience to the systems admins.

To force the `delete` of the docs, your should have `__SOFT__` present in `skip_events`.

## Interaction with Other Modules
Within LIMP ecosystem, reaching any other method, whether on the same module or another can be achieved using the following:
```python
self.{method_name}(skip_events=[], env=env, session=session, query=[], doc{}) # Same module method
self.modules['module_name'].{method_name}(skip_events=[], env=env, session=session, query=[], doc{}) # Another module method
```
Ultimately, this unified structure allows two modules to access each other without ending in a dead loop where each module is calling the other.

`env` and `session` should always be passed as is without changing. We shall have this area of LIMP documented separately but for now keep passing them in a chain.

`skip_events` is a simple list of events that you would like to skip on this call. Those events can be imported as:
```python
from event import Event
```
The events we have and we can use to skip are:
1. `__PERM__`: The most iconic event. It's the permission check event from the call. Basically, skipping this event allow users to reach methods they weren't allowed to before. A good example of this is having a proxy module that translates the call to a private module.
2. `__PRE__`: The event to skip `pre` event of a `CRUD` operation method. This is useful if you know the method you are calling has a `pre` event that might result in your call be manipulate in an unwanted way.
3. `__ON__`: Similar to `__PRE__` but for `on` event of a `CRUD` operation methods.
4. `__ARGS__`: Skip args check event. This is the event where LIMP would confirm your `query` and `doc` args passed are exactly as required by both the method definition in `methods` and as well as `attrs` and `optional_attrs`. This is helpful when you want to problematically skip `query_args` or `doc_args` check to achieve a sequence, usually not available to other public cases. Passing it would also result in [`user` Special Attrs](#special-attrs) not being auto populated by the current session user's `_id`, meaning not passing it manually would result in `400 Missing Attr` error. In [`realm` mode](/docs/api-realm.md)-enabled app, passing `__ARGS__` would also result in `query` and `doc` not being updated with `realm` attr. When creating a [user](/docs/api-user-session.md#user) doc, skipping `__ARGS__` event would also result in `groups` attr not being automatically set to `DEFAULT` group, but rather accept the `groups` value being passed by the call.
5. `__SOFT__`: Skip soft behaviour of the operation. This can be used with two operations. With `create` operation, skipping `__SOFT__` event would return the full created doc, rather than its `_id` only as part of the response. In `delete` operation this would apply [force delete strategy](/docs/api-module.md#delete-strategy). This event can also be used from the front-end calls as [`$soft` special query](/docs/api-call.md#soft).

Beside, `skip_events`, `env` and `session` there are the regular `query` and `doc` objects which were explored in [quick start guide](/docs/quick-start.md)