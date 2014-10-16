"""Tests for sa.context"""

import unittest

try:
    from unittest.mock import patch, Mock, MagicMock, mock_open
except ImportError:
    from mock import patch, Mock, MagicMock, mock_open

import sa.errors
import sa.context


class TestContext(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        patch.stopall()

    def test_set_plugin_data(self):
        context = sa.context._Context()
        context.set_plugin_data("test_plugin", "test", "value")
        self.assertEqual(context.plugin_data,
                         {"test_plugin": {"test": "value"}})

    def test_get_plugin_data(self):
        context = sa.context._Context()
        context.plugin_data["test_plugin"]["test"] = "value"
        result = context.get_plugin_data("test_plugin", "test")
        self.assertEqual(result, "value")

    def test_get_plugin_data_all(self):
        context = sa.context._Context()
        context.plugin_data["test_plugin"]["test"] = "value"
        result = context.get_plugin_data("test_plugin")
        self.assertEqual(result, {"test": "value"})

    def test_del_plugin_data(self):
        context = sa.context._Context()
        context.plugin_data["test_plugin"]["test"] = "value"
        context.del_plugin_data("test_plugin", "test")
        self.assertEqual(context.plugin_data,
                         {"test_plugin": {}})

    def test_del_plugin_data_all(self):
        context = sa.context._Context()
        context.plugin_data["test_plugin"]["test"] = "value"
        context.del_plugin_data("test_plugin")
        self.assertEqual(context.plugin_data, {})

    def test_pop_plugin_data(self):
        context = sa.context._Context()
        context.plugin_data["test_plugin"]["test"] = "value"
        result = context.pop_plugin_data("test_plugin", "test")
        self.assertEqual(context.plugin_data, {"test_plugin": {}})
        self.assertEqual(result, "value")

    def test_pop_plugin_data_all(self):
        context = sa.context._Context()
        context.plugin_data["test_plugin"]["test"] = "value"
        result = context.pop_plugin_data("test_plugin")
        self.assertEqual(context.plugin_data, {})
        self.assertEqual(result, {"test": "value"})


class TestGlobalContextLoadPlugin(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.mock_module = MagicMock()
        self.mock_import = patch("sa.context.importlib").start()
        self.mock_load2 = patch("sa.context.GlobalContext._load_module_py2",
                                return_value=self.mock_module).start()
        self.mock_load3 = patch("sa.context.GlobalContext._load_module_py3",
                                return_value=self.mock_module).start()
        self.mock_unload = patch("sa.context.GlobalContext."
                                 "unload_plugin").start()
        self.mock_issubclass = patch("sa.context.issubclass",
                                     create=True).start()
        self.mock_py3 = patch("sa.context.future.utils", MagicMock()).start()

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        patch.stopall()

    def test_load_plugin_load_module(self):
        ctxt = sa.context.GlobalContext()
        ctxt.load_plugin("sa.plugins.test_plugin.TestPlugin")
        self.mock_import.import_module.assert_called_with("sa.plugins.test_plugin")

    def test_load_plugin_load_module_already_loaded(self):
        ctxt = sa.context.GlobalContext()
        ctxt.plugins["TestPlugin"] = Mock()
        ctxt.load_plugin("sa.plugins.test_plugin.TestPlugin")
        self.mock_unload.assert_called_once_with("TestPlugin")
        self.mock_import.import_module.assert_called_with("sa.plugins.test_plugin")

    def test_load_plugin_load_module_import_error(self):
        self.mock_import.import_module.side_effect = ImportError()
        ctxt = sa.context.GlobalContext()
        self.assertRaises(sa.errors.PluginLoadError, ctxt.load_plugin,
                          "sa.plugins.test_plugin.TestPlugin")

    def test_load_plugin_from_path_py3(self):
        self.mock_py3.PY3 = True
        ctxt = sa.context.GlobalContext()
        ctxt.load_plugin("TestPlugin", "/etc/sa/plugins/test_plugin.py")
        self.assertFalse(self.mock_import.import_module.called)
        self.assertFalse(self.mock_load2.called)
        self.mock_load3.assert_called_with("/etc/sa/plugins/test_plugin.py")

    def test_load_plugin_from_path_py2(self):
        self.mock_py3.PY3 = False
        ctxt = sa.context.GlobalContext()
        ctxt.load_plugin("TestPlugin", "/etc/sa/plugins/test_plugin.py")
        self.assertFalse(self.mock_import.import_module.called)
        self.assertFalse(self.mock_load3.called)
        self.mock_load2.assert_called_with("/etc/sa/plugins/test_plugin.py")

    def test_load_plugin_load_module_missing_plugin_class(self):
        ctxt = sa.context.GlobalContext()
        self.mock_module.TestPlugin = None
        self.assertRaises(sa.errors.PluginLoadError, ctxt.load_plugin,
                          "TestPlugin", "/etc/sa/plugins/test_plugin.py")

    def test_load_plugin_load_module_not_subclass(self):
        ctxt = sa.context.GlobalContext()
        self.mock_issubclass.return_value = False
        self.assertRaises(sa.errors.PluginLoadError, ctxt.load_plugin,
                          "TestPlugin", "/etc/sa/plugins/test_plugin.py")

    def test_load_plugin_register_rules(self):
        plugin_obj = self.mock_module.TestPlugin.return_value
        plugin_obj.eval_rules = ("test_eval_rule",)
        ctxt = sa.context.GlobalContext()
        ctxt.load_plugin("TestPlugin", "/etc/sa/plugins/test_plugin.py")

        self.assertEqual(ctxt.eval_rules["test_eval_rule"],
                         plugin_obj.test_eval_rule)

    def test_load_plugin_register_rules_redefined(self):
        plugin_obj = self.mock_module.TestPlugin.return_value
        plugin_obj.eval_rules = ("test_eval_rule",)
        ctxt = sa.context.GlobalContext()
        ctxt.eval_rules["test_eval_rule"] = Mock()

        ctxt.load_plugin("TestPlugin", "/etc/sa/plugins/test_plugin.py")
        self.assertEqual(ctxt.eval_rules["test_eval_rule"],
                         plugin_obj.test_eval_rule)

    def test_load_plugin_register_rules_undefined(self):
        plugin_obj = self.mock_module.TestPlugin.return_value
        plugin_obj.eval_rules = ("test_eval_rule",)
        plugin_obj.test_eval_rule = None

        ctxt = sa.context.GlobalContext()
        self.assertRaises(sa.errors.PluginLoadError, ctxt.load_plugin,
                          "TestPlugin", "/etc/sa/plugins/test_plugin.py")


class TestGlobalContextLoadModule(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.mock_machinery = patch("sa.context.importlib.machinery",
                                    create=True).start()
        self.mock_imp = patch("sa.context.imp.load_module", create=True).start()
        self.mock_open = patch("sa.context.open", mock_open(),
                               create=True).start()

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        patch.stopall()

    def test_py3(self):
        ctxt = sa.context.GlobalContext()
        result = ctxt._load_module_py3("/etc/sa/plugins/test_plugin.py")
        self.mock_machinery.SourceFileLoader.assert_called_with(
            "test_plugin", "/etc/sa/plugins/test_plugin.py")
        expected = self.mock_machinery.SourceFileLoader(
            "test_plugin", "/etc/sa/plugins/test_plugin.py").load_module()
        self.assertEqual(result, expected)

    def test_py2(self):
        ctxt = sa.context.GlobalContext()
        result = ctxt._load_module_py2("/etc/sa/plugins/test_plugin.py")
        mock_openf = self.mock_open("/etc/sa/plugins/test_plugin.py", "U")
        expected = self.mock_imp("test_plugin", mock_openf,
                                 "/etc/sa/plugins/test_plugin.py",
                                 ('.py', 'U', 1))
        self.assertEqual(result, expected)

    def test_py2_no_valid_suffix(self):
        ctxt = sa.context.GlobalContext()
        self.assertRaises(sa.errors.PluginLoadError, ctxt._load_module_py2,
                          "/etc/sa/plugins/test_plugin.pyx")


class TestGlobalContextUnloadPlugin(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        patch.stopall()

    def test_unload(self):
        ctxt = sa.context.GlobalContext()
        ctxt.plugins["TestPlugin"] = MagicMock()

        ctxt.unload_plugin("TestPlugin")
        self.assertNotIn("TestPlugin", ctxt.plugins)

    def test_unload_not_loaded(self):
        ctxt = sa.context.GlobalContext()
        self.assertRaises(sa.errors.PluginLoadError, ctxt.unload_plugin,
                          "TestPlugin")

    def test_unload_delete_eval_rules(self):
        ctxt = sa.context.GlobalContext()
        ctxt.plugins["TestPlugin"] = MagicMock(eval_rules=["test_eval_rule"])
        ctxt.eval_rules["test_eval_rule"] = MagicMock()

        ctxt.unload_plugin("TestPlugin")
        self.assertEqual(ctxt.eval_rules, {})

    def test_unload_remove_plugin_data(self):
        ctxt = sa.context.GlobalContext()
        ctxt.plugins["TestPlugin"] = MagicMock()
        ctxt.plugin_data["TestPlugin"]["test"] = "value"

        ctxt.unload_plugin("TestPlugin")
        self.assertEqual(ctxt.plugin_data, {})


def suite():
    """Gather all the tests from this package in a test suite."""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestContext, "test"))
    test_suite.addTest(unittest.makeSuite(TestGlobalContextLoadPlugin, "test"))
    test_suite.addTest(unittest.makeSuite(TestGlobalContextLoadModule, "test"))
    test_suite.addTest(unittest.makeSuite(TestGlobalContextUnloadPlugin, "test"))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
