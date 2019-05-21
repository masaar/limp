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
4. The call should be tokenised using `JWT` standard with the following header, using the session token, or `ANON_TOKEN` if you have not yet been authenticated:
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
7. Files can only be pushed as part of the `doc` object in the call if you are using the special call to `file/upload`. Right before sending the call, attempt to detect any `FileList` or matching types in the call `doc` object. If any are found, iterate over all the files in the `FileList`, read each as `ByteArray` object and slice it into slices matching the default or user-set SDK `fileChunkSize` attr. Each slice should be sent to LIMPd in the form of:
```typescript
{
	attr: String;
	index: Number; // Index of the file in the FileList.
	chunk: Number; // Index of the chunk of the current file.
	total: Number; // Total number of chunks to be sent.
	file: { // Attr file is not user-defined. This should always be the name of the attr.
		name: String; // File name.
		size: Number; // File size.
		type: String; // File mime-type.
		lastModified: Number; // File disk lastModified value.
		content: String; // The byteArray slice joined with ',' commas e.g. byteArraySlice.join(',')
	}
}
```
The previous `doc` object should be then sent to special endpoint `file/upload` which would parse the file, confirm it's part of an ongoing file upload process and respond with `Chunk accepted` message for all the chunks except the last which would be `Last Chunk accepted`. Once you receive confirmation from LIMP app that all files in all `FileList` objects you detected earlier are uploaded, you then can send the original call. [LIMP SDK for Angular](https://github.com/masaar/ng-limp) has very clear workflow on handling `FileList`s and parse them with the explained method.