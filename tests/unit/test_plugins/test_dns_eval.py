"""Test DNSEval"""
import unittest
import collections

try:
    from unittest.mock import patch, Mock, MagicMock, call
except ImportError:
    from mock import patch, Mock, MagicMock, call

import ipaddress

import pad.context
import pad.plugins.dns_eval


class TestDNSEval(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.ips = [ipaddress.ip_address(u"127.0.0.1")]
        self.local_data = {}
        self.global_data = {}
        self.mock_ctxt = MagicMock()
        self.mock_ctxt.reverse_ip = pad.context.GlobalContext().reverse_ip
        self.mock_msg = MagicMock()
        self.mock_msg.sender_address = "sender@example.com"
        self.mock_msg.get_untrusted_ips.return_value = self.ips
        self.plugin = pad.plugins.dns_eval.DNSEval(self.mock_ctxt)
        self.plugin.set_local = lambda m, k, v: self.local_data.__setitem__(k, v)
        self.plugin.get_local = lambda m, k: self.local_data.__getitem__(k)
        self.plugin.set_global = self.global_data.__setitem__
        self.plugin.get_global = self.global_data.__getitem__
        self.mock_ruleset = MagicMock(checked={}, not_checked={})

    def test_finish_parsing_end(self):
        eval_rule = MagicMock()
        eval_rule.eval_rule_name = "check_rbl"
        eval_rule.eval_args = ("set id", "rbl.example.com.")
        self.mock_ruleset.checked["MY_RULE"] = eval_rule
        patch("pad.plugins.dns_eval.isinstance", return_value=True,
              create=True).start()

        self.plugin.finish_parsing_end(self.mock_ruleset)
        self.assertEqual(
            self.plugin["zones"], {"set id": "rbl.example.com."}
        )

    def test_check_rbl(self):
        """Test the check_rbl method."""
        self.plugin.check_rbl(
            self.mock_msg, "example_ser", "example.com"
        )
        self.mock_ctxt.query_dns.assert_called_with(
            "1.0.0.127.example.com", 'A')

    def test_check_rbl_subnet(self):
        """Test the check_rbl method."""
        self.plugin.check_rbl(
            self.mock_msg, "example_ser", "example.com", "127.0.0.1"
        )
        self.mock_ctxt.query_dns.assert_called_with(
            "1.0.0.127.example.com", 'A')

    def test_check_rbl_txt(self):
        """Test the check_rbl_txt method."""
        self.plugin.check_rbl_txt(
            self.mock_msg, "example_ser", "example.com", "127.0.0.2"
        )
        self.mock_ctxt.query_dns.assert_called_with(
            "1.0.0.127.example.com", 'TXT')

    def test_check_rbl_sub(self):
        """Test the check_rbl_sub method."""
        self.plugin.check_rbl(
            self.mock_msg, "example_ser", "example.com",
        )
        self.plugin.check_rbl_sub(
            self.mock_msg, "example_ser", "127.0.0.1",
        )
        self.mock_ctxt.query_dns.assert_called_with(
            "1.0.0.127.example.com", 'A')

    def test_check_dns_sender_with_a_records(self):
        """Test the check_dns_sender rule"""

        def mock_query(domain, rtype="A"):
            return ["127.0.0.1"]

        self.mock_ctxt.query_dns.side_effect = mock_query
        restult = self.plugin.check_dns_sender(self.mock_msg)
        self.assertFalse(restult)

    def test_check_dns_sender_no_mx(self):
        """Test the check_dns_sender rule"""

        def mock_query_a(domain, rtype="A"):
            return []

        def mock_query_mx(domain, rtype="MX"):
            return ["127.0.0.1"]

        self.mock_ctxt.query_dns.side_effect = mock_query_a
        self.mock_ctxt.query_dns.side_effect = mock_query_mx
        restult = self.plugin.check_dns_sender(self.mock_msg)
        self.assertFalse(restult)

    def test_check_dns_sender_invalid(self):
        """Test the check_dns_sender rule"""

        def mock_query_a(domain, rtype="A"):
            return ["127.0.0.1"]

        def mock_query_mx(domain, rtype="MX"):
            return []

        self.mock_ctxt.query_dns.side_effect = mock_query_a
        self.mock_ctxt.query_dns.side_effect = mock_query_mx

        result = self.plugin.check_dns_sender(self.mock_msg)
        self.assertTrue(result)

    def test_check_rbl_envfrom(self):
        """Test the check_rbl_from_envfrom eval rule"""
        self.plugin.check_rbl_envfrom(
            self.mock_msg, "example_set", "example.org"
        )
        self.mock_ctxt.query_dns.assert_called_with(
            "example.com.example.org", 'A')

    def test_check_rbl_from_host(self):
        """Test the check_rbl_from_domain eval rule"""
        from_host = ["test@example.net"]
        self.mock_msg.get_addr_header.return_value = from_host
        self.plugin.check_rbl_from_host(
            self.mock_msg, "example_set", "example.com"
        )
        self.mock_ctxt.query_dns.assert_called_with(
            "example.net.example.com", 'A')

    def test_check_rbl_from_domain(self):
        """Test the check_rbl_from_domain eval rule"""
        from_headers = ["test@example.org"]
        self.mock_msg.get_addr_header.return_value = from_headers
        self.plugin.check_rbl_from_domain(
            self.mock_msg, "example_set", "example.com"
        )
        self.mock_ctxt.query_dns.assert_called_with(
            "example.org.example.com", 'A')

    def test_check_rbl_from_domain_addr(self):
        """Test the check_rbl_from_domain eval rule"""
        from_headers = ["test@example.org", "teo@example.test",
                        "from@example.net", "domain.example.com"]
        self.mock_msg.get_addr_header.return_value = from_headers
        self.plugin.check_rbl_from_domain(
            self.mock_msg, "example_set", "example.com", "127.0.0.1"
        )
        self.mock_ctxt.query_dns.assert_called_with(
            "domain.example.com.example.com", 'A')

    def test_check_rbl_accreditor(self):
        """Test the check_rbl_from_domain eval rule"""
        self.mock_msg.sender_address = "sender@a--accreditor.mail.example.com"
        self.plugin.check_rbl_accreditor(
            self.mock_msg, "accredit", "example.com", "127.0.0.1", "accreditor"
        )
        self.mock_ctxt.query_dns.assert_called_with(
            "1.0.0.127.example.com", 'A')
