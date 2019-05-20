# LIMP Module
In LIMP ecosystem, modules are the brains of your app. It's where all your business logic goes. Unlike, MVC architecture, LIMP takes care of everything on your behalf and you only have to define modules that serve as:
1. Data Types (or Models): Every module is a standalone data type. It has its attrs and data extending config.
2. Controllers: Every module has its set of methods. In most cases, you just need to define the base methods and get to go. But, you also can define unlimited number of methods to serve your business logic.
3. Access Control Definitions: That's correct. Every module has its own set of permissions that you can define according to your needs. You can even extend this way beyond you can imagine.

For this, LIMP ideology is to compose modules that are totally standalone in logic, however they can be connected to other modules either by `extns` or by internal calls.

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