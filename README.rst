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
