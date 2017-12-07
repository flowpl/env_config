from functools import partial
from os import environ


def _load_scalar(parser, default, validator, key):
    try:
        values = parser(environ[key])
        validator(values)
        return values
    except KeyError:
        if not default:
            raise ConfigValueError(key)
        return default
    except BaseException as e:
        raise ConfigParseError(key, e)


def _load_list(parser, default, validator, separator, key):
    try:
        values = [parser(value.strip()) for value in environ[key].split(separator)]
        [validator(value) for value in values]
        return values
    except KeyError:
        if not default:
            raise ConfigValueError(key)
        return default
    except BaseException as e:
        raise ConfigParseError(key, e)


def boolean(value):
    truthy = ['yes', 'true', '1']
    falsy = ['no', 'false', '0']
    if value.lower() in truthy:
        return True
    if value.lower() in falsy:
        return False
    raise ValueError('"{}" is not a valid boolean, allowed values are "{}"'.format(value, '","'.join(truthy + falsy)))


class ConfigError(BaseException):
    pass


class ConfigValueError(ConfigError):
    def __init__(self, variable_name):
        super().__init__()
        self.__variable_name = variable_name

    @property
    def message(self):
        return "environment variable '{}' is missing".format(self.variable_name)

    @property
    def variable_name(self):
        return self.__variable_name

    @property
    def instruction(self):
        return "export {}=[your value here]".format(self.variable_name)

    def __str__(self):
        return self.message


class ConfigParseError(ConfigError):
    def __init__(self, key, previous_error):
        super().__init__()
        self.__key = key
        self.__previous_error = previous_error

    @property
    def key(self):
        return self.__key

    @property
    def previous_error(self):
        return self.__previous_error

    @property
    def message(self):
        return "Error while parsing value for {}: {}".format(self.key, str(self.__previous_error))

    @property
    def instruction(self):
        return "{}: {}".format(self.key, str(self.previous_error))

    def __str__(self):
        return self.message


class ConfigMissingError(ConfigError):
    def __init__(self, key):
        super().__init__()
        self.__key = key

    @property
    def key(self):
        return self.__key

    @property
    def message(self):
        return "Config setting could not be found, call {} before accessing it.".format(self.instruction)

    @property
    def instruction(self):
        return 'declare("{}", [your definition here])'.format(self.key)

    def __str__(self):
        return self.message


class AggregateConfigError(ConfigError):
    def __init__(self, exceptions):
        super().__init__()
        self.__exceptions = exceptions

    @property
    def exceptions(self):
        return self.__exceptions

    @property
    def message(self):
        missing_env_variables = []
        missing_declarations = []
        parse_errors = []
        for ex in self.exceptions:
            if isinstance(ex, ConfigValueError):
                missing_env_variables.append(ex.instruction)
            elif isinstance(ex, ConfigMissingError):
                missing_declarations.append(ex.instruction)
            elif isinstance(ex, ConfigParseError):
                parse_errors.append(ex.instruction)
            else:
                raise RuntimeError(str(ex))

        result = ''
        if len(missing_env_variables) > 0:
            result += 'Missing environment variables:\n'
            result += '\n'.join(sorted(missing_env_variables)) + '\n\n'
        if len(missing_declarations) > 0:
            result += 'Missing declarations:\n'
            result += '\n'.join(sorted(missing_declarations)) + '\n\n'
        if len(parse_errors) > 0:
            result += 'Parse errors:\n'
            result += '\n'.join(sorted(parse_errors)) + '\n\n'
        return result

    def __str__(self):
        return self.message


def parse_int(default=None, validator=lambda x: x):
    return partial(_load_scalar, int, default, validator)


def parse_float(default=None, validator=lambda x: x):
    return partial(_load_scalar, float, default, validator)


def parse_str(default=None, validator=lambda x: x):
    return partial(_load_scalar, lambda x: x, default, validator)


def parse_bool(default=None, validator=lambda x: x):
    return partial(_load_scalar, boolean, default, validator)


def parse_str_list(default=None, validator=lambda x: x, separator=','):
    return partial(_load_list, lambda x: x, default, validator, separator)


def parse_int_list(default=None, validator=lambda x: x, separator=','):
    return partial(_load_list, int, default, validator, separator)


def parse_float_list(default=None, validator=lambda x: x, separator=','):
    return partial(_load_list, float, default, validator, separator)


def parse_bool_list(default=None, validator=lambda x: x, separator=','):
    return partial(_load_list, boolean, default, validator, separator)


def __parse_definition_result(result):
    if isinstance(result, tuple):
        return result[0], result[1]
    else:
        return result, []


def _parse_dict(prefix, definition, defer_raise, tags, current_tag):
    result = {}
    exceptions = []
    for k, v in definition.items():
        variable_name = "{}_{}".format(prefix, k)
        if isinstance(definition[k], dict):
            result[k], ex = \
                __parse_definition_result(_parse_dict(variable_name, definition[k], defer_raise, tags, current_tag))
            exceptions = exceptions + ex
        else:
            try:
                result[k], ex = __parse_definition_result(definition[k](variable_name.upper()))
                exceptions = exceptions + ex
            except BaseException as e:
                if current_tag not in tags:
                    result[k] = e
                elif defer_raise:
                    exceptions.append(e)
                else:
                    raise e
    return result, exceptions


class Config(object):

    def __init__(self, defer_raise=False):
        super().__init__()
        self.__parsed_values = {}
        self.__definitions = {}
        self.__exceptions = []
        self.__defer_raise = defer_raise

    def declare(self, key, definition, tags=('default',), current_tag='default'):
        """
        declare config options
        :param key: string
        :param definition: Any
        :return: None
        """
        self.__definitions[key] = definition
        if isinstance(definition, dict):
            self.__parsed_values[key], exceptions = _parse_dict(key, definition, self.__defer_raise, tags, current_tag)
            self.__exceptions = self.__exceptions + exceptions
        else:
            try:
                self.__parsed_values[key] = definition(key.upper())
            except BaseException as e:
                if current_tag not in tags:
                    self.__parsed_values[key] = e
                elif self.__defer_raise:
                    self.__exceptions.append(e)
                else:
                    raise e

    def reload(self):
        for key, definition in self.__definitions.items():
            self.declare(key, definition)

    def get(self, key):
        value = None
        try:
            value = self.__parsed_values[key]
        except KeyError:
            ex = ConfigMissingError(key)
            if self.__defer_raise:
                self.__exceptions.append(ex)
            else:
                raise ex

        if value and isinstance(value, dict):
            for key, val in value.items():
                if isinstance(val, BaseException):
                    raise val

        if value and isinstance(value, BaseException):
            raise value

        if self.__defer_raise and len(self.__exceptions) > 0:
            raise AggregateConfigError(self.__exceptions)

        return value
