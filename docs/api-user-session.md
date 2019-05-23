# Users and Session in LIMP

LIMP core modules are mainly about users and sessions. The three pillars of our user and sessions ecosystem in LIMP are:
1. `User`: The module representing a user in LIMP. It has huge number of attrs that in many cases might be extra, but still present for maximum scalability.
2. `Group`: The module representing a group in LIMP. A group in LIMP ecosystem is where all the user privileges are decided*.
3. `Session`: The module representing a user session in LIMP. Any call and any operation happening within LIMP ecosystem has to have a session in order to set the level of access to the user of the session**.

> \* Although some special privileges can be set to users since `User` module has the attr `privileges`, but it's highly discouraged behaviour. This attr was only implemented as a final resort for a complicated scenario.

> \** Although LIMP has the capability to skip session checks internally, but this is only present to handle config-level calls. Developers should always pass `session` and expect to receive `session` in their methods since `session` is one of the chained params in LIMP methods.

## `User`
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
14. `username_hash`: The authentication hash using the `username` attr. More on the authentication hashes later. Type `str`.
15. `email_hash`: The authentication hash using the `email` attr. Type `str`.
16. `phone_hash`: The authentication hash using the `phone` attr. Type `str`.
17. `status`: Self-descriptive status of the user. Type `('active', 'banned', 'deleted', 'disabled_password')`.
18. `attrs`: Additional user attrs. This can be extra information about the user, or some system values you want to have every user to have. Type `attrs`.

Among all the previous attrs you need to pay attention to:
### Authentications Attrs
These are the attrs `username`, `email` and `phone`. These attrs are unique. Meaning, no two users can have the either of the same values.

### Authentication Hashes
These are the attrs `username_hash`, `email_hash` and `phone_hash`. These attrs are the hashes that LIMP matches as part of the authentication process. These hashes get generated at the client-side and not the server side as security measurement. The hashes are *The second part of the JWT of a dict with attr `hash` as its only attr and its value set to a list with the following values in order: authentication attr, authentication value, and the password, all signed as the password*. Technically, if you are generating `username_hash`, your dict should be:
```python
{
	'hash':['username', 'the-username-here', 'the-password-here']
}
```
You then generate the JWT of the previous dict, using `the-password-here` and take only the second part of it. For instance, the `username_hash` for this example would be:
```
eyJoYXNoIjpbInVzZXJuYW1lIiwidGhlLXVzZXJuYW1lLWhlcmUiLCJ0aGUtcGFzc3dvcmQtaGVyZSJdfQ
```

### Permissions on `CRUD` Operations
For many reasons, we decided to make all the `CRUD` operations of `User` module only accessible via [proxy modules](/docs/api-module.md#collection). In order to give apps full control over access to users without the need to twist the privileges of the default `User` module, since it's a core module and part of the original distribution of LIMP, we decided to let developers create their own proxy modules for `User` module, with their own set of permissions.

> Note to Self/TODO: Add placeholder for proxy modules in the tutorial.

### Optional Attrs
All attrs are required when creating a user doc except: `website`, `locale`, `login_time`, `status`, and `attrs`.

