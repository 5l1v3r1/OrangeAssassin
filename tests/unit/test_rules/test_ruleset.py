"""Tests for sa.rules.ruleset"""

import unittest

try:
    from unittest.mock import patch, Mock, PropertyMock
except ImportError:
    from mock import patch, Mock, PropertyMock

import sa.rules.ruleset


class TestRuleSet(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        patch.stopall()

    def test_match(self):
        mock_msg = Mock(rules_checked={})
        mock_rule = Mock()
        ruleset = sa.rules.ruleset.RuleSet()
        ruleset.checked = {"TEST_RULE": mock_rule}

        ruleset.match(mock_msg)

        mock_rule.match.assert_called_with(mock_msg)
        self.assertEqual(mock_msg.rules_checked["TEST_RULE"],
                         mock_rule.match(mock_msg))

    def test_get_rule(self):
        mock_rule = Mock()
        ruleset = sa.rules.ruleset.RuleSet()
        ruleset.checked = {"TEST_RULE": mock_rule}

        self.assertEqual(ruleset.get_rule("TEST_RULE"), mock_rule)

    def test_get_rule_not_checked(self):
        mock_rule = Mock()
        ruleset = sa.rules.ruleset.RuleSet()
        ruleset.not_checked = {"TEST_RULE": mock_rule}

        self.assertEqual(ruleset.get_rule("TEST_RULE"), mock_rule)

    def test_get_rule_check_only(self):
        mock_rule = Mock()
        ruleset = sa.rules.ruleset.RuleSet()
        ruleset.not_checked = {"TEST_RULE": mock_rule}

        self.assertRaises(KeyError, ruleset.get_rule, "TEST_RULE",
                          checked_only=True)

    def test_add_rule_should_check(self):
        mock_rule = Mock(**{"should_check.return_value": True})
        name_mock = PropertyMock(return_value="TEST_RULE")
        type(mock_rule).name = name_mock

        ruleset = sa.rules.ruleset.RuleSet()
        ruleset.add_rule(mock_rule)
        self.assertEqual(ruleset.checked, {"TEST_RULE": mock_rule})
        self.assertEqual(ruleset.not_checked, {})

    def test_add_rule_should_not_check(self):
        mock_rule = Mock(**{"should_check.return_value": False})
        name_mock = PropertyMock(return_value="TEST_RULE")
        type(mock_rule).name = name_mock

        ruleset = sa.rules.ruleset.RuleSet()
        ruleset.add_rule(mock_rule)
        self.assertEqual(ruleset.checked, {})
        self.assertEqual(ruleset.not_checked, {"TEST_RULE": mock_rule})

    def test_add_rule_preprocess(self):
        mock_rule = Mock()
        ruleset = sa.rules.ruleset.RuleSet()

        ruleset.add_rule(mock_rule)
        mock_rule.preprocess.assert_called_with(ruleset)

    def test_add_rule_postprocess(self):
        mock_rule = Mock()
        ruleset = sa.rules.ruleset.RuleSet()

        ruleset.add_rule(mock_rule)
        mock_rule.postprocess.assert_called_with(ruleset)


def suite():
    """Gather all the tests from this package in a test suite."""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestRuleSet, "test"))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
