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

import sublime_plugin
import unittest

from .plugin_tests import os_tests
from .plugin_tests import preproc_error_origin

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
