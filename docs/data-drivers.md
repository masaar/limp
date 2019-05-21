# Data Controller and Drivers
When LIMP started years back with version 1, there were always much of databases of choice. The original team wasn't sure 100% about which technology to adapt which resulted in the ultimate belief *Data Controller and Data Drivers show always remain pluggable*.

LIMP doesn't support any driver for data (in other words doesn't support no database but) [MongoDB](https://mongodb.com). That's why the `drivers` folder in LIMP root has only one driver. The driver is a mirror of the Data Controller which is the class located at https://github.com/masaar/limp/data.py. The Data Controller has the following methods:
1. `create_conn`: This method calls the Driver and request a new connection to be initialised.
2. `read`: This method calls the Driver and passes the `collection` and the `query` to be executed on the database.
3. `create`: This method calls the Driver and passes the `collection` and the `doc` to be created on the database.
4. `update`: This method calls the Driver and passes the `collection` and the `query`, and `update` to update the set of docs the database.
5. `delete`: This method calls the Driver and passes the `collection` and the `query` to delete set of docs on the database.
6. `drop`: This method calls the Driver and passes the `collection` to be dropped from the database.

Additionally, it has two methods for internal use which are:
1. `singleton`: This is a requirement of the Python `metaclass` created to abstract all classes in LIMP. It also converts the class variable `driver` from the string to the object representing the Driver.
2. `sanitise_attrs`: Ultimately, this method was introduced in order to convert `BaseModule` instances passed as part of `query` and `doc` args to `BSON ObjectId`. this happens by extracting the `_id` value of these objects.

# Create a Driver for LIMP
We definitely are looking forward to have more and more Data Drivers supported. As it's hard to write down technical specs for this part of LIMP, we suggest that you have a look at the inners of https://github.com/masaar/limp/drivers/mongodb.py. Try to replicate the same for your database of choice, and if you feel stuck are something needs more clarification don't hesitate to request for help using [Github issues](https://github.com/masaar/limp/issues).