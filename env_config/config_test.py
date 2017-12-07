from unittest import TestCase
from os import environ

import snapshottest
from ddt import ddt, data
from validators import email, ValidationFailure

from . import Config, ConfigValueError, parse_str, parse_int, parse_float, parse_str_list, \
    parse_int_list, parse_float_list, parse_bool, parse_bool_list, ConfigParseError, ConfigMissingError, \
    AggregateConfigError


def delete_environment_variable(name):
    try:
        del environ[name]
    except KeyError:
        pass


class ConfigParseErrorTest(TestCase):
    def test_parse_error(self):
        prev = RuntimeError('something happened')
        err = ConfigParseError('some_key', prev)
        self.assertEqual('some_key', err.key)
        self.assertEqual(prev, err. previous_error)
        self.assertIn('some_key', err.message)
        self.assertIn('some_key', str(err))


class ConfigValueErrorTest(TestCase):
    def test_value_error(self):
        err = ConfigValueError('some_key')
        self.assertEqual('some_key', err.variable_name)
        self.assertIn('some_key', err.message)
        self.assertIn('some_key', str(err))


class ConfigTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.config = Config()
        delete_environment_variable('KEY')


@ddt
class SkalarValuesTest(ConfigTestCase):

    def test_string(self):
        environ['KEY'] = 'some_value'
        self.config.declare('key', parse_str())
        result = self.config.get('key')
        self.assertEqual(result, 'some_value')

    def test_string_variable_missing(self):
        with self.assertRaises(ConfigValueError):
            self.config.declare('key', parse_str())

    def test_string_return_default(self):
        self.config.declare('key', parse_str('default'))
        result = self.config.get('key')
        self.assertEqual('default', result)

    def test_string_validator_fails(self):
        environ['KEY'] = 'some_value'
        with self.assertRaises(ConfigParseError):
            def validator(input):
                self.assertEqual('some_value', input)
                raise RuntimeError('some message')

            self.config.declare('key', parse_str(validator=validator))

    def test_int(self):
        environ['KEY'] = '1'
        self.config.declare('key', parse_int())
        result = self.config.get('key')
        self.assertEqual(result, 1)

    def test_int_variable_missing(self):
        with self.assertRaises(ConfigValueError):
            self.config.declare('key', parse_int())

    def test_int_return_default(self):
        self.config.declare('key', parse_int(89))
        result = self.config.get('key')
        self.assertEqual(89, result)

    def test_int_validator_fails(self):
        environ['KEY'] = '13'
        with self.assertRaises(ConfigParseError) as context:
            def validator(input):
                self.assertEqual('13', input)
                raise RuntimeError('some message')

            self.config.declare('key', parse_int(validator=validator))
        self.assertEqual(context.exception.key, 'KEY')

    def test_int_value_is_invalid(self):
        environ['KEY'] = 'some_invalid_int'
        with self.assertRaises(ConfigParseError):
            self.config.declare('key', parse_int())

    def test_float(self):
        environ['KEY'] = '1.4'
        self.config.declare('key', parse_float())
        result = self.config.get('key')
        self.assertEqual(result, 1.4)

    def test_float_variable_missing(self):
        with self.assertRaises(ConfigValueError):
            self.config.declare('key', parse_float())

    def test_float_return_default(self):
        self.config.declare('key', parse_float(1.4))
        result = self.config.get('key')
        self.assertEqual(1.4, result)

    def test_float_validator_fails(self):
        environ['KEY'] = '1.4'
        with self.assertRaises(ConfigParseError) as context:
            def validator(input):
                self.assertEqual('1.4', input)
                raise RuntimeError('some message')

            self.config.declare('key', parse_float(validator=validator))

        self.assertEqual(context.exception.key, 'KEY')

    def test_float_value_is_invalid(self):
        environ['KEY'] = 'some_invalid_float'
        with self.assertRaises(ConfigParseError):
            self.config.declare('key', parse_float())

    @data(
        ['TRUE', True],
        ['true', True],
        ['yes', True],
        ['1', True],
        ['false', False],
        ['FALSE', False],
        ['no', False],
        ['0', False],
    )
    def test_bool(self, test_data):
        environ['KEY'] = test_data[0]
        self.config.declare('key', parse_bool())
        result = self.config.get('key')
        self.assertEqual(result, test_data[1])

    def test_bool_variable_missing(self):
        with self.assertRaises(ConfigValueError):
            self.config.declare('key', parse_bool())

    def test_bool_return_default(self):
        self.config.declare('key', parse_bool(True))
        result = self.config.get('key')
        self.assertEqual(True, result)

    def test_bool_validator_fails(self):
        environ['KEY'] = 'true'
        with self.assertRaises(ConfigParseError) as context:
            def validator(input):
                self.assertEqual('true', input)
                raise RuntimeError('some message')

            self.config.declare('key', parse_bool(validator=validator))

        self.assertEqual(context.exception.key, 'KEY')

    def test_bool_value_is_invalid(self):
        environ['KEY'] = 'some_invalid_boolean'
        with self.assertRaises(ConfigParseError):
            self.config.declare('key', parse_bool())


class ListValuesTest(ConfigTestCase):
    def setUp(self):
        super().setUp()
        delete_environment_variable('KEY')

    def test_string_list(self):
        environ['KEY'] = 'one,two,three'
        self.config.declare('key', parse_str_list())
        result = self.config.get('key')
        self.assertEqual(result, ['one', 'two', 'three'])

    def test_string_list_strip_whitespace(self):
        environ['KEY'] = 'one ,\ntwo\t,   three  \t'
        self.config.declare('key', parse_str_list())
        result = self.config.get('key')
        self.assertEqual(result, ['one', 'two', 'three'])

    def test_string_list_variable_missing(self):
        with self.assertRaises(ConfigValueError):
            self.config.declare('key', parse_str_list())

    def test_string_list_different_separator(self):
        environ['KEY'] = 'one-two-three'
        self.config.declare('key', parse_str_list(separator='-'))
        result = self.config.get('key')
        self.assertEqual(['one', 'two', 'three'], result)

    def test_string_list_return_default(self):
        default_value = ['default1', 'default2']
        self.config.declare('key', parse_str_list(default_value))
        result = self.config.get('key')
        self.assertEqual(default_value, result)

    def test_string_list_validator_fails(self):
        environ['KEY'] = 'true,false'
        with self.assertRaises(ConfigParseError) as context:
            def validator(input):
                raise RuntimeError('some message')

            self.config.declare('key', parse_bool_list(validator=validator))

        self.assertEqual(context.exception.key, 'KEY')

    def test_string_list_validator_applied_to_each_element(self):
        environ['KEY'] = 'true,false'
        values_validated = []

        def validator(input):
            nonlocal values_validated
            values_validated.append(input)

        self.config.declare('key', parse_bool_list(validator=validator))
        self.assertListEqual([True, False], values_validated)

    def test_int_list(self):
        environ['KEY'] = '123,456,789'
        self.config.declare('key', parse_int_list())
        result = self.config.get('key')
        self.assertEqual(result, [123, 456, 789])

    def test_int_list_trim_whitespace(self):
        environ['KEY'] = '123\t, 456\n,  789    \t'
        self.config.declare('key', parse_int_list())
        result = self.config.get('key')
        self.assertEqual(result, [123, 456, 789])

    def test_int_list_variable_missing(self):
        with self.assertRaises(ConfigValueError):
            self.config.declare('key', parse_int_list())

    def test_int_list_return_default(self):
        default_value = [1, 4, 7]
        self.config.declare('key', parse_int_list(default_value))
        result = self.config.get('key')
        self.assertEqual(default_value, result)

    def test_int_list_different_separator(self):
        environ['KEY'] = '1-2-3'
        self.config.declare('key', parse_int_list(separator='-'))
        result = self.config.get('key')
        self.assertEqual([1, 2, 3], result)

    def test_int_list_validator_fails(self):
        environ['KEY'] = '1,2'
        with self.assertRaises(ConfigParseError) as context:
            def validator(input):
                raise RuntimeError('some message')

            self.config.declare('key', parse_int_list(validator=validator))

        self.assertEqual(context.exception.key, 'KEY')

    def test_int_list_validator_applied_to_each_element(self):
        environ['KEY'] = '1,2'
        values_validated = []

        def validator(input):
            nonlocal values_validated
            values_validated.append(input)

        self.config.declare('key', parse_int_list(validator=validator))
        self.assertListEqual([1, 2], values_validated)

    def test_int_list_one_value_invalid(self):
        environ['KEY'] = '1,em,45'
        with self.assertRaises(ConfigParseError):
            self.config.declare('key', parse_int_list())

    def test_float_list(self):
        environ['KEY'] = '123,456,789'
        self.config.declare('key', parse_float_list())
        result = self.config.get('key')
        self.assertEqual(result, [123, 456, 789])

    def test_float_list_trim_whitespace(self):
        environ['KEY'] = '123\t, 456\n,  789    \t'
        self.config.declare('key', parse_float_list())
        result = self.config.get('key')
        self.assertEqual(result, [123, 456, 789])

    def test_float_list_variable_missing(self):
        with self.assertRaises(ConfigValueError):
            self.config.declare('key', parse_float_list())

    def test_float_list_return_default(self):
        default_value = [1.3, 5.8, 5.89008]
        self.config.declare('key', parse_float_list(default_value))
        result = self.config.get('key')
        self.assertEqual(default_value, result)

    def test_float_list_different_separator(self):
        environ['KEY'] = '1.4-4.3-9.56'
        self.config.declare('key', parse_float_list(separator='-'))
        result = self.config.get('key')
        self.assertEqual([1.4, 4.3, 9.56], result)

    def test_float_list_validator_fails(self):
        environ['KEY'] = '1.2,4.6'
        with self.assertRaises(ConfigParseError) as context:
            def validator(input):
                raise RuntimeError('some message')

            self.config.declare('key', parse_float_list(validator=validator))

        self.assertEqual(context.exception.key, 'KEY')

    def test_float_list_validator_applied_to_each_element(self):
        environ['KEY'] = '1.2,4.6'
        values_validated = []
        def validator(input):
            nonlocal values_validated
            values_validated.append(input)

        self.config.declare('key', parse_float_list(validator=validator))
        self.assertListEqual([1.2, 4.6], values_validated)

    def test_float_list_one_value_invalid(self):
        environ['KEY'] = '1.9,em,45.0'
        with self.assertRaises(ConfigParseError):
            self.config.declare('key', parse_float_list())

    def test_bool_list(self):
        environ['KEY'] = 'yes,FALSE,1'
        self.config.declare('key', parse_bool_list())
        result = self.config.get('key')
        self.assertEqual(result, [True, False, True])

    def test_bool_list_trim_whitespace(self):
        environ['KEY'] = 'yes\t, FALSE\n,  1    \t'
        self.config.declare('key', parse_bool_list())
        result = self.config.get('key')
        self.assertEqual(result, [True, False, True])

    def test_bool_list_variable_missing(self):
        with self.assertRaises(ConfigValueError):
            self.config.declare('key', parse_bool_list())

    def test_bool_list_return_default(self):
        default_value = [True, True]
        self.config.declare('key', parse_bool_list(default_value))
        result = self.config.get('key')
        self.assertEqual(default_value, result)

    def test_bool_list_different_separator(self):
        environ['KEY'] = 'yes-FALSE-1'
        self.config.declare('key', parse_bool_list(separator='-'))
        result = self.config.get('key')
        self.assertEqual([True, False, True], result)

    def test_bool_list_validator_fails(self):
        environ['KEY'] = 'true,false'
        with self.assertRaises(ConfigParseError) as context:
            def validator(input):
                self.assertEqual(True, input)
                raise RuntimeError('some message')

            self.config.declare('key', parse_bool_list(validator=validator))

        self.assertEqual(context.exception.key, 'KEY')

    def test_bool_list_validator_applied_to_each_element(self):
        environ['KEY'] = 'true,false'
        values_validated = []

        def validator(input):
            nonlocal values_validated
            values_validated.append(input)

        self.config.declare('key', parse_bool_list(validator=validator))
        self.assertListEqual([True, False], values_validated)

    def test_bool_list_one_value_invalid(self):
        environ['KEY'] = 'True,em,No'
        with self.assertRaises(ConfigParseError):
            self.config.declare('key', parse_bool_list())


