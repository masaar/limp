# LIMP Tests Workflow

One of the aspects for better product of development is adaptation of Test-Driven Development process. However, as it's well known to all developers, writing sophisticated tests can be a huge time and efforts waste factor, although when the final structure is still not realised. And, what makes adapting TDD even harder is applying it on a full fledged framework. That's why we are having tests built-in with LIMP.

LIMP provides simple workflow to write tests. Unlike regular TDD approach where you have unit and integration tests, LIMP swapped that with single multi-step test workflow. The idea is, LIMP apps are mature enough to have most of its basic functionalities being taken care of by LIMP ecosystem, where the user is only writing advanced and high-level modules and methods. This makes testing on unit level almost impossible. However, the workflow we introduced in LIMP originally for our use allowed us to attempt both, unit and integration test altogether.

LIMP tests workflow runs the test in parallel collections on the same database, ultimately allowing developers to test all the aspect of the app without touching the actual data. The way LIMP does this is by prefixing all collections names in all the loaded modules with `test_`. LIMP leaves the test collections present after the tests run for further inspection by developers, if needed.

The tests workflow produces at the end of every run a separate detailed JSON-formatted report that includes all the details of the test including passed, failed and skipped tests. This tests reports are available in Git-non-tracked `tests` folder LIMP root. The tests reports are having the test name with the date of the run for easier access and archiving of tests reports when needed.

## Sample Test
Let's try and write a test for our `limp-sample-app` from [quick start](/docs/quick-start.md). To do so, go to package config on `__init__.py` of the package. Add attr `tests` to config dict. The attr should be a dict. Every item in this dict present a test, one or multi step test. Let's write a test for `Staff` module `create` method. Set, `tests` to:
```python
'tests':{
	'staff-create':[
		{
			'step':'call',
			'module':'staff',
			'method':'create',
			'query':{},
			'doc':{
				'photo':{'__attr':'file'},
				'name':{
					'ar_AE':'جون دو',
					'en_AE':'John Doe'
				},
				'jobtitle':{
					'ar_AE':'مجهول',
					'en_AE':'Anonymous'
				},
				'bio':{
					'ar_AE':'مجهول',
					'en_AE':'Anonymous'
				}
			},
			'acceptance':{
				'status':200,
				'args.count':1
			}
		}
	]
}
```
Let's go through this one by one:

## Test Step `call`
First thing to notice is the form of of the test. It's a list. The list allows us to add more than one step to the test if required. Basically, you can write a unit-test in LIMP by creating a one-step test, or else an integration test using a multi-step test. In our case here we are testing the `create` method using one-step which relatively makes it a unit-test. Let's go though the attrs of the `call` test step:
1. **`step`**: This is the step type. Here we have a `call` step, which means we are testing a call. Other types are: `test`, `auth` and `signout`, which we would come to mention in a bit.
2. **`module`**: For the `call` step you need to define the `module` your method of test choice is on.
3. **`method`**: Self-descriptive the method of test choice.
4. **`query`**: Self-descriptive call `query`, since we are testing a `create` operation here, we aren't having any `query` to pass.
5. **`doc`**: Self-descriptive call `doc`, since we are testing a `create` operation here, we have all the fun go on this attr. We would talk more about it.
6. **`acceptance`**: The mother of all tests attrs. Universally. This is the measurements LIMP Test object matches with the results from the call in order to know whether the test had failed or passed. You can set unlimited number of acceptance measurements here, and the test would only be considered passed if all of the acceptance measurements are matching the results.

The attrs `step`, `module`, and `method` are simple and don't require verbose explanation. Attr `query` is a regular call `query` that you can append here as-is and expect it to work without any issues, but we are keeping it empty since our `create` operation doesn't need any. Attr `doc` is having similar structure to what we have experienced in [quick start guide](/docs/quick-start.md) when creating a staff. We even have all of the locale attrs having both the Arabic and English values. But, one attr is having something exceptional--The `doc` attr `photo` is having the value set to `{'__attr':'file'}`. This is one of the tests workflow amazing features. It allows you to generate values for the call `doc` without the need to statically define them, this is helpful when you want to repeat some test few times but every time with different value. Another good use case is files definition. It could be a little hectic to define a file as part of the call because of the number of attrs a LIMP file type requires, which an easy to remember generator makes it easier to write tests and update them.

