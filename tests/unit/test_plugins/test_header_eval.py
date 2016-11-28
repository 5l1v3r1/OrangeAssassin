import unittest
import collections

try:
    from unittest.mock import patch, Mock, MagicMock, call
except ImportError:
    from mock import patch, Mock, MagicMock, call

import pad.plugins.header_eval


class TestHeaderEval(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.local_data = {}
        self.global_data = {}
        self.mock_ctxt = MagicMock()
        self.mock_msg = MagicMock()
        self.plugin = pad.plugins.header_eval.HeaderEval(self.mock_ctxt)
        self.plugin.set_local = lambda m, k, v: self.local_data.__setitem__(k,
                                                                            v)
        self.plugin.get_local = lambda m, k: self.local_data.__getitem__(k)
        self.plugin.set_global = self.global_data.__setitem__
        self.plugin.get_global = self.global_data.__getitem__
        self.mock_ruleset = MagicMock()
        self.mock_locale = patch("pad.plugins.header_eval."
                                 "pad.locales.charset_ok_for_locales").start()

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        patch.stopall()

    def test_check_for_fake_aol_relay_in_rcvd_spam(self):
        header = ("from unknown (HELO mta05bw.bigpond.com) (80.71.176.130) "
                  "by rly-xw01.mx.aol.com with QMQP; Sat, 15 Jun 2002 "
                  "23:37:16 -0000")
        self.mock_msg.get_decoded_header.return_value = [header]
        result = self.plugin.check_for_fake_aol_relay_in_rcvd(self.mock_msg)
        self.assertTrue(result)

    def test_check_for_fake_aol_relay_in_rcvd_not_spam1(self):
        header = ("from  rly-xj02.mx.aol.com (rly-xj02.mail.aol.com "
                  "[172.20.116.39]) by omr-r05.mx.aol.com (v83.35) with "
                  "ESMTP id RELAYIN7-0501132011; Wed, 01 May 2002 "
                  "13:20:11 -0400")
        self.mock_msg.get_decoded_header.return_value = [header]
        result = self.plugin.check_for_fake_aol_relay_in_rcvd(self.mock_msg)
        self.assertFalse(result)

    def test_check_for_fake_aol_relay_in_rcvd_not_spam2(self):
        header = ("from logs-tr.proxy.aol.com (logs-tr.proxy.aol.com "
                  "[152.163.201.132]) by rly-ip01.mx.aol.com "
                  "(8.8.8/8.8.8/AOL-5.0.0) with ESMTP id NAA08955 for "
                  "<sapient-alumni@yahoogroups.com>; Thu, 4 Apr 2002 13:11:20 "
                  "-0500 (EST)")
        self.mock_msg.get_decoded_header.return_value = [header]
        result = self.plugin.check_for_fake_aol_relay_in_rcvd(self.mock_msg)
        self.assertFalse(result)

    def test_check_for_faraway_charset_in_headers_no_locale(self):
        self.mock_locale.return_value = False
        self.global_data["ok_locales"] = ""
        self.mock_msg.get_raw_header.return_value = ["=?UTF8?B?dGVzdA==?="]
        result = self.plugin.check_for_faraway_charset_in_headers(self.mock_msg)
        self.assertFalse(result)

    def test_check_for_faraway_charset_in_headers_all_locale(self):
        self.mock_locale.return_value = False
        self.global_data["ok_locales"] = "all"
        self.mock_msg.get_raw_header.return_value = ["=?UTF8?B?dGVzdA==?="]
        result = self.plugin.check_for_faraway_charset_in_headers(self.mock_msg)
        self.assertFalse(result)

    def test_check_for_faraway_charset_in_headers_spam(self):
        self.mock_locale.return_value = False
        self.global_data["ok_locales"] = "ru"
        self.mock_msg.get_raw_header.return_value = ["=?UTF8?B?dGVzdA==?="]
        result = self.plugin.check_for_faraway_charset_in_headers(self.mock_msg)
        self.assertTrue(result)

    def test_check_for_faraway_charset_in_headers_ham(self):
        self.mock_locale.return_value = True
        self.global_data["ok_locales"] = "ru"
        self.mock_msg.get_raw_header.return_value = ["=?UTF8?B?dGVzdA==?="]
        result = self.plugin.check_for_faraway_charset_in_headers(self.mock_msg)
        self.assertFalse(result)

    def test_check_for_faraway_charset_in_headers_invalid_header(self):
        self.mock_locale.return_value = False
        self.global_data["ok_locales"] = "ru"
        patch("pad.plugins.header_eval.email.header.decode_header",
              side_effect=ValueError).start()
        self.mock_msg.get_raw_header.return_value = ["=?UTF8?B?dGVzdA==?="]
        result = self.plugin.check_for_faraway_charset_in_headers(self.mock_msg)
        self.assertFalse(result)

    def test_check_for_faraway_charset_in_headers_correct_call(self):
        self.mock_locale.return_value = False
        self.global_data["ok_locales"] = "ru ko"
        self.mock_msg.get_raw_header.return_value = ["=?UTF8?B?dGVzdA==?="]
        result = self.plugin.check_for_faraway_charset_in_headers(self.mock_msg)
        self.mock_locale.assert_called_with("utf8", ["ru", "ko"])

    def test_check_header_count_range_match(self):
        self.mock_msg.get_raw_header.return_value = ["a", "b"]
        result = self.plugin.check_header_count_range(self.mock_msg, "Test",
                                                      "2", "3")
        self.mock_msg.get_raw_header.assert_called_with("Test")
        self.assertTrue(result)

    def test_check_header_count_range_no_match(self):
        self.mock_msg.get_raw_header.return_value = ["a", "b"]
        result = self.plugin.check_header_count_range(self.mock_msg, "Test",
                                                      "3", "4")
        self.mock_msg.get_raw_header.assert_called_with("Test")
        self.assertFalse(result)

    def test_check_for_missing_to_header_has_to(self):
        self.mock_msg.get_raw_header.side_effect = [["test@example.com"]]
        result = self.plugin.check_for_missing_to_header(self.mock_msg)
        self.assertFalse(result)

    def test_check_for_missing_to_header_has_apparently_to(self):
        self.mock_msg.get_raw_header.side_effect = [[], ["test@example.com"]]
        result = self.plugin.check_for_missing_to_header(self.mock_msg)
        self.assertFalse(result)

    def test_check_for_missing_to_header_match(self):
        self.mock_msg.get_raw_header.side_effect = [[], []]
        result = self.plugin.check_for_missing_to_header(self.mock_msg)
        self.assertTrue(result)