class FlatDictValuesTest(ConfigTestCase):
    def setUp(self):
        super().setUp()
        delete_environment_variable('KEY_STRING')
        delete_environment_variable('KEY_INT')
        delete_environment_variable('KEY_FLOAT')
        delete_environment_variable('KEY_STRING_LIST')
        delete_environment_variable('KEY_FLOAT_LIST')
        delete_environment_variable('KEY_INT_LIST')
        delete_environment_variable('KEY_ONE')

    def test_dict(self):
        environ['KEY_STRING'] = 'string'
        environ['KEY_INT'] = '1'
        environ['KEY_FLOAT'] = '1.4'
        environ['KEY_BOOL'] = 'false'
        environ['KEY_STRING_LIST'] = 'one,two'
        environ['KEY_FLOAT_LIST'] = '1.4, 3.89'
        environ['KEY_INT_LIST'] = '1,2,3'
        environ['KEY_BOOL_LIST'] = '1,FALSE,no'
        self.config.declare(
            'key',
            {
                'string': parse_str(),
                'int': parse_int(),
                'float': parse_float(),
                'bool': parse_bool(),
                'string_list': parse_str_list(),
                'int_list': parse_int_list(),
                'float_list': parse_float_list(),
                'bool_list': parse_bool_list(),
            },
        )

        result = self.config.get('key')

        self.assertDictEqual(
            {
                'string': 'string',
                'int': 1,
                'float': 1.4,
                'bool': False,
                'string_list': ['one', 'two'],
                'int_list': [1, 2, 3],
                'float_list': [1.4, 3.89],
                'bool_list': [True, False, False],
            },
            result
        )

    def test_dict_variable_missing(self):
        with self.assertRaises(ConfigValueError):
            self.config.declare('key', {'one': parse_str()})

    def test_dict_element_missing(self):
        environ['KEY_STRING'] = 'string'
        with self.assertRaises(ConfigValueError):
            self.config.declare(
                'key',
                {
                    'string': parse_str(),
                    'int': parse_int(),
                },
            )


