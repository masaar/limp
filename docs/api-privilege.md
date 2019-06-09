[Back to Index](/README.md)

# Privileges in LIMP

Privileges in LIMP are the definitions of the users' access level.

Every LIMP module in your app has its defined privileges as we explored in [LIMP module reference](/docs/api-module.md#privileges). The default privileges are `read`, `create`, `update`, `delete`, and `admin`. However, you can define more and make use of these privileges per your needs.

To give privileges to users, you either give them these privileges as part of their [`default_privileges` config of your LIMP app](/docs/api-package.md#default_privileges), or alternatively create a new group with the privileges being provisioned to the users who would be part of the new group later.

A `privileges` value looks like this:
```python
{
	'module_name':['privilege_1', 'privilege_2', ..., 'privilege_n']
}
```
There's also a wild card privilege definition. This is helpful when you want to give the users all the privileges available for a module:
```python
{
	'module_name':'*'
}
```
This wild card definition gets dynamically expanded to all the [`privileges` of the module](/docs/api-module.md#privileges).

And, by mixing these two formats you get easy to read and analyse set of privileges as lists or wild card definitions to every module in a unified `privileges` dict.