"""Expose some eval rules that do checks on the headers."""

from __future__ import division
from __future__ import absolute_import

import re
import email.header

import pad.locales
import pad.plugins.base

from pad.regex import Regex


class HeaderEval(pad.plugins.base.BasePlugin):
    eval_rules = (
        "check_for_fake_aol_relay_in_rcvd",
        "check_for_faraway_charset_in_headers",
        "check_for_unique_subject_id",
        "check_illegal_chars",
        "check_for_forged_hotmail_received_headers",
        "check_for_no_hotmail_received_headers",
        "check_for_msn_groups_headers",
        "check_for_forged_eudoramail_received_headers",
        "check_for_forged_yahoo_received_headers",
        "check_for_forged_juno_received_headers",
        "check_for_matching_env_and_hdr_from",
        "sorted_recipients",
        "similar_recipients",
        "check_for_missing_to_header",
        "check_for_forged_gw05_received_headers",
        "check_for_round_the_world_received_helo",
        "check_for_round_the_world_received_revdns",
        "check_for_shifted_date",
        "subject_is_all_caps",
        "check_for_to_in_subject",
        "check_outlook_message_id",
        "check_messageid_not_usable",
        "check_header_count_range",
        "check_unresolved_template",
        "check_ratware_name_id",
        "check_ratware_envelope_from",
    )

    def check_for_fake_aol_relay_in_rcvd(self, msg, target=None):
        """Check for common AOL fake received header."""
        for recv in msg.get_decoded_header("Received"):
            if not Regex(r" rly-[a-z][a-z]\d\d\.", re.I).search(recv):
                continue
            if Regex(r"\/AOL-\d+\.\d+\.\d+\)").search(recv):
                continue
            if Regex(r"ESMTP id (?:RELAY|MAILRELAY|MAILIN)").search(recv):
                continue
            return True
        return False

    def check_for_faraway_charset_in_headers(self, msg, target=None):
        """Check if the Subject/From header is in a NOT ok locale.

        This eval rule requires the ok_locales setting configured,
        and not set to ALL.
        """
        ok_locales = self.get_global("ok_locales")
        if not ok_locales or ok_locales.lower() == "all":
            return False
        ok_locales = ok_locales.split()

        # XXX We should really be checking ALL headers here,
        # XXX not just Subject and From.
        for header_name in ("Subject", "From"):
            for header in msg.get_raw_header(header_name):
                try:
                    decoded_header = email.header.decode_header(header)
                except (ValueError, email.header.HeaderParseError):
                    continue

                for value, charset in decoded_header:
                    if not pad.locales.charset_ok_for_locales(
                            charset, ok_locales):
                        return True

        return False

    def check_for_unique_subject_id(self, msg, target=None):
        return False

    def check_illegal_chars(self, msg, target=None):
        return False

    def check_for_forged_hotmail_received_headers(self, msg, target=None):
        return False

    def check_for_no_hotmail_received_headers(self, msg, target=None):
        return False

    def check_for_msn_groups_headers(self, msg, target=None):
        return False

    def check_for_forged_eudoramail_received_headers(self, msg, target=None):
        return False

    def check_for_forged_yahoo_received_headers(self, msg, target=None):
        return False

    def check_for_forged_juno_received_headers(self, msg, target=None):
        return False

    def check_for_matching_env_and_hdr_from(self, msg, target=None):
        return False

    def sorted_recipients(self, msg, target=None):
        return False

    def similar_recipients(self, msg, target=None):
        return False

    def check_for_missing_to_header(self, msg, target=None):
        """Check if the To header is missing."""
        if msg.get_raw_header("To"):
            return False
        if msg.get_raw_header("Apparently-To"):
            return False
        return True

    def check_for_forged_gw05_received_headers(self, msg, target=None):
        return False

    def check_for_round_the_world_received_helo(self, msg, target=None):
        return False

    def check_for_round_the_world_received_revdns(self, msg, target=None):
        return False

    def check_for_shifted_date(self, msg, target=None):
        return False

    def subject_is_all_caps(self, msg, target=None):
        return False

    def check_for_to_in_subject(self, msg, target=None):
        return False

    def check_outlook_message_id(self, msg, target=None):
        return False

    def check_messageid_not_usable(self, msg, target=None):
        return False

    def check_header_count_range(self, msg, header, minr, maxr, target=None):
        """Check if the count of the header is withing the given range.
        The range is inclusive in both ranges.

        :param header: the header name
        :param minr: the minimum number of headers with the same name
        :param maxr: the minimum number of headers with the same name
        :return: True if the header count is withing the range.
        """
        return int(minr) <= len(msg.get_raw_header(header)) <= int(maxr)

    def check_unresolved_template(self, msg, target=None):
        return False

    def check_ratware_name_id(self, msg, target=None):
        return False

    def check_ratware_envelope_from(self, msg, target=None):
        return False
