config_py
=========

Declare and load configuration from environment variables.


Install
-------

.. code-block:: sh

   pip install config



Examples
--------


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

.. code-block:: python

   from env_config import Config, parse_str

   cfg = Config()
   cfg.declare(
       'dict',
       {
          'value1': parse_str(),
          'dict2': {
              'value2': parse_str(),
          },
       },
   )

   # this will load values from two environment variables DICT_VALUE_1 and DICT_DICT2_VALUE2 and return them in the
   # same structure as declared above
   dict_result = cfg.get('dict')


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

It's possible to load variables declared to a tag from a file.

.. code-block:: python

   from env_config import Config, parse_str

   # set variables declared in the test tag to be loaded from the bash file test.sh
   config = Config(tags=dict(test='test.sh'))
   # variable1 is declared in test and the current tag is test. variable1 will be loaded from test.sh
   config.declare('variable1', parse_int(), ('test',), 'test'))
   # variable2 is declared in the default tag. variable2 will be ignored because the current tag is test
   config.declare('variable2', parse_int(), ('default',), 'test')
