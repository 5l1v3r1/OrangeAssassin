#coding: utf-8
"""Functional tests for MIMEEval Plugin"""

from __future__ import absolute_import
import unittest
import tests.util

PRE_CONFIG = """
loadplugin     Mail::SpamAssassin::Plugin::MIMEEval

report _SCORE_
report _TESTS_
"""

# Define rules for plugin
CONFIG = """
body CHECK_MIME_BASE64_COUNT                     eval:check_for_mime("mime_base64_count")
body CHECK_MIME_BASE64_ENCODED_TEXT              eval:check_for_mime("mime_base64_encoded_text")
body CHECK_MIME_BODY_HTML_COUNT                  eval:check_for_mime("mime_body_html_count")
body CHECK_MIME_BODY_TEXT_COUNT                  eval:check_for_mime("mime_body_text_count")
body CHECK_MIME_FARAWAY_CHARSET                  eval:check_for_mime("mime_faraway_charset")
body CHECK_MIME_MISSING_BOUNDARY                 eval:check_for_mime("mime_missing_boundary")
body CHECK_MIME_MULTIPART_ALTERNATIVE            eval:check_for_mime("mime_multipart_alternative")
body CHECK_MIME_MULTIPART_RATIO                  eval:check_for_mime("mime_multipart_ratio")
body CHECK_MIME_QP_COUNT                         eval:check_for_mime("mime_qp_count")
body CHECK_MIME_QP_LONG_LINE                     eval:check_for_mime("mime_qp_long_line")
body CHECK_MIME_QP_RATIO                         eval:check_for_mime("mime_qp_ratio")
body CHECK_MIME_ASCII_TEXT_ILLEGAL               eval:check_for_mime("mime_ascii_text_illegal")
body CHECK_MIME_TEXT_UNICODE_RATIO               eval:check_for_mime("mime_text_unicode_ratio")

body CHECK_MIME_HTML                             eval:check_for_mime_html()
body CHECK_MIME_HTML_ONLY                        eval:check_for_mime_html_only()

body CHECK_MISSING_MIME_HEAD_BODY_SEPARATOR      eval:check_msg_parse_flags("missing_mime_head_body_separator")
body CHECK_MISSING_MIME_HEADERS                  eval:check_msg_parse_flags("missing_mime_headers")
body CHECK_TRUNCATED_HEADERS                     eval:check_msg_parse_flags("truncated_headers")
body CHECK_MIME_EPILOGUE_EXISTS                  eval:check_msg_parse_flags("mime_epilogue_exists")

body CHECK_FARAWAY_CHARSET                       eval:check_for_faraway_charset()
body CHECK_UPPERCASE                             eval:check_for_uppercase()
body CHECK_MULTIPART_RATIO                       eval:check_mime_multipart_ratio('min_ration', 'max_ratio')
body CHECK_BASE64_LENGTH                         eval:check_base64_length('min_length', 'max_length')
body CHECK_MA_NON_TEXT                           eval:check_ma_non_text()
body CHECK_ASCII_TEXT_ILLEGAL                    eval:check_for_ascii_text_illegal()
body CHECK_ABUNDANT_UNICODE_RATIO                eval:check_abundant_unicode_ratio('min_ration', 'max_ratio')
body CHECK_QP_RATION                             eval:check_qp_ratio('min_ration', 'max_ratio')
"""

MSG_HTML_ONLY = """Subject: test
Content-Type: text/html
<div dir="ltr">Test Body</div>
"""


MSG_ILLEGAL_ASCII = u"""Subject: test

Τεστ
"""

MSG_HTML_MOSTLY = """Subject: test
Content-Type: multipart/alternative; boundary=001a1148e51c20e31305439a7bc2

--001a1148e51c20e31305439a7bc2
Content-Type: text/plain; charset=UTF-8

Test Body

--001a1148e51c20e31305439a7bc2
Content-Type: text/html; charset=UTF-8

<div dir="ltr">Test Body</div>

--001a1148e51c20e31305439a7bc2--
"""

MSG_BASE64_LONG = """Content-Transfer-Encoding: base64

aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa==
"""


MSG_ABUNDANT_UNICODE = """Content-Type: text/plain
abc&#x3030;
"""


MSG_PARSE_FLAGS = """Content-Type: multipart/mixed; boundary="sb"
%s: %s
MIME-Version: 1.0
Test

--sb

Test
--sb
Content-type: text/plain; charset=us-ascii

Test

--sb--
This is the epilogue.  It is also to be ignored.""" % ("a"*257, "b"*8193)

