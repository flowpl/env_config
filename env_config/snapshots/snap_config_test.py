# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['ErrorReportingTest::test_do_not_report_the_same_error_multiple_times 1'] = '''Missing environment variables:
export ERR_KEY_1=[your value here]

Missing declarations:
declare("undeclared", [your definition here])

'''

snapshots['ErrorReportingTest::test_report_message_for_missing_environment_variables 1'] = '''Missing environment variables:
export ERR_KEY_1=[your value here]
export ERR_KEY_1_DICT2_DICT3_KEY4=[your value here]
export ERR_KEY_1_DICT2_KEY3=[your value here]

Missing declarations:
declare("undeclared", [your definition here])

Parse errors:
ERR_KEY_1_VALUE1: invalid literal for int() with base 10: 'some int value'
INT_VALUE: invalid literal for int() with base 10: 'some int value'

'''

snapshots['LoadConfigFromFileTest::test_load_bash_file 1'] = '''
Missing exports:
export DICT1_VALUE2=[your value here]
export FIFTH_VARIABLE=[your value here]
export FOURTH_VARIABLE=[your value here]
export SIXTH_VARIABLE=[your value here]
export THIRD_VARIABLE=[your value here]

'''

snapshots['NamespaceTest::test_raise_config_value_error_when_prefixed_variable_does_not_exist 1'] = "environment variable 'NAMESPACE_KEY' is missing"

snapshots['NamespaceTest::test_raise_confiv_missing_error_when_prefixed_variable_is_not_declared 1'] = 'Config setting could not be found, call declare("key", [your definition here]) before accessing it.'

snapshots['NamespaceTest::test_raise_confic_missing_error_when_prefixed_variable_is_not_declared 1'] = 'Config setting could not be found, call declare("key", [your definition here]) before accessing it.'

snapshots['LoggerConfigTest::test_raise_config_error_when_logger_does_not_exist 1'] = 'logger does not exist: missing'
