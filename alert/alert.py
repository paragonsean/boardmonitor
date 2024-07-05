#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import sys

from dataclasses import dataclass

import smtplib 
from email.message import EmailMessage

import alert.config as cfga
import util.util as util


@dataclass
class SMTP:
    server  : smtplib.SMTP_SSL
    user    : str
    password: str
    message : EmailMessage
    ft3_info: str

@dataclass
class Recipients:
    email: list
    sms  : list


class Alert(object):
    def __init__(self, session=None, verbose=util.VerboseLevel.info):
        """Initialize FasTrak3 email/SMS alert system
        """
        _methodname = self.__init__.__name__

        self.session = session
        self.verbose = verbose

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("alert framework initialization")
            sys.stdout.flush()

        _message = EmailMessage()
        _message['From']    = cfga._FT3_ALERT_SMTP_SERVER_USER
        _message['Subject'] = "FasTrak3 Alarms"
        
        _ft3_info  = 'Board Name: {:}\n'.format(session.board.name)
        _ft3_info += 'Board IPv4: {:}\n\n'.format(session.board.ip)

        self.smtp = SMTP(server=None,
                         user=cfga._FT3_ALERT_SMTP_SERVER_USER,
                         password=cfga._FT3_ALERT_SMTP_SERVER_PASSWORD,
                         message=_message, ft3_info=_ft3_info)

        self._ssl_conn()
        self.recipients = Recipients(email=[], sms=[])

        self._ssl_except = 0

    def subscribe(self, email=None, sms=None):
        """Subscribe recipient to alerts
        """
        _methodname = self.subscribe.__name__
        
        if email is not None:
            self.recipients.email += [email]
            if self.verbose >= util.VerboseLevel.info:
                util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
                print("email {:} subscribed to alerts".format(email))
                sys.stdout.flush()
        if sms is not None:
            self.recipients.sms += [sms]
            if self.verbose >= util.VerboseLevel.info:
                util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
                print("SMS {:} subscribed to alerts".format(sms))
                sys.stdout.flush()

        self._to()

    def unsubscribe(self, email=None, sms=None):
        """Unsubscribe recipient from alerts
        """
        _methodname = self.unsubscribe.__name__

        if email is not None:
            _E = self.recipients.email
            if email in _E:
                _ = _E.pop(_E.index(email))
                if self.verbose >= util.VerboseLevel.info:
                    util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
                    print("email {:} unsubscribed from alerts".format(email))
                    sys.stdout.flush()
            else:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("email {:} is not subscribed to alerts".format(email))
                    sys.stdout.flush()

        if sms is not None:
            _S = self.recipients.sms
            if sms in _S:
                _ = _S.pop(_S.index(sms))
                if self.verbose >= util.VerboseLevel.info:
                    util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
                    print("SMS {:} unsubscribed from alerts".format(sms))
                    sys.stdout.flush()
            else:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("SMS {:} is not subscribed to alerts".format(sms))
                    sys.stdout.flush()

        # Update recipients
        self._to()

    def push(self, info=[]):
        """Push message to recipients
        """
        _methodname = self.push.__name__

        try:
            ts = util._FT3_UTIL_NOW()

            smtp = self.smtp
            smtp.server.login(user=smtp.user, password=smtp.password)

            msgdata = '\n'
            msgdata += smtp.ft3_info
            msgdata += 'Datetime  : {:}\n\n'.format(ts)

            for i in info:
                msgdata += i + '\n'

            m = smtp.message
            m.set_content(msgdata)

            if m['To'] is not None:
                smtp.server.send_message(m)
        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("alert push exception e {}".format(e))
                sys.stdout.flush()

            self._ssl_except += 1
            if self._ssl_except >= cfga._FT3_ALERT_SMTP_SSL_RETRY:
                self._ssl_conn()

    def _ssl_conn(self):
        """SMTP SSL connection
        """
        _methodname = self._ssl_conn.__name__

        try:
            _server = smtplib.SMTP_SSL(host=cfga._FT3_ALERT_SMTP_SSL_HOST,
                                       port=cfga._FT3_ALERT_SMTP_SSL_PORT)
            self._ssl_except = 0
        except Exception as e:
            _server = None
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("SMTP SSL connection exception e {}".format(e))
                sys.stdout.flush()

        self.smtp.server = _server

    def _to(self):
        """Helper to set recipients
        """
        m = self.smtp.message
        del m['To']
        m['To'] = ', '.join(self.recipients.email+self.recipients.sms)
