"""Tests the AWL Plugin"""
from __future__ import absolute_import

import os
import getpass
import unittest
import tests.util

try:
    import pymysql
    use_sqlalchemy = False
    CONF_MYSQL = "user_awl_dsn DBI:mysql:OrangeAssassin:127.0.0.1"
except:
    import sqlite3
    use_sqlalchemy = True
    CONF_MYSQL = "user_awl_dsn sqlite:///OrangeAssassin.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS `awl` (
  `username` varchar(255) NOT NULL DEFAULT '',
  `email` varchar(200) NOT NULL DEFAULT '',
  `ip` varchar(40) NOT NULL DEFAULT '',
  `count` int(11) NOT NULL DEFAULT '0',
  `totscore` float NOT NULL DEFAULT '0',
  `signedby` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`username`,`email`,`signedby`,`ip`)
);
"""

AWL_URI_RULESET = """
uri_detail TEST %s
describe TEST Suspicious URL received
score TEST 1.000
header AWL eval:check_from_in_auto_whitelist()
"""

PRE_CONFIG = """
loadplugin     Mail::SpamAssassin::Plugin::URIDetail
loadplugin     Mail::SpamAssassin::Plugin::AWL

report _SCORE_
report _TESTS_
"""

MSG_MULTIPART = """From: Tester That Tests The Test <test@example.com>
Received: by 8.8.8.8
Subject: test
Content-Type: multipart/alternative; boundary=001a11c39d507b0142052155ffb1

--001a11c39d507b0142052155ffb1
Content-Type: text/plain; charset=UTF-8

Hello,

dwdwdwd

--001a11c39d507b0142052155ffb1
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: quoted-printable

<html>https://www.example.com</html>

--001a11c39d507b0142052155ffb1--
"""


class TestFunctionalAWLPlugin(tests.util.TestBase):

    def setUp(self):
        super(TestFunctionalAWLPlugin, self).setUp()

        if use_sqlalchemy:
            self.db = sqlite3.connect("OrangeAssassin.db")
        else:
            self.db = pymysql.connect(host='localhost', port=3306,
                                      user='root',
                                      db='OrangeAssassin')
        self.c = self.db.cursor()
        self.c.execute(SCHEMA)
        self.db.commit()

    def tearDown(self):
        super(TestFunctionalAWLPlugin, self).tearDown()
        self.c.execute("DROP TABLE IF EXISTS `awl`;")
        self.db.commit()
        self.c.close()
        self.db.close()

    def test_check_awl_basic_rule(self):
        self.setup_conf(config=AWL_URI_RULESET %
                        "raw =~ /www(w|ww|www|www\.)?/" + CONF_MYSQL,
                        pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_MULTIPART)
        self.check_report(result, 1.0, ["TEST"])

    def test_check_existing_msg_rule(self):
        self.c.execute("INSERT INTO awl "
                       "(username, email, ip, count, totscore, signedby) "
                       "VALUES "
                       "('%s', 'test@example.com', 'none', 3, 10, '');" %
                       (getpass.getuser()))
        self.db.commit()
        self.setup_conf(config=AWL_URI_RULESET %
                        "raw =~ /www(w|ww|www|www\.)?/" + CONF_MYSQL,
                        pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_MULTIPART)
        self.check_report(result, 2.2, ["TEST"])

    def test_check_ip_rule(self):
        self.c.execute("INSERT INTO awl "
                       "(username, email, ip, count, totscore, signedby) "
                       "VALUES "
                       "('%s', 'test@example.com', '8.8.8.8', 3, 10, '');" %
                       (getpass.getuser()))
        self.db.commit()
        self.setup_conf(config=AWL_URI_RULESET %
                        "raw =~ /www(w|ww|www|www\.)?/" + CONF_MYSQL,
                        pre_config=PRE_CONFIG)
        result = self.check_pad(MSG_MULTIPART)
        self.check_report(result, 1.0, ["TEST"])
