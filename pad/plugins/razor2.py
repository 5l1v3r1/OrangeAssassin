import pad.plugins.base
import subprocess
from threading import Timer


def kill_process(process, log):
    log.debug("Razor timed out")
    process.kill()


class Razor2Plugin(pad.plugins.base.BasePlugin):
    eval_rules = ("check_razor2",
                  "check_razor2_range")

    options = {"use_razor2": ("bool", True),
               "razor_timeout": ("int", 5),
               "razor_config": ("str", "")
               }

    def check_razor2_range(self, msg, engine, min, max, target=None):
        """
        Not implemented. Use pyzor in order to check range conditions.
        :param msg:
        :param engine:
        :param min:
        :param max:
        :param target:
        :return:
        """

    def check_razor2(self, msg, full="", target=None):
        """ Checks a mail against the distributed Razor Catalogue
        by communicating with a Razor Catalogue Server.
            If we have returncode = 1 => it's not a spam
            If we have returncode = 0 => it's a spam
        :param msg: Message to be check
        :param full: Not used
        :param target: "None" by default
        :return:True if the message is listed on Rayzor
        """
        if not self["use_razor2"]:
            return 0

        try:
            return self.get_local(msg, "razor2_result")
        except KeyError:
            pass
        self.set_local(msg, "razor2_result", 0)

        if not self["razor_config"]:
            args = ["razor-check"]
        else:
            args = ["razor-check", self["razor_config"]]
        try:
            proc = subprocess.Popen(args, stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
        except OSError as e:
            self.ctxt.log.error("Unable to run razor-check: %s", e)
            return

        my_timer = Timer(self["razor_timeout"], kill_process,
                         [proc, self.ctxt.log])
        try:
            my_timer.start()
            proc.communicate(input=str.encode(msg.raw_msg))
        finally:
            my_timer.cancel()

        if proc.returncode in (1, 0):
            self.set_local(msg, "razor2_result", proc.returncode)
        self.ctxt.log.debug(proc.returncode)
        return not proc.returncode

    def plugin_report(self, msg):
        """Report the message to razor server as spam."""
        my_timer = None
        try:
            proc = subprocess.Popen(["razor-revoke"],
                                    stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
            my_timer = Timer(self["razor_timeout"], kill_process,
                             [proc, self.ctxt.log])
            my_timer.start()
            proc.communicate(input=str.encode(msg.raw_msg))
            return proc.returncode

        except OSError:
            self.ctxt.log.warning("Unable to run razor-report")
        finally:
            if not my_timer:
                my_timer.cancel()

        return False

    def plugin_revoke(self, msg):
        """Report the message to razor server as ham."""
        my_timer = None
        try:
            proc = subprocess.Popen("razor-revoke",
                                    stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
            my_timer = Timer(self["razor_timeout"], kill_process,
                             [proc, self.ctxt.log])
            my_timer.start()
            proc.communicate(input=str.encode(msg.raw_msg))
            return proc.returncode

        except OSError:
            self.ctxt.log.warning("Unable to run razor-revoke")
        finally:
            if not my_timer:
                my_timer.cancel()

        return False