class NestedDictValuesTest(ConfigTestCase):
    def setUp(self):
        super().setUp()
        delete_environment_variable('KEY_STRING')
        delete_environment_variable('KEY_DICT2_INT')
        delete_environment_variable('KEY_DICT2_DICT3_FLOAT')
        delete_environment_variable('KEY_STRING_LIST')
        delete_environment_variable('KEY_FLOAT_LIST')
        delete_environment_variable('KEY_INT_LIST')

    def test_recursive_dict(self):
        environ['KEY_STRING'] = 'string'
        environ['KEY_DICT2_INT'] = '1'
        environ['KEY_DICT2_DICT3_FLOAT'] = '1.4'
        environ['KEY_STRING_LIST'] = 'one,two'
        environ['KEY_FLOAT_LIST'] = '1.4, 3.89'
        environ['KEY_INT_LIST'] = '1,2,3'
        self.config.declare(
            'key',
            {
                'string': parse_str(),
                'dict2': {
                    'int': parse_int(),
                    'dict3': {
                        'float': parse_float(),
                    },
                },
                'string_list': parse_str_list(),
                'int_list': parse_int_list(),
                'float_list': parse_float_list()
            },
        )

        result = self.config.get('key')

        self.assertDictEqual(
            {
                'string': 'string',
                'dict2': {
                    'int': 1,
                    'dict3': {
                        'float': 1.4,
                    },
                },
                'string_list': ['one', 'two'],
                'int_list': [1, 2, 3],
                'float_list': [1.4, 3.89]
            },
            result
        )

    def test_recursive_dict_nested_element_missing(self):
        environ['KEY_STRING'] = 'string'
        with self.assertRaises(ConfigValueError):
            self.config.declare(
                'key',
                {
                    'string': parse_str(),
                    'dict2': {
                        'dict3': {
                            'float': parse_float(),
                        },
                    }
                },
            )


class GetTest(ConfigTestCase):
    def test_get_without_declare(self):
        with self.assertRaises(ConfigMissingError):
            self.config.get('something')


