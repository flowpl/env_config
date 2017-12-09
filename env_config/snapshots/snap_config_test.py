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
