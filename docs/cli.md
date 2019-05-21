# CLI Interface
LIMPd is your one-stop script in LIMP ecosystem. It allows you to [install dependencies](/dependencies.md), [test your packages](/tests.md), and of course run your app with highly config runtime command line args. Full reference to usage of LIMP CLI interface:
```
usage: limpd.py [-h] [--version] [--install-deps] [--env ENV] [--debug]
                [--packages PACKAGES] [-p PORT] [--test TEST] [--test-flush]
                [--test-force]

optional arguments:
  -h, --help            show this help message and exit
  --version             Show LIMP version and exit
  --install-deps        Install dependencies for LIMP and packages.
  --env ENV             Choose specific env
  --debug               Enable debug mode
  --packages PACKAGES   List of packages separated by commas to be loaded
  -p PORT, --port PORT  Set custom port [default 8081]
  --test TEST           Run specified test.
  --test-flush          Flush previous test data collections
  --test-force          Force running all test steps even if one is failed
  ```