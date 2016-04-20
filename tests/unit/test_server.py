"""Unittest for scripts.padd"""

import signal
import logging
import unittest
import threading

try:
    from unittest.mock import patch, Mock, call, MagicMock
except ImportError:
    from mock import patch, Mock, call, MagicMock


import pad.server


class TestServer(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        logging.getLogger("pad-logger").handlers = [logging.NullHandler()]
        self.mock_socket = patch("pad.server.socket", create=True).start()
        self.mock_sock = patch("pad.server.Server.socket", create=True).start()
        patch("pad.server.pad.config.get_config_files").start()
        patch("pad.server.socketserver").start()
        self.mock_bind = patch("pad.server.Server.server_bind").start()
        self.mock_active = patch("pad.server.Server.server_activate").start()
        self.mock_signal = patch("pad.server.signal.signal",
                                 create=True).start()
        self.mock_thread = patch("pad.server.threading.Thread").start()
        self.mock_parser = patch("pad.server."
                                 "pad.rules.parser.PADParser").start()
        self.mock_rules = patch("pad.server."
                                "pad.rules.parser.parse_pad_rules").start()
        self.mainset = self.mock_rules.return_value.get_ruleset.return_value
        self.conf = {
            "allow_user_rules": False
        }
        self.mainset.conf = self.conf

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        patch.stopall()

    def test_init_ruleset(self):
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        self.assertEqual(server._parser_results,
                         self.mock_rules.return_value.results)
        self.assertEqual(server._ruleset, self.mainset)

    def test_handler(self):
        mock_check = MagicMock()
        mock_rfile = MagicMock()
        mock_rfile.readline.return_value = b"CHECK SPAMC/1.2"
        mock_request = MagicMock()
        mock_request.makefile.return_value = mock_rfile
        mock_server = MagicMock()

        patch("pad.server.COMMANDS", {"CHECK": mock_check}, create=True).start()
        pad.server.RequestHandler(mock_request, ("127.0.0.1", 47563),
                                  mock_server)
        mock_check.assert_called_with(mock_rfile, mock_rfile,
                                      mock_server)

    def test_server(self):
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        self.mock_bind.assert_called_with()
        self.mock_active.assert_called_with()

    def test_server_signals(self):
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        calls = [
            call(signal.SIGUSR1, server.reload_handler),
            call(signal.SIGTERM, server.shutdown_handler)
        ]
        self.mock_signal.assert_has_calls(calls)

    def test_shutdown(self):
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        server.shutdown_handler()
        self.mock_thread.assert_called_with(target=server.shutdown)

    def test_reload(self):
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        server.reload_handler()
        self.mock_thread.assert_called_with(target=server.load_config)

    def test_user_ruleset_none(self):
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        result = server.get_user_ruleset(user=None)
        self.assertEqual(result, self.mainset)

    def test_user_ruleset_user_not_allowed(self):
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        result = server.get_user_ruleset(user="alex")
        self.assertEqual(result, self.mainset)

    def test_user_ruleset_user_no_pref(self):
        self.conf["allow_user_rules"] = True
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        with patch("pad.server.os.path.exists", return_value=False):
            result = server.get_user_ruleset(user="alex")
        self.assertEqual(result, self.mainset)

    def test_user_ruleset_user(self):
        self.conf["allow_user_rules"] = True
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        with patch("pad.server.os.path.exists", return_value=True):
            result = server.get_user_ruleset(user="alex")
        parser = self.mock_parser.return_value
        self.assertEqual(result, parser.get_ruleset.return_value)

    def test_user_ruleset_user_file_parsed(self):
        self.conf["allow_user_rules"] = True
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        with patch("pad.server.os.path.exists", return_value=True):
            result = server.get_user_ruleset(user="alex")
        parser = self.mock_parser.return_value
        parser.parse_file.assert_called_with(
            "/home/alex/.spamassassin/user_prefs"
        )

    def test_user_ruleset_user_cached(self):
        self.conf["allow_user_rules"] = True
        server = pad.server.Server(("0.0.0.0", 783), "/dev/null",
                                   "/etc/spamassassin/")
        cached_result = Mock()
        server._user_rulesets["alex"] = cached_result

        result = server.get_user_ruleset(user="alex")
        self.assertEqual(result, cached_result)

class TestPreForkServer(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        logging.getLogger("pad-logger").handlers = [logging.NullHandler()]
        self.mock_socket = patch("pad.server.socket", create=True).start()
        self.mock_sock = patch("pad.server.Server.socket", create=True).start()
        self.mock_forever = patch("pad.server.Server.serve_forever").start()
        self.mock_kill = patch("pad.server.os.kill", create=True).start()
        patch("pad.server.pad.config.get_config_files").start()
        patch("pad.server.socketserver").start()
        patch("pad.server._eintr_retry").start()
        self.mock_bind = patch("pad.server.Server.server_bind").start()
        self.mock_active = patch("pad.server.Server.server_activate").start()
        self.mock_signal = patch("pad.server.signal.signal",
                                 create=True).start()
        self.mock_thread = patch("pad.server.threading.Thread").start()
        self.mock_fork = patch("pad.server.os.fork", create=True).start()


    def tearDown(self):
        unittest.TestCase.tearDown(self)
        patch.stopall()

    def test_server_forever(self):
        server = pad.server.PreForkServer(("0.0.0.0", 783), "/dev/null",
                                          "/etc/spamassassin/")
        server.serve_forever()
        self.assertEqual(len(server.pids), 6)

    def test_master_shutdown(self):
        shutdown = patch("pad.server.Server.shutdown").start()
        server = pad.server.PreForkServer(("0.0.0.0", 783), "/dev/null",
                                          "/etc/spamassassin/", prefork=2)
        server.pids = [100, 101]
        server.shutdown()
        calls = [
            call(100, signal.SIGTERM),
            call(101, signal.SIGTERM),
        ]
        self.mock_kill.assert_has_calls(calls)

    def test_worker_shutdown(self):
        shutdown = patch("pad.server.Server.shutdown").start()
        server = pad.server.PreForkServer(("0.0.0.0", 783), "/dev/null",
                                          "/etc/spamassassin/", prefork=2)
        server.pids = None
        server.shutdown()
        shutdown.assert_called_with(server)

    def test_master_reload(self):
        load_config = patch("pad.server.Server.load_config").start()
        server = pad.server.PreForkServer(("0.0.0.0", 783), "/dev/null",
                                          "/etc/spamassassin/", prefork=2)
        server.pids = [100, 101]
        server.load_config()
        calls = [
            call(100, signal.SIGUSR1),
            call(101, signal.SIGUSR1),
        ]
        self.mock_kill.assert_has_calls(calls)

    def test_worker_reload(self):
        load_config = patch("pad.server.Server.load_config").start()
        server = pad.server.PreForkServer(("0.0.0.0", 783), "/dev/null",
                                          "/etc/spamassassin/", prefork=2)
        server.pids = None
        server.load_config()
        load_config.assert_called_with(server)

def suite():
    """Gather all the tests from this package in a test suite."""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestServer, "test"))
    test_suite.addTest(unittest.makeSuite(TestPreForkServer, "test"))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