class TestFunctionalMIMEEval(tests.util.TestBase):

    def test_check_html_only(self):
        self.setup_conf(
            config="""
            body MIME_HTML_ONLY		eval:check_for_mime_html_only()
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_HTML_ONLY)
        self.check_report(result, 1.0, ["MIME_HTML_ONLY"])

    def test_check_html_only_negative(self):
        self.setup_conf(
            config="""
            body MIME_HTML_ONLY     eval:check_for_mime_html_only()l
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_HTML_MOSTLY)
        self.check_report(result, 0, [])

    def test_check_html(self):
        self.setup_conf(
            config="""
            body MIME_HTML		eval:check_for_mime_html()
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_HTML_MOSTLY)
        self.check_report(result, 1.0, ["MIME_HTML"])

    def test_check_html_negative(self):
        self.setup_conf(
            config="""
            body MIME_HTML      eval:check_for_mime_html()
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_PARSE_FLAGS)
        self.check_report(result, 0, [])

    def test_check_html_on_html_only_mess(self):
        self.setup_conf(
            config="""
            body MIME_HTML      eval:check_for_mime_html()
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_HTML_ONLY)
        self.check_report(result, 1.0, ["MIME_HTML"])

    def test_check_mime_multipart_ratio(self):
        self.setup_conf(
            config="""
            body MIME_HTML_MOSTLY eval:check_mime_multipart_ratio('0.30','0.50')
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_HTML_MOSTLY)
        self.check_report(result, 1.0, ["MIME_HTML_MOSTLY"])

    def test_abundant_unicode_ratio(self):
        self.setup_conf(
            config="""
            body ABUNDANT_UNICODE eval:check_abundant_unicode_ratio(0.02)
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_ABUNDANT_UNICODE)
        self.check_report(result, 1.0, ["ABUNDANT_UNICODE"])

    def test_base64_length(self):
        self.setup_conf(
            config="""
            body BASE64_LENGTH eval:check_base64_length(79)
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_BASE64_LONG)
        self.check_report(result, 1.0, ["BASE64_LENGTH"])

    def test_mime_ascii_text_illegal(self):
        self.setup_conf(
            config="""
            body MIME_ILLEGAL_ASCII eval:check_for_mime("mime_ascii_text_illegal")
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_ILLEGAL_ASCII)
        self.check_report(result, 1.0, ["MIME_ILLEGAL_ASCII"])

    def test_mime_ascii_text_illegal_negative(self):
        self.setup_conf(
            config="""
            body MIME_ILLEGAL_ASCII eval:check_for_mime("mime_ascii_text_illegal")
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_PARSE_FLAGS)
        self.check_report(result, 0, [])

    def test_ascii_text_illegal(self):
        self.setup_conf(
            config="""
            body ILLEGAL_ASCII eval:check_for_ascii_text_illegal()
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_ILLEGAL_ASCII)
        self.check_report(result, 1.0, ["ILLEGAL_ASCII"])

    def test_ascii_text_illegal_negative(self):
        self.setup_conf(
            config="""
            body ILLEGAL_ASCII eval:check_for_ascii_text_illegal()
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_ABUNDANT_UNICODE)
        self.check_report(result, 0, [])

    def test_mime_body_html_count(self):
        self.setup_conf(
            config="""
            body HTML_COUNT eval:check_for_mime("mime_body_html_count")
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_HTML_MOSTLY)
        self.check_report(result, 1.0, ["HTML_COUNT"])

    def test_mime_body_text_count(self):
        self.setup_conf(
            config="""
            body TEXT_COUNT eval:check_for_mime("mime_body_text_count")
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_HTML_MOSTLY)
        self.check_report(result, 1.0, ["TEXT_COUNT"])

    def test_check_parse_flags_missing_headers_body_separator(self):
        self.setup_conf(
            config="""
            body MISSING_HB eval:check_msg_parse_flags("missing_mime_head_body_separator")
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_PARSE_FLAGS)
        self.check_report(result, 1.0, ["MISSING_HB"])

    def test_check_parse_flags_missing_headers(self):
        self.setup_conf(
            config="""
            body MISSING_H eval:check_msg_parse_flags("missing_mime_headers")
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_PARSE_FLAGS, debug=True)
        self.check_report(result, 1.0, ["MISSING_H"])

    def test_check_parse_flags_truncated_headers(self):
        self.setup_conf(
            config="""
            body TRUNCATED_H eval:check_msg_parse_flags("truncated_headers")
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_PARSE_FLAGS, debug=True)
        self.check_report(result, 1.0, ["TRUNCATED_H"])

    def test_check_parse_flags_mime_epilogue_exists(self):
        self.setup_conf(
            config="""
            body MIME_EPILOGUE_EXISTS eval:check_msg_parse_flags("mime_epilogue_exists")
            """,
            pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_PARSE_FLAGS, debug=True)
        self.check_report(result, 1.0, ["MIME_EPILOGUE_EXISTS"])


def suite():
    """Gather all the tests from this package in a test suite."""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestFunctionalMIMEEval, "test"))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')