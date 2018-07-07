config_py
=========

Declare and load configuration from environment variables.

Supported features:

- declare different sets of variables for production, test and other environments
- load variables from file if necessary
- parse configuration into different datatypes

  - str
  - int
  - float
  - bool ('True', 'False', 1, 0, 'yes', 'no')
  - str[]
  - int[]
  - float[]
  - bool[]
  - nested types
- easy to work with reports about missing variables and declaration issues

  .. code-block:: python

     Missing environment variables:
     export ERR_KEY_1=[your value here]
     export ERR_KEY_1_DICT2_DICT3_KEY4=[your value here]
     export ERR_KEY_1_DICT2_KEY3=[your value here]

     Missing declarations:
     declare("undeclared", [your definition here])

     Parse errors:
     ERR_KEY_1_VALUE1: invalid literal for int() with base 10: 'some int value'


Install
-------

.. code-block:: sh

   pip install config



Examples
--------

* `Create a new Config instance`_
* `Declare and load scalar values`_
* `Declare and load list values`_
* `Declare and load nested values`_
* `Namespace your variables`_
* `Add validation`_
* `Reloading configuration at runtime`_
* `Declaring optional variables`_
* `Loading variables from a file`_


Create a new Config instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from env_config import

   # control error reporting.
   # If deferred, config errors are raised the first time Config.get() is called.
   # The error message contains a detailed report about all errors encountered while parsing config variables.
   # If not deferred, Config raises on the first error encountered. This most likely happens while calling Config.declare().
   # Default is defer_raise=True
   cfg = Config(defer_raise=False)

   # load config from a file. See a more detailed example further down.
   cfg = Config(filename_variable='CONFIG_FILE')


Declare and load scalar values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from env_config import Config, parse_int, parse_float, parse_str, parse_bool

   cfg = Config()

   # declare variables with the appropriate parser
   cfg.declare('my_int_variable', parse_int())
   cfg.declare('my_float_variable', parse_float())
   cfg.declare('my_str_variable', parse_str())
   cfg.declare('my_bool_variable', parse_bool())

   # load the values

   # will load the value of MY_INT_VARIABLE as an int
   int_result = cfg.get('my_int_variable')
   # will load the value of MY_FLOAT_VARIABLE as a float
   float_result  = cfg.get('my_float_variable')
   # will load the value of MY_STR_VARIABLE as a str
   str_result = cfg.get('my_str_variable')


Declare and load list values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from env_config import Config, parse_int_list

   cfg = Config()

   # declare variables with the appropriate parser
   cfg.declare('my_int_list_variable', parse_int_list())

   # load the values

   # will load the value of MY_INT_LIST_VARIABLE as a list of ints.
   # By default it assumes the elements to be comma separated
   int_list_result = cfg.get('my_int_list_variable')


Declare and load nested values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most libraries need multiple variables to be correctly configured.
Nested values help reduce boilerplate necessary to wire configuration with the library.

.. code-block:: python

   from env_config import Config, parse_str
   import psycopg2

   cfg = Config()
   cfg.declare(
       'database',
       {
          'dbname': parse_str(),
          'user': parse_str(),
          'password': parse_str()
       },
   )

   # this will load values from these environment variables and parse them into a dict:
   #  - DATABASE_DBNAME
   #  - DATABASE_USER
   #  - DATABASE_PASSWORD

   psyco_config = cfg.get('database')
   # the dict will look like this: {'dbname': 'some value', 'user': 'username', 'password': 'vsjkfl'}
   psyco_connection = psycopg2.connect(**psyco_config)


Namespace your variables
^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

   from env_config import Config, parse_str
   import psycopg2

   cfg = Config(namespace='my_prefix')
   cfg.declare('database')

   # the value will be loaded from the environment variable: MY_PREFIX_DATABASE
   value = cfg.get('database')


Add validation
^^^^^^^^^^^^^^

