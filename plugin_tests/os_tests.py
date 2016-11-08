# Copyright (c) 2016 Electric Imp
# This file is licensed under the MIT License
# http://opensource.org/licenses/MIT

import os
import unittest
import sublime

import imp_developer


class OSTests(unittest.TestCase):
    """OS specific tests"""

    # Verifies that the platform executable exists on the platform
    def test_platform_executable_exists(self):
        create_project_command = imp_developer.ImpCreateProjectCommand(sublime.active_window())
        path = create_project_command.get_sublime_path()
        self.assertTrue(os.path.exists(path))
