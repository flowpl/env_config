import logging
from functools import partial
from os import environ, path, getcwd


MODULE_NAME='env_config'


def _load_scalar(parser, default, validator, key, file_contents):
    try:
        values = parser(environ[key])
    except KeyError:
        try:
            values = parser(file_contents[key])
        except KeyError:
            if default is None:
                raise ConfigValueError(key)
            return default
        except BaseException as e:
            raise ConfigParseError(key, e)
    except BaseException as e:
        raise ConfigParseError(key, e)

    try:
        validator(values)
        return values
    except BaseException as e:
        raise ConfigParseError(key, e)


def _load_list(parser, default, validator, separator, key, file_contents):
    try:
        values = [parser(value.strip()) for value in environ[key].split(separator)]
    except KeyError:
        try:
            values = [parser(value.strip()) for value in file_contents[key].split(separator)]
        except KeyError:
            if default is None:
                raise ConfigValueError(key)
            return default
        except BaseException as e:
            raise ConfigParseError(key, e)
    except BaseException as e:
        raise ConfigParseError(key, e)

    try:
        [validator(value) for value in values]
        return values
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


class ConfigNotInCurrentTagError(ConfigError):
    def __init__(self, key, tag):
        super().__init__()
        self.__key = key
        self.__tag = tag

    @property
    def key(self):
        return self.__key

    @property
    def tag(self):
        return self.__tag

    def __str__(self):
        return 'variable is no defined for current tag (variable: {}, tag: {})'.format(self.key, self.tag)


class AggregateConfigError(ConfigError):
    def __init__(self, exceptions, filename):
        super().__init__()
        self.__exceptions = exceptions
        self.__filename = filename

    @property
    def exceptions(self):
        return self.__exceptions

    @property
    def filename(self):
        return self.__filename

    @property
    def message(self):
        missing_env_variables = set()
        missing_declarations = set()
        parse_errors = set()
        for ex in self.exceptions:
            if isinstance(ex, ConfigValueError):
                missing_env_variables.add(ex.instruction)
            elif isinstance(ex, ConfigMissingError):
                missing_declarations.add(ex.instruction)
            elif isinstance(ex, ConfigParseError):
                parse_errors.add(ex.instruction)
            else:
                raise RuntimeError(str(ex))

        if self.filename:
            result = 'Errors in config file {}:\n\n'.format(self.filename)
        else:
            result = ''
        if len(missing_env_variables) > 0:
            if self.filename:
                result += 'Missing exports:\n'
            else:
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


class ConfigFileEmptyError(ConfigError):
    def __init__(self, file_name):
        super().__init__()
        self.__file_name = file_name

    def __str__(self):
        return 'Config file does not export any variables {}. Check the bash docs on how to export variables.'\
            .format(self.__file_name)


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


def _parse_dict(prefix, definition, defer_raise, tags, current_tag, file_contents):
    result = {}
    exceptions = []
    for k, v in definition.items():
        variable_name = "{}_{}".format(prefix, k)
        if isinstance(definition[k], dict):
            result[k], ex = __parse_definition_result(
                _parse_dict(variable_name, definition[k], defer_raise, tags, current_tag, file_contents))
            exceptions = exceptions + ex
        else:
            try:
                result[k], ex = __parse_definition_result(definition[k](variable_name.upper(), file_contents))
                exceptions = exceptions + ex
            except BaseException as e:
                if current_tag not in tags:
                    result[k] = ConfigNotInCurrentTagError(k, current_tag)
                elif defer_raise:
                    exceptions.append(e)
                else:
                    raise e
    return result, exceptions


def _read_file(filename):
    variable_marker = 'export ' # which variables to load
    key_value_divider = '='
    result = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            if len(line) == 0 or line[0] == '#' or len(line) < len(variable_marker):
                continue
            if line[:len(variable_marker)] == variable_marker:
                parts = line.replace(variable_marker, '').split(key_value_divider)
                result[parts[0]] = parts[1].strip('"\'\n')
    if len(result.keys()) == 0:
        raise ConfigFileEmptyError(filename)
    return result


class Config(object):

    def __init__(self, defer_raise=True, filename_variable=None):
        """
        Create a new Config object

        :param defer_raise: bool Whether to show errors as an aggregated report or fail on the first error found.
        :param filename_variable: str The variable name from which to get the file name
        """
        super().__init__()
        self.__parsed_values = {}
        self.__definitions = {}
        self.__exceptions = []
        self.__defer_raise = defer_raise
        self.__file_contents = {}
        self.__filename_variable = filename_variable
        self.__filename = None
        self.__tags = {}
        self.__logger = logging.getLogger(MODULE_NAME)

    @property
    def logger(self):
        return self.__logger

    def declare(self, key, definition, tags=('default',), current_tag='default'):
        """
        declare config options
        :param key: string
        :param definition: Any
        :param tags: set(str) list of tags that this variable should exist in
        :param current_tag: str the tag to declare this variable for
        :return: None
        """
        if current_tag in tags and current_tag not in self.__file_contents:
            try:
                filename = path.join(getcwd(), environ[self.__filename_variable])
                try:
                    self.__file_contents = _read_file(filename)
                    self.__filename = filename
                except FileNotFoundError as e:
                    self.logger.warning(
                        'Config file not found. Ignoring. {{"filename_variable": "{0}", "filename": "{1}"}}'.format(
                            self.__filename_variable,
                            e.filename
                        )
                    )
            except (KeyError, TypeError):
                pass
        elif current_tag not in self.__tags:
            self.__file_contents = {}
        self.__definitions[key] = definition
        if isinstance(definition, dict):
            self.__parsed_values[key], exceptions = \
                _parse_dict(key, definition, self.__defer_raise, tags, current_tag, self.__file_contents)
            self.__exceptions = self.__exceptions + exceptions
        else:
            try:
                self.__parsed_values[key] = definition(key.upper(), self.__file_contents)
            except BaseException as e:
                if current_tag not in tags:
                    self.__parsed_values[key] = ConfigNotInCurrentTagError(key, current_tag)
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
            raise AggregateConfigError(self.__exceptions, self.__filename)

        return value