.. code-block:: python

   from env_config import Config, parse_str, parse_str_list
   from validators import email

   # config expects validators to raise an Error on failure.
   # Since the validators package returns Failures instead of raising, we create a small adapter.
   def email_validator(value):
       result = email(value)
       if isinstance(result, ValidationFailure):
           raise ValueError('"{}" is not a valid email address'.format(value))

   cfg = Config()

   cfg.declare('valid_email', parse_str(validator=email_validator))
   # this also works with lists. The validator function is applied to each value separately
   cfg.declare('valid_list_of_emails, parse_str_list(validator=email_validator))

   valid_email = cfg.get('valid_email')
   valid_list_of_emails = cfg.get('valid_list_of_emails')


Reloading configuration at runtime
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from env_config import Config, parse_str, reload

   cfg = Config()
   cfg.declare('some_value', parse_str())
   value = cfg.get('some_value')

   # Values are actually loaded during declare().
   # Changes to the environment at runtime are not picked up automatically.
   # Relaoding has to be triggered explicitly.

   cfg.reload()

   new_value = cfg.get('some_value')


Declaring optional variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes you just want to load a subset of all variables. For example most applications nowadays get executed
in a live environment and in a testing environment.
Another example is different processes, for example a web endpoint and a background worker, sharing configuration setup.

.. code-block:: python

   # config.py

   from env_config import Config, parse_str

   def declare_config(tag):
      required = ('live', 'test')
      test_optional = ('live',)

      cfg = Config()
      # this variable is available both in live and test
      cfg.declare('some_value', parse_str(), required, tag)
      # this variable is only available in live. In test it won't be loaded and only raises an error when accessed.
      cfg.declare('some_other_value', parse_str(), test_optional, tag)
      return cfg

.. code-block:: python

   # live-app.py

   from config import declare_config

   # the active tag is 'live', so all variables tagged with 'live' are required and raise errors when missing.
   cfg = declare_config('live')

   # access variables
   val = cfg.get('some_value')

.. code-block:: python

   # something_test.py

   from config import declare_config

   # the active tag is 'test', so all variables tagged with 'test' are required and raise errors when missing.
   # All other variables become optional and only raise errors when accessed with
   cfg.declare_config('test')

   # access variables
   val = cfg.get('some_value')

   # raise an error, because the variable is not available in 'test'
   val2 = cfg.get('some_other_value')


Loading variables from a file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes it's rather cumbersome to declare all the variables explicitly.
For example the PyCharm variable declaration is rather awkward to use.

To elegantly deal with these kinds of situations, it's possible to load variables declared to a tag from a bash file.
So only one variable (the file name) has to be declared. The rest is loaded from that file.
The file is not evaluated, though. Only :code:`export` declarations are extracted and parsed into variables.


define the variable holding the file name

.. code-block:: bash

   export CONFIG_FILE=test.sh


Create a file test.sh with the variable declarations.

.. code-block:: bash

   #!/usr/bin/env bash

   # comment is ignored

   HIDDEN_VARIABLE="value not parsed"
   export VISIBLE_VARIABLE_1="this value will be available"

   function {
      # if the line does not start with export it's ignored
   }

   # variables inside strings are not expanded. The value will contain the literal :code:`$OTHER_VARIABLE`.
   export VARIABLE_CONTAINING_REFERENCE="$OTHER_VARIABLE"


Then setup the CONFIG_FILE variable to load the file.


.. code-block:: python

   from env_config import Config, parse_str

   # uses the value of CONFIG_FILE as the file name to load variables from
   config = Config(filename_variable='CONFIG_FILE', defer_raise=False)
   # visible_variable_1 is declared in test and the current tag is test. variable1 will be loaded from test.sh
   config.declare('visible_variable_1', parse_int(), ('test',), 'test'))

   # visible_variable_2 is declared in the 'default' tag and not available in the config file.
   # visible_variable_2 will be ignored because the current tag is 'test'
   config.declare('visible_variable_1', parse_int(), ('default',), 'test')
