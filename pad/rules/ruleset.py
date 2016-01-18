"""A set of rules."""

from builtins import dict
from builtins import object

from future import standard_library
standard_library.install_hooks()

import socket
import email.utils
import collections
import email.mime.text
import email.mime.base
import email.mime.multipart

import pad
import pad.errors


class RuleSet(object):
    """A set of rules used to match against a message."""
    header_start = "X-Spam-"

    def __init__(self, ctxt):
        """Create a new empty RuleSet if paranoid is set to False any
        invalid rule is ignored.
        """
        self.ctxt = ctxt
        self.report = []
        # Store modification that need to be done to the message in
        # the following format:
        # (True/False, header_name, value)
        # Where the first argument is True if the header should be
        # removed instead of added.
        self.header_mod = {
            "spam": [],
            "ham": [],
            "all": [],
        }
        self.checked = collections.OrderedDict()
        self.not_checked = dict()
        # XXX Hardcoded at the moment, should be loaded from configuration.
        self.use_bayes = True
        self.use_network = True
        self.required_score = 5

    def _interpolate(self, text, msg):
        # XXX Some plugins might define custom tags here.
        # XXX We need to check them as well.
        text = text.replace("_HOSTNAME_", socket.gethostname())
        text = text.replace("_REPORT_", self.get_matched_report(msg))
        return text

    def add_rule(self, rule):
        """Add a rule to the ruleset, execute any pre and post processing
        that's defined for the rule.
        """
        rule.preprocess(self)
        if rule.should_check():
            self.checked[rule.name] = rule
        else:
            self.not_checked[rule.name] = rule
        rule.postprocess(self)

    def add_report(self, text):
        """Add some text to the report used when the message
        is classified as Spam.
        """
        self.report.append(text)

    def get_report(self, msg):
        """Get the Spam report for this message

        :return: A string representing the report for this
        Spam message.
        """
        return self._interpolate("\n".join(self.report), msg) + "\n"

    def get_matched_report(self, msg):
        """Get a report of rules that matched this message."""
        report = "\n".join(str(self.get_rule(name))
                           for name, result in msg.rules_checked.items()
                           if result)
        return "\n%s" % report

    def clear_report_template(self):
        """Reset the report."""
        self.report = []

    def add_header_rule(self, value, remove=False):
        """Add rule to add a header for the corresponding.

        The value must be in the following format:

         [all|spam|ham] [header_name] [header_value]

        If remove is set to True, then the header is removed
        instead of added.
        """
        if remove:
            msg_status, header_name, header_value = value.split(None, 2)
        else:
            msg_status, header_name = value.split(None, 1)
            header_value = None

        msg_status = msg_status.lower()
        if msg_status not in self.header_mod:
            raise pad.errors.InvalidRule("add_header", value)

        header_name = self.header_start + header_name

        self.header_mod[msg_status].append((remove, header_name, header_value))

    def clear_headers(self):
        """Remove all rules that modify headers to the message."""
        self.header_mod = {
            "spam": [],
            "ham": [],
            "all": [],
        }

    def get_adjusted_message(self, msg, header_only=False):
        """Get message adjusted by the rules."""
        spam = msg.score >= self.required_score
        if not spam or header_only:
            newmsg = msg.msg
        else:
            newmsg = self._get_bounce_message(msg)

        self._adjust_headers(msg, newmsg, self.header_mod["all"])
        if spam:
            self._adjust_headers(msg, newmsg, self.header_mod["spam"])
        else:
            self._adjust_headers(msg, newmsg, self.header_mod["ham"])

        return newmsg.as_string()

    def _adjust_headers(self, msg, newmsg, rules):
        """Adjust the headers of this message according to
        this list of rules. The rules are tuples in the following
        format:

        True/False, header_name, header_value

        If the first argument is True then remove the header
        instead of adding it.
        """
        for remove, name, value in rules:
            if remove:
                del newmsg[name]
            else:
                newmsg.add_header(name, self._interpolate(value, msg))

    def _get_bounce_message(self, msg):
        """Create a bounce message from the original."""
        newmsg = email.mime.multipart.MIMEMultipart("mixed")
        newmsg["Received"] = (
            "from localhost by %s with SpamPad (version %s); %s" %
            (socket.gethostname(), pad.__version__,
             email.utils.formatdate(localtime=True))
        )
        # Switched around
        newmsg["From"] = msg.msg['To']
        newmsg["To"] = msg.msg['From']
        newmsg["Subject"] = msg.msg["Subject"]
        msg_date = msg.msg["Date"] or email.utils.formatdate(localtime=True)
        newmsg["Date"] = msg_date
        newmsg.preamble = "This is a multi-part message in MIME format."
        newmsg.epilogue = ""

        newmsg.attach(email.mime.text.MIMEText(self.get_report(msg)))
        original_attachment = email.mime.base.MIMEBase("message", "rfc822",
                                                   x_spam_type="original")
        original_attachment.add_header("Content-Disposition", "inline")
        original_attachment.add_header("Content-Description",
                                       "original message before SpamPAD")
        original_attachment.set_payload(msg.raw_msg)
        newmsg.attach(original_attachment)

    def get_rule(self, name, checked_only=False):
        """Gets the rule with the given name. If checked_only is set to True
        then only returns the rule if it is going to be checked.

        Raises KeyError if no rule is found.
        """
        try:
            return self.checked[name]
        except KeyError:
            if checked_only:
                raise
        return self.not_checked[name]

    def post_parsing(self):
        """Run all post processing hooks."""
        for rule_list in (self.checked, self.not_checked):
            for name, rule in list(rule_list.items()):
                try:
                    rule.postparsing(self)
                except pad.errors.InvalidRule as e:
                    self.ctxt.err(e)
                    if self.ctxt.paranoid:
                        raise
                    del rule_list[name]

    def match(self, msg):
        """Match the message against all the rules in this ruleset."""
        for name, rule in self.checked.items():
            result = rule.match(msg)
            self.ctxt.log.debug("Checked rule %s: %s", rule, result)
            msg.rules_checked[name] = result
            if result:
                msg.score += rule.score
        self.ctxt.hook_check_end(msg)
