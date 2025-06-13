import unittest
import sys
import os
import unittest

import sys
import os
import unittest

# Add the parent directory (/app) to sys.path to find the 'app' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app as dash_app_instance

class TestAppBasic(unittest.TestCase):

    def test_app_initialization(self):
        self.assertIsNotNone(dash_app_instance, "Dash app instance should be initialized.")
        if hasattr(dash_app_instance, 'server'):
             self.assertIsNotNone(dash_app_instance.server, "Dash app server should be initialized.")

    def test_app_layout_defined(self):
        self.assertIsNotNone(dash_app_instance, "Dash app instance must be initialized to check layout.")
        self.assertIsNotNone(dash_app_instance.layout, "Dash app layout should be defined.")
        is_dash_component = hasattr(dash_app_instance.layout, 'to_plotly_json')
        self.assertTrue(is_dash_component, "Layout should be a Dash component.")

if __name__ == '__main__':
    unittest.main()
