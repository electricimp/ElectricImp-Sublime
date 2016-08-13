########################################################################
# This is a sceleton for plugin unit tests. More tests to be added here. 

# The tests can be run from the Sublime Text Console this way:
# > window.run_command("run_all_tests")
########################################################################

import os
import sys
import sublime
import sublime_plugin
import unittest

sys.path.append(os.path.dirname(__file__))

import imp_developer

test_classes = [
	OSTests
]

current_window = None

class RunAllTestsCommand(sublime_plugin.WindowCommand):
	def run(self):
		global test_classes, current_window
		current_window = self
		for klass in test_classes:
			suite = unittest.TestLoader().loadTestsFromTestCase(klass)
			unittest.TextTestRunner(verbosity=2).run(suite)

class OSTests(unittest.TestCase):
	"""OS specific tests"""

	# Verifies that the platform executable exists on the platform
	def test_platform_executable_exists(self):
		global current_window
		create_project_command = imp_developer.ImpCreateProjectCommand(current_window)
		path = create_project_command.get_sublime_path()
		self.assertTrue(os.path.exists(path))