class ExternalValidationTest(ConfigTestCase):
    def setUp(self):
        super().setUp()
        delete_environment_variable('KEY')

    def test_validate_str(self):
        environ['KEY'] = 'someinvalidemail'

        def email_validator(value):
            result = email(value)
            if isinstance(result, ValidationFailure):
                raise ValueError('"{}" is not a valid email address'.format(value))

        with self.assertRaises(ConfigParseError):
            self.config.declare('key', parse_str(validator=email_validator))


class ReloadTest(ConfigTestCase):
    def setUp(self):
        super().setUp()
        delete_environment_variable('KEY')

    def test_reload(self):
        environ['KEY'] = 'original value'
        self.config.declare('key', parse_str())
        value1 = self.config.get('key')
        self.assertEqual(value1, 'original value')
        environ['KEY'] = 'new value'
        value2 = self.config.get('key')
        self.assertEqual(value2, 'original value')

        self.config.reload()

        value3 = self.config.get('key')
        self.assertEqual(value3, 'new value')


class ErrorReportingTest(ConfigTestCase, snapshottest.TestCase):
    def setUp(self):
        super().setUp()
        self.config = Config(defer_raise=True)
        delete_environment_variable('ERR_KEY_1')
        delete_environment_variable('ERR_KEY_2')
        delete_environment_variable('INT_VALUE')
        delete_environment_variable('UNDECLARED')
        delete_environment_variable('ERR_KEY_1_VALUE1')

    def test_single_value(self):
        self.config.declare('err_key_1', parse_str())
        with self.assertRaises(AggregateConfigError):
            self.config.get('err_key_1')

    def test_multiple_values(self):
        self.config.declare('err_key_1', parse_str())
        self.config.declare('err_key_2', parse_str())
        with self.assertRaises(AggregateConfigError) as context:
            self.config.get('err_key_1')

        self.assertEqual(len(context.exception.exceptions), 3)

    def test_single_dict_value(self):
        self.config.declare('err_key_1', {'value1': parse_str()})
        with self.assertRaises(AggregateConfigError):
            self.config.get('err_key_1')

    def test_nested_dict_values(self):
        self.config.declare(
            'err_key_1',
            {
                'value1': parse_str(),
                'dict2': {
                    'key3': parse_str(),
                    'dict3': {
                        'key4': parse_str()
                    }
                }
            })
        with self.assertRaises(AggregateConfigError) as context:
            self.config.get('err_key_1')

        self.assertEqual(len(context.exception.exceptions), 3)

    def test_report_message_for_missing_environment_variables(self):
        environ['INT_VALUE'] = 'some int value'
        environ['UNDECLARED'] = 'some value'
        environ['ERR_KEY_1_VALUE1'] = 'some int value'

        self.config.declare('err_key_1', parse_int())
        self.config.declare(
            'err_key_1',
            {
                'value1': parse_int(),
                'dict2': {
                    'key3': parse_str(),
                    'dict3': {
                        'key4': parse_str()
                    }
                }
            })
        self.config.declare('int_value', parse_int())
        with self.assertRaises(AggregateConfigError) as context:
            self.config.get('undeclared')

        self.assertMatchSnapshot(str(context.exception))


class ConfigEnvironmentTest(ConfigTestCase):

    def test_do_not_raise_when_declaring_a_variable_in_another_environment(self):
        self.config.declare('optional', parse_str(), ('default',), 'other')

    def test_raise_declare_error_when_getting_a_variable_from_another_environment(self):
        self.config.declare('optional', parse_str(), ('default',), 'other')
        with self.assertRaises(ConfigValueError):
            self.config.get('optional')

    def test_do_not_raise_when_declaring_a_dict_in_another_environment(self):
        self.config.declare('optional', {'value': parse_str()}, ('default',), 'other')

    def test_raise_declare_error_when_getting_a_dict_from_another_environment(self):
        self.config.declare('optional', {'value': parse_str()}, ('default',), 'other')
        with self.assertRaises(ConfigValueError):
            self.config.get('optional')

    def test_do_not_raise_when_declaring_a_list_in_another_environment(self):
        self.config.declare('optional', parse_str_list(), ('default',), 'other')