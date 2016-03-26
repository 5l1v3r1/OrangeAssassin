"""Tests for pad.dns_interface """

import logging
import datetime
import unittest
import ipaddress

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from builtins import str

from pad.dns_interface import DNSInterface


class TestDNSInterface(unittest.TestCase):
    """Test dns interface class"""

    def setUp(self):
        super(TestDNSInterface, self).setUp()
        logging.getLogger("pad-logger").handlers = [logging.NullHandler()]
        self.resolver = patch(
            "pad.dns_interface.dns.resolver.Resolver").start().return_value
        self.dns = DNSInterface()

    def tearDown(self):
        patch.stopall()
        super(TestDNSInterface, self).tearDown()

    def test_test_interval_seconds(self):
        self.dns.test_interval="60s"
        self.assertEqual(self.dns.test_interval,
                         datetime.timedelta(seconds=60))

    def test_test_interval_seconds_implicit(self):
        self.dns.test_interval="60"
        self.assertEqual(self.dns.test_interval,
                         datetime.timedelta(seconds=60))

    def test_test_interval_minutes(self):
        self.dns.test_interval="60m"
        self.assertEqual(self.dns.test_interval,
                         datetime.timedelta(minutes=60))

    def test_test_interval_hours(self):
        self.dns.test_interval="60h"
        self.assertEqual(self.dns.test_interval,
                         datetime.timedelta(hours=60))

    def test_test_interval_days(self):
        self.dns.test_interval="60d"
        self.assertEqual(self.dns.test_interval,
                         datetime.timedelta(days=60))

    def test_test_interval_weeks(self):
        self.dns.test_interval="60w"
        self.assertEqual(self.dns.test_interval,
                         datetime.timedelta(weeks=60))

    def test_dns_available_yes(self):
        self.dns.available = "yes"
        self.assertTrue(self.dns.available)

    def test_dns_available_no(self):
        self.dns.available = "no"
        self.assertFalse(self.dns.available)

    def test_dns_available_test(self):
        patch("pad.dns_interface.DNSInterface._query").start()
        self.dns.available = "test"
        self.assertTrue(self.dns.available)

    def test_dns_available_test_fail(self):
        patch("pad.dns_interface.DNSInterface._query", return_value=[]).start()
        self.dns.available = "test"
        self.assertFalse(self.dns.available)

    def test_dns_available_test_custom_dns(self):
        patch("pad.dns_interface.DNSInterface._query", return_value=[]).start()
        self.dns.available = "test: example.com 1.example.com 2.example.com"
        self.assertFalse(self.dns.available)

    def test_is_query_restricted_empty(self):
        """Test a domain that when no restrictions apply"""
        self.assertFalse(
            self.dns.is_query_restricted("1.2.3.4.5.example.com"))

    def test_is_query_restricted_true(self):
        """Test an allowed domain."""
        self.dns.query_restrictions = {"1.2.3.4.5.example.com": True}

        self.assertTrue(
            self.dns.is_query_restricted("1.2.3.4.5.example.com"))

    def test_is_query_restricted_false(self):
        """Test a restricted domain"""
        self.dns.query_restrictions = {"1.2.3.4.5.example.com": False}
        self.assertFalse(
            self.dns.is_query_restricted("1.2.3.4.5.example.com"))

    def test_qname_parent_is_restricted_true(self):
        """Test a domain with an allowed parent"""
        self.dns.query_restrictions = {"4.5.example.com": True}
        self.assertTrue(
            self.dns.is_query_restricted("1.2.3.4.5.example.com"))

    def test_qname_parent_is_restricted_false(self):
        """Test a domain with a restricted parent"""
        self.dns.query_restrictions = {"4.5.example.com": False}
        self.assertFalse(
            self.dns.is_query_restricted("1.2.3.4.5.example.com"))

    def test_is_query_restricted_false_with_parent_true(self):
        """Test an allowed domain with a restricted parent."""
        self.dns.query_restrictions = {"2.3.4.5.example.com": True,
                                       "4.5.example.com": False}
        self.assertTrue(
            self.dns.is_query_restricted("1.2.3.4.5.example.com"))

    def test_is_query_restricted_true_with_parent_false(self):
        """Test a restricted domain with an allowed parent."""
        self.dns.query_restrictions = {"2.3.4.5.example.com": False,
                                       "4.5.example.com": True}
        self.assertFalse(
            self.dns.is_query_restricted("1.2.3.4.5.example.com"))

    def test_query(self):
        self.dns.query("example.com", "A")

    def test_query_restricted(self):
        self.dns.query_restrictions = {"example.com": True}
        result = self.dns.query("example.com", "A")
        self.assertEqual(result, [])

    def test_query_error(self):
        pass

    def test_reverse_ip(self):
        result = self.dns.reverse_ip(ipaddress.ip_address(str("127.0.0.1")))
        self.assertEqual("1.0.0.127", result)
