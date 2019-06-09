[Back to Index](/README.md)

# Users and Session in LIMP

LIMP core modules are mainly about users and sessions. The three pillars of our user and sessions ecosystem in LIMP are:
1. `User`: The module representing a user in LIMP. It has huge number of attrs that in many cases might be extra, but still present for maximum scalability.
2. `Group`: The module representing a group in LIMP. A group in LIMP ecosystem is where all the user privileges are decided*.
3. `Session`: The module representing a user session in LIMP. Any call and any operation happening within LIMP ecosystem has to have a session in order to set the level of access to the user of the session**.

> \* Although some special privileges can be set to users since `User` module has the attr `privileges`, but it's highly discouraged behaviour. This attr was only implemented as a final resort for a complicated scenario.

> \** Although LIMP has the capability to skip session checks internally, but this is only present to handle config-level calls. Developers should always pass `session` and expect to receive `session` in their methods since `session` is one of the chained params in LIMP methods.

## `User`
`User` module is the representation of a user in LIMP ecosystem. Every call to your app modules should be carried out by users. Even your non-authenticated, anonymous users get represented in LIMP as `ANON` user which has set of privileges set on app-level.

The module has the attrs:
1. `username`: Self-descriptive username of the user. Type `str`.
2. `email`: Self-descriptive email of the user. Type `email`.
3. `phone`: Self-descriptive phone of the user. Type `phone`.
4. `name`: Self-descriptive name of the user. Type `locale`.
5. `bio`: Self-descriptive biography of the user. Type `locale`.
6. `address`: Self-descriptive biography of the user. Type `locale`.
7. `postal_code`: Self-descriptive postal code of the user. Type `str`.
8. `website`: Self-descriptive website of the user. Type `uri:web`.
9. `locale`: Self-descriptive default locale of the user. It should be one of the locales supported by the app. Type `locales`.
10. `create_time`: The time the user doc was created. This value is set by LIMP. Type `time`.
11. `login_time`: Last time the user logged-in. This value is updated by LIMP. Type `time`.
12. `groups`: List of groups the user belong to. If [extensions workflow](/docs/api-module.md#extns) is enabled in the call this would be extended to groups. Type `['id']`.
13. `privileges`: Custom privileges of the user. This attr should not be used unless your app logic is unable to make use of groups, which is very unlikely. Type `privileges`.
14. `username_hash`: The auth hash using the `username` attr. More on the auth hashes later. Type `str`.
15. `email_hash`: The auth hash using the `email` attr. Type `str`.
16. `phone_hash`: The auth hash using the `phone` attr. Type `str`.
17. `status`: Self-descriptive status of the user. Type `('active', 'banned', 'deleted', 'disabled_password')`.
18. `attrs`: Additional user attrs. This can be extra information about the user, or some system values you want to have every user to have. Type `attrs`.

Among all the previous attrs you need to pay attention to:
### Authentications Attrs
These are the attrs `username`, `email` and `phone`. These attrs are unique. Meaning, no two users can have the either of the same values.

### Auth Hashes
These are the attrs `username_hash`, `email_hash` and `phone_hash`. These attrs are the hashes that LIMP matches as part of the auth process. These hashes get generated at the client-side and not the server side as security measurement. The hashes are *The second part of the JWT of a dict with attr `hash` as its only attr and its value set to a list with the following values in order: auth attr, auth value, and the password, all signed as the password*. Technically, if you are generating `username_hash`, your dict should be:
```python
{
	'hash':['username', 'the-username-here', 'the-password-here']
}
```
You then generate the JWT of the previous dict, using `the-password-here` and take only the second part of it. For instance, the `username_hash` for this example would be:
```
eyJoYXNoIjpbInVzZXJuYW1lIiwidGhlLXVzZXJuYW1lLWhlcmUiLCJ0aGUtcGFzc3dvcmQtaGVyZSJdfQ
```

### Optional Attrs
All attrs are required when creating a user doc except: `website`, `locale`, `login_time`, `status`, and `attrs`.

### Permissions on `CRUD` Operations
For many reasons, we decided to make all the `CRUD` operations of `User` module only accessible via [proxy modules](/docs/api-module.md#collection). In order to give apps full control over access to users without the need to twist the privileges of the default `User` module, since it's a core module and part of the original distribution of LIMP, we decided to let developers create their own proxy modules for `User` module, with their own set of permissions.

That said, if you want to give your users more relaxed access you set the [`default_privileges`](/docs/api-package.md#default_privileges) on module `User` to `['read', 'update']`. This would allow users to `read` their own user docs and `update` their docs (which is also their profiles) values. If you give them also by default `['delete']` privilege they would be able to `delete` their user doc. This is highly not recommended as the `delete` operation method of `User` module doesn't deal with situations where references to the user doc might exist in other modules after deletion of the user doc. This is not a behaviour you would like to deal with in your app, rather deleting a user should always be carried on by a proxy module that run the `delete` operation on all of the docs that have reference to the being-deleted user.

Additionally, `User` module has an `on_read` event that removes the auth hashes from the docs results of `read` operation. This is a security measurement to make sure no developer would wrongly expose the auth hashes to the world.

One more note on `update` operation for module `User`; Since `update` operation scope is the doc, this means updates to `attrs` attr are supposed to be destructive, meaning calling `update` operation on doc with `attrs` set to one value changed is supposed to delete the other `attrs`. This is not the case with `User` module, as the module verbosely updates only the attrs passed as part of the call `doc` attr `attrs`.

`User` module has also the following methods:
1. `read_privileges`: A system-requirement method. This is the method that compiles user's privileges. Developers are not supposed to use this method.
2. `add_group`: To facilitate better interface to manage the the users groups we added this method to add a group to user in a single call. To make use of the method call it with endpoint `user/add_group`, with `query` having the user `_id` and `doc` has the group `_id`. If the group is already added, error `400 CORE_USER_GROUP_ADDED` would be returned.
3. `delete_group`: Similar to `add_group` but to delete a group from the user doc, with the same use instructions. If the group is not present in user doc `groups` list, error `400 CORE_USER_GROUP_NOT_ADDED` would be returned.

## `Group`
The users in LIMP ecosystem should always be part of at least the `DEFAULT` group, except for `ANON` and `ADMIN` users who are not part of any group. Groups are where you decide the level of access users in your app have. You set their privileges based on what access you want them to have, and LIMP would take care of the rest on your behalf to make sure they only gain access to endpoints they should be able to access. Refer to [`permissions` section of LIMP module](/docs/api-module.md#permissions) reference for verbose explanation on how privileges and permissions check happen.

The module has the following attrs:
1. `user`: The user as group owner `_id`. Type `id`.
2. `name`: Self-descriptive name of the group. Type `locale`.
3. `bio`: Self-descriptive biography of the group. Type `locale`.
4. `privileges`: The privileges of the group. This is the most important attr of the group. This sets all users belonging to this group privileges. Type `privileges`.
5. `attrs`: Similar to [`User` module `attrs`](#user), it allows you to add extra information or extra system values you require group docs to have. Type `attrs`.

### Permissions on `CRUD` Operations
In most cases, your app defines the groups required for its functionality as part of your app [packages config](/docs/api-package.md#groups). However, `ADMIN` user who can always create more groups. Users who have `group.admin` privilege can also access all the `CRUD` operations of `Group` module. Yet, unlike `User` module which is only managed by `ADMIN` by default, a group owner should be able to able to update the group `name`, `bio` and `attrs`, but not `privileges`. A group owner also can delete the group.

## `Session`
The calls made to different LIMP endpoints, are always carried out by users as we learnt in `User` module introduction, however the way LIMP identifies the user in reference is by checking the current session. `Session` module was introduced in order to manage the `auth`, `reauth`, and `signout` endpoints. `Session` module is also the home of a system-level method that checks the permissions of the users before granting them access to. The current session doc gets carried around with the users calls journey in LIMP ecosystem.

The module has the following attrs:
1. `user`: Reference to the user `_id`. Type `id`.
2. `host_add`: The IP of which the user is connecting from. Type `ip`.
3. `user_agent`: The User Agent value of the user. Type `str`.
4. `timestamp`: The session creation time. Type `time`.
5. `expiry`: The session expiration time. Type `time`.
6. `token`: The session token more on it next. Type `str`.

### Sessions Tokens
When a user calls `session/auth` to auth to LIMP, a session doc is created with an auto-generated `token` attr. The `token` attr of the user session is the token all the calls in the session are required to be signed with. This is a security measurement in LIMP where all calls to LIMPd should always be `JWT` tokenised. This is applied to `ANON` user session as well. That's why LIMP package has the ability to set a [`anon_token`](/docs/api-package.md#anon_token) that your front-end apps pass to SDKs in order to sign even the anonymous users' calls as.

### Permissions on `CRUD` Operations
Among the all the modules in this reference, `Session` is having the most strict permissions. Technically, no user can access the `CRUD` operations, including `ADMIN` user. This permissions structure was put in place to make sure no developer custom privileges structure would result in unauthorised access to other users' sessions. However, the session information are always available LIMP methods as part of the params. Also, front-end apps get the session details upon the successful `session/auth` or `session/reauth`.