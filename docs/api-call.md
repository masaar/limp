[Back to Index](/README.md)

# LIMP Call
Everything you send your LIMP-powered app is a call. In most of the cases the call would return a response bound to it. The use of request-response `HTTP/1`-like model of messages transmission over `HTTP/2 Websocket` was a design decision--When we needed to work on the very first version of LIMP with websocket, we realised building a universal API has to come with basic concepts and not case-specific handlers.

Since our front-end framework of choice is Angular, you would notice that all the examples in these docs of LIMP are written in (typescript)[https://www.typescriptlang.org] and our (LIMP SDK for Angular)[https://github.com/masaar/ng-limp].

## Call Object
Regardless of the SDK you are using, any LIMP SDK is supposed to make your life easier by letting you send data in specific uniform and get the data you are always expecting to get. Technically, you send to LIMP app the following attrs with every call:
1. `call_id`: An attr representing unique identifier of your call. This is required in order to pipe the response to the request. You can read more about [websockets multiplexing on this article](https://www.rabbitmq.com/blog/2012/02/23/how-to-compose-apps-using-websockets).
2. `endpoint`: A string representing the `module/method` path.
3. `sid`: The current session `_id`. This is required to verify the request.
4. `token`: The current session `token`. This is required to tokenise the request.
5. `query`: The [Query object](#query-object) of the call.
6. `doc`: The [Doc object](#doc-object) of the call.

However, in the SDK world, you simply call the `call()` method on your SDK object and you usually send simple only the `endpoint` and when you are having more advanced use-cases you specify `query` and `doc` objects. Other attrs of the call should be set and managed by the SDK. One good start to get good glimpse of the call object and the SDK usage is to make the calls in [LIMP Sandbox on Github](https://masaar.github.io/limp-sandbox/dist/limp-sandbox/) and monitor the console for the calls that you can reuse as-is in your app in most cases, regardless of the framework, programming language and SDK.

Next is we explore the `query` object which is deemed the most essential object in a LIMP call.


## Query Object
The call `query` object is the most essential object. Although, you need to specify an `endpoint` to make any call, `query` is the object that allows you to get access to any specific data you need. The `query` object is a complex form of nested lists and objects with the following signature:
```typescript
interface {
	[attr: number]: queryStep | {
		$search?: string;
		$sort?: { [attr: string]: 1 | -1 };
		$skip?: number;
		$limit?: number;
		$extn?: false | Array<string>;
		$attrs?: Array<string>;
		$group: Array<{ by: string; count: number; }>;
		[attr: string]: { $not: any } | { $eq: any } | { $gt: number } | { $gte: number } | { $lt: number } | { $lte: number } | { $bet: [number, number] } | { $all: Array<any> } | { $in: Array<any> } | { $attrs: Array<string>; } | { $skip: false | Array<string>; } | queryStep | any;
	}
}
```
`query` object uses lists to reflect logical `or` condition, and objects to reflect `and` condition. Following are samples of different queries:

### Simple `and` condition
```typescript
[
	{
		attr1: 'conditionVal',
		attr2: 'conditionVal'
	}
]
```
If this gets translated into Python condition it would be:
```python
attr1 == 'conditionVal' and attr2 == 'conditionVal'
```

### Simple `or` condition
```typescript
[
	[
		{attr1: 'conditionVal'},
		{attr2: 'conditionVal'}
	]
]
```
If this gets translated into Python condition it would be:
```python
attr1 == 'conditionVal' or attr2 == 'conditionVal'
```

### Complex `and` & `or` condition
```typescript
[
	{
		attr1: 'conditionVal',
		__or: [
			{attr2: 'conditionVal'},
			{attr3: 'conditionVal'}
		]
	}
]
```
If this gets translated into Python condition it would be:
```python
attr1 == 'conditionVal' and (attr2 == 'conditionVal' or attr3 == 'conditionVal')
```
As you see in this example specifically, we used `__or` as key. This is a simple workaround for the status (where a nested `or` query as list (or array) in a `and` query as object) requiring it to have a key. LIMP does check such cases with any key that is a list and starts with `__or`. This means you can have multiple `or` condition nested in a `and` query simply by adding any additional identifier to `__or` key. For instance you can do this:
```typescript
[
	{
		attr1: 'conditionVal',
		__or1: [
			{attr2: 'conditionVal'},
			{attr3: 'conditionVal'}
		],
		__or2: [
			{attr4: 'conditionVal'},
			{attr5: 'conditionVal'}
		]
	}
]
```
If this gets translated into Python condition it would be:
```python
attr1 == 'conditionVal' and (attr2 == 'conditionVal' or attr3 == 'conditionVal') and (attr4 == 'conditionVal' or attr5 == 'conditionVal')
```

### Query Opers
By passing an attr in `query` object, you are telling LIMP to match docs that are having the attrs set to the value passed in the `query`. However, additional opers are available for wider accessibility and control:

#### `$gt`
Matches docs with attr values greater than set value. Value is `int` type.

#### `$lt`
Matches docs with attr values less than set value. Value is `int` type.

#### `$gte`
Matches docs with attr values greater than or equal set value. Value is `int` type.

#### `$lte`
Matches docs with attr values less than or equal set value. Value is `int` type.

#### `$bet`
Matches docs with attr values less than or equal set value. Value is array of `int` type. e.g. `[num1, num2]`.

#### `$not`
Matches docs with attr values not equal set value. Value is `any` type.

#### `$regex`
Matches docs with attr values matching set regular expression. Value is `str` type.

#### `$all`
Matches docs with list attr values matching all set list values. Value is list of `any` type.

#### `$all`
Matches docs with attr values matching at least one of the set list values. Value is `any` type.

As we explored in the [quick start](/docs/quick-start.md#read), we called the `staff/read` API endpoint with `_id` set to one of the two staff created which allowed us to get the needed doc only. Theoretically, any attr of the module attrs you are interacting with in your call can be sent in your `query` object and it should assess in matching the docs you are in need of. However, since the structure of [LIMP modules](/docs/api-module.py) allow the developers to manipulate or force specific attrs on `object` and `doc` attrs, you as backend developer can make use of such features for any advantage of the app overall design, and you as front-end developer should be aware of such use-cases.

However, beside sending the module attrs in `query` object, you can also send query special attrs, which are:

### Query Special Attrs
Additional available query attributes are the magic methods which have common form and unique use cases. Which are:

#### `$search`
```typescript
interface { $search: string; }
```
You can use this attr to pass on any string value to search for matching results in the data collection. `$search` assumes there are already the necessary requirements for it to perform in the database being used, such as text indexes.

#### `$sort`
```typescript
interface { $sort: { [attr: string]: 1 | -1  }; }
```
This self-descriptive magic attr allows you to pass any number of attributes names with their value being `1` or `-1` to determine the requested order of matched data.

#### `$skip`
```typescript
interface { $skip: number; }
```
This self-descriptive magic attr allows you to pass a number to determine the number of docs to skip of matched data.

#### `$limit`
```typescript
interface { $limit: number; }
```
This self-descriptive magic attr allows you to pass a number to determine the number of docs to limit the number of matched data to.

#### `$extn`
```typescript
interface { $extn: false | Array<string>; }
```
Setting this magic attr to false, would result in the data documents being matched to not get [extended](#extns). This can be used in scenarios to limit the data transferred if the piece of info you are looking for is essentially not in the extended data, but rather in the original data.

You can also pass an array of strings representing names of attrs you want only to be extended. For instance, if you are dealing with a module that has 4 attrs getting extended while you only require one of them to be extended you can set `$extn` to `['attr-to-be-extended']` and the other attrs would return only the `_id` of the extn docs, while `attr-to-be-extended` would be extended.

#### `$attrs`
Another data control magic attr is `$attrs` which allows you to send array of strings of the names of the attrs you only want LIMP to send as part of the matching response.

## Doc Object
The call `doc` object is straightforward representation of the data you are sending to LIMP app. As we explored in the [quick start](/docs/quick-start.md#create), we created a `Staff` doc by sending the attrs required by the module. Notice the `doc` object deals only with non-binary data types. This means the `doc` object can have nested objects (which are converted to Python dict at LIMP side), lists and arrays, booleans, numbers, and of course strings. This was decided in order to facilitate uniformity in handling the data in calls `doc` object. However, we were able to successfully send a photo (which is binary data) as part of the staff `create` call. What happened then? LIMP SDKs have special methods to handle binary data and send it in a special call to a non-existant `file/upload` endpoint in chunks. The chunk size can be set directly on the SDK object as explained in the [tutorial](/docs/tutorial.md#front-end-init). Technically, your SDK should handle this on your behalf, however for your SDK to be able to do so you should follow the instructions associated with sending files as part of `doc` object, which should be available in the docs of your SDK of choice.

### Doc Opers
Similar to [Query Opers](#query-opers), `doc` object has also useful set of opers that can be used for update calls:

#### `$add`
```typescript
interface { $add: number; }
```
This operator takes a `int` as value and adds it to the attr. You can use negative `int` value for subtraction.

#### `$push`
```typescript
interface { $push: any; }
```
This operator pushes a value into the list attr.

#### `$pushUnique`
```typescript
interface { $pushUnique: any; }
```
This operator pushes a value into the list attr of it doesn't exist.

#### `$pull`
```typescript
interface { $pull: any; }
```
This operator pulls all matching values from list attr.