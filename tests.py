# Copyright (c) 2016 Electric Imp
# This file is licensed under the MIT License
# http://opensource.org/licenses/MIT

########################################################################
# This is a sceleton for plugin unit tests. More tests to be added here. 

# The tests can be run from the Sublime Text Console this way:
# > window.run_command("run_all_tests")
########################################################################

import os
import sys

import imp
import sublime_plugin
import unittest

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
CODE_DIRS = [
    # 'plugin_tests',
]
sys.path += [BASE_PATH] + [os.path.join(BASE_PATH, f) for f in CODE_DIRS]

# Reload plugin files on change
if 'plugin_tests' in sys.modules:
    imp.reload(sys.modules['plugin_tests'])
from plugin_tests import os_tests

sys.path.append(os.path.dirname(__file__))

test_classes = [
    os_tests.OSTests
]

current_window = None


class RunAllTestsCommand(sublime_plugin.WindowCommand):
    def run(self):
        global test_classes, current_window
        current_window = self
        for klass in test_classes:
            suite = unittest.TestLoader().loadTestsFromTestCase(klass)
            unittest.TextTestRunner(verbosity=2).run(suite)