The test `acceptance` is a dict with the key being translated to the test results object. you can match anything from the results object simply by writing the attr name in the `acceptance` as a key, setting the value to the accepted value. If you need to go further in levels use the dot `.` notation. For instance we are having two measurements for our test. First, the `status` should be `200` and, second `args.count` should be `1`.

Now let's run the test to see whether our module method is valid or not. To run a test, use LIMPd with the following command:
```bash
python limpd.py --env dev --test staff-create --test-flush
```
Let's explore every arg from the command. Up until `env` arg things are fine, but following are the tests workflow args, which are:
1. `test`: A flag to determine LIMPd is starting in test mode. It also is a setter for the test name the developer wants to run.
2. `test-flush`: A flag to determine LIMPd should delete the previous tests collection from the database. This means this runs the test as if you never ran LIMPd on before, or created any doc before. In most of the cases this should be always present on your test. We didn't set this as the default behaviour in order to make sure developers don't lose access to crucial previous tests collections for running the test command.

One last thing, running LIMP tests workflow would result in `debug` mode set to `True` automatically in order for the developers to detect any unexpected errors.

Let's run the test and see what do we get in the last two lines:
```
2019-05-22 11:56:35,926  [DEBUG]  Finished testing 1 steps [Passed: 0, Failed: 1, Skipped: 0] with success rate of: 0%
2019-05-22 11:56:35,929  [DEBUG]  Full tests log available at: X:\path\to\limp\tests\LIMP-TEST_staff-create_22-May-2019.json
```

That doesn't seem good, eh? Our test had failed. But why? That's what the report would help us know. Let's open the report and explore it. The report has the following attrs:
1. **`test`**: The test details. This is helpful when developers refer to previous tests reports for tests that might have been removed or updated. 
2. **`status`**: The overall text status of the test. It can be `PASSED`, `FAILED` or `PARTIAL`.
3. **`success_rate`**: The success rate of the tests.
4. **`stats`**: The details statistics of `passed`, `failed`, `skipped` and `total` number of steps in the test.
5. **`steps`**: The details of the steps. This is every tested step complete log. Generators in the steps get compiled into the values so you can confirm any unexpected results.

To figure out, what went wrong and why the test was marked failed, let's check the results of the step in `steps`. The results are:
```python
"results": {
	"status": 403,
	"msg": "You don't have permissions to access this endpoint.",
	"args": {
		"code": "CORE_SESSION_FORBIDDEN"
	}
}
```

## Test Step `auth`
It's clear why the test had failed. We attempted calling the method as `ANON` user that doesn't have the privilege required to create staff doc. To resole this issue let's add the `auth` step before the `call` step in our test. The `auth` step allows us to authenticate as any user and make the proceeding steps as the authenticated user. The `auth` step you need to add looks like this:
```python
{
	'step':'auth',
	'var':'email',
	'val':'ADMIN@LIMP.MASAAR.COM',
	'hash':'eyJoYXNoIjpbImVtYWlsIiwiQURNSU5ATElNUC5NQVNBQVIuQ09NIiwiX19BRE1JTiJdfQ'
}
```
The `auth` step has the following attrs:
1. **`var`**: The authentication attr to use. As you are aware from [user and session](/docs/api-user-session.md), we can authenticate using any of the attrs `phone`, `email` or `username`.
2. **`val`**: The authentication attr value.
3. **`hash`**: The authentication hash.

The previous values are perfect for `ADMIN` user of `limp-sample-app`. So, if you changed nothing the previous values should result in successful `auth` step.

Let's run our test again. This time you should get the following final results in LIMPd log:
```
2019-05-22 22:25:23,222  [DEBUG]  Finished testing 2 steps [Passed: 2, Failed: 0, Skipped: 0] with success rate of: 100%
2019-05-22 22:25:23,233  [DEBUG]  Full tests log available at: X:\path\to\limp\tests\LIMP-TEST_staff-create_22-May-2019.1.json
```
The results are more prettier this time. We have 100% success rate, and two steps being passed. You can even have a look at the test report to see the results of both the steps.

