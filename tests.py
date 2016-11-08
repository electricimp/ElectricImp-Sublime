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

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "plugin_tests"))

import plugin_tests
from plugin_tests import os_tests
from plugin_tests import preproc_error_origin

plugin_tests = imp.reload(plugin_tests)
plugin_tests.os_tests = imp.reload(plugin_tests.os_tests)
plugin_tests.preproc_error_origin = imp.reload(plugin_tests.preproc_error_origin)

test_classes = [
    os_tests.OSTests,
    preproc_error_origin.PreprocTests
]

class RunAllTestsCommand(sublime_plugin.WindowCommand):
    def run(self):
        global test_classes
        for klass in test_classes:
            suite = unittest.TestLoader().loadTestsFromTestCase(klass)
            unittest.TextTestRunner(verbosity=2).run(suite)