## Test Step `test`
Now, let's test the `read` operation. We can do the same by writing a test like this:
```python
'staff-read':[
	{
		'step':'call',
		'module':'staff',
		'method':'read',
		'query':{},
		'doc':{},
		'acceptance':{
			'status':200,
			'args.count':1
		}
	}
]
```
And let's run the test using:
```bash
python limpd.py --env dev --test staff-read --test-flush
```
You won't like the results a lot this time, just like the first time earlier:
```
2019-05-22 22:33:35,694  [DEBUG]  Finished testing 1 steps [Passed: 0, Failed: 1, Skipped: 0] with success rate of: 0%
2019-05-22 22:33:35,697  [DEBUG]  Full tests log available at: X:\path\to\limp\tests\LIMP-TEST_staff-read_22-May-2019.json
```
Just like how we inspected the report, let's do again. The results this time are:
```python
"results": {
	"status": 200,
	"msg": "Found 0 docs.",
	"args": {
		"total": 0,
		"count": 0,
		"docs": [],
		"groups": []
	}
}
```
What's going on? Your test is running using `test-flush` tests workflow arg. This causes the staff created in your test earlier getting deleted before your `staff-read` is run and getting passed. Basically, if you want to test a specific method you should be able to test it even with a fresh install like this scenario. So, in order to test our `read` operation we should first `create` the staff doc then `read` it, right? This is like repeating yourself. This is a very anti-DRY statement. In order to keep you (and us) aligned with DRY standard, we introduced `test` step. `test` step allows developers to run another test as a step. This is unit-testing on steroid; Rather than creating separate integration test workflow, LIMP tests workflow allow you to logically test your methods without the need to rub your head on which to write and run. Our `test` step here should be:
```python
{
	'step':'test',
	'test':'staff-create'
}
```
Yes, that's it! You just nested a whole other test as a step in another test.
Let's run the test and enjoy the more happy results this time:
```
2019-05-22 22:44:05,842  [DEBUG]  Finished testing 2 steps [Passed: 2, Failed: 0, Skipped: 0] with success rate of: 100%

2019-05-22 22:44:05,846  [DEBUG]  Full tests log available at: X:\path\to\limp\tests\LIMP-TEST_staff-read_22-May-2019.1.json
```
Let's now recall what's going on:
1. LIMP was ordered to run `staff-read` test.
2. `staff-read` test is having two steps.
3. First step is a `test` step, referring to `staff-create` test.
4. `staff-create` test has two steps.
5. First step is an `auth` step as `ADMIN` to get privilege required to create a staff doc.
6. Second step is a `call` step to `create` operation on `Staff` module.
7. `staff-create` test is passed and we continue on `staff-read` test steps.
8. `staff-read` second step is `call` step to `read` operation on `Staff` module.
9. Both steps are passed thus declaring the test `PASSED`.

As you see, the workflow is one. Meaning, whatever steps LIMP run as part of the test you wrote it would be run in the same session. In other words, The time when we run the `call` step on `read` operation, we actually called the method as `ADMIN` user. This is not what we are intending to test. We need to make sure `ANON` user is having access to the staff doc just created. In order to do so, we need the `signout` step.

## Test Step `signout`
Similar to the purpose of `auth` step, `signout` allows developers to signout from the current session and attempt to run the proceeding step as `ANON` user. This is helpful to make sure your anonymous users are having access to the public data, that only authenticated users can create. To use the `signout` step, add it after the `test` step and right before `call` step of our `staff-read` test. This would result in our test end up looking like:
```python
'staff-read':[
	{
		'step':'test',
		'test':'staff-create'
	},
	{
		'step':'signout'
	},
	{
		'step':'call',
		'module':'staff',
		'method':'read',
		'query':{},
		'doc':{},
		'acceptance':{
			'status':200,
			'args.count':1
		}
	}
]
```
By running the test again, you still would see happy results (sorry, no more tricks xD). You would also notice that we have ran 3 steps this time:
```
2019-05-22 22:59:15,254  [DEBUG]  Finished testing 3 steps [Passed: 3, Failed: 0, Skipped: 0] with success rate of: 100%
2019-05-22 22:59:15,256  [DEBUG]  Full tests log available at: X:\path\to\limp\tests\LIMP-TEST_staff-read_22-May-2019.2.json
```

That wraps up the reference on how to write tests for LIMP tests workflow. Let's know if you need more steps types. Feel free to create your own and share it with us. And, we would be happy to accept any suggestion in this regard.

## Tests Workflow `test-force` arg
One last aspect to share it with you in LIMP tests workflow is running it with `test-force` arg. By running LIMPd test mode with this arg you ultimately force LIMPd to continue running all tests even if any failed. This is usually not what a developer would like to do, but since we are trying to make a framework for all use-cases we considered adding this feature as well.