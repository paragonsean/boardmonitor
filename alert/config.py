#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""

_FT3_ALERT_SMTP_SERVER_USER     = "Fast-trak3@visi-trak.com"
_FT3_ALERT_SMTP_SERVER_PASSWORD = "V!5!-tRAk3"

_FT3_ALERT_SMTP_SSL_HOST = "smtp.gmail.com"
_FT3_ALERT_SMTP_SSL_PORT = 465

_FT3_ALERT_SMTP_SSL_RETRY = 5


# SMS gateway helper lambda functions
# SMS gateways ref. https://en.wikipedia.org/wiki/SMS_gateway
_FT3_ALERT_SMS_ATT_GATEWAY        = "txt.att.net"
_FT3_ALERT_SMS_TMOBILE_GATEWAY    = "tmomail.net"
_FT3_ALERT_SMS_USCELLULAR_GATEWAY = "email.uscc.net"
_FT3_ALERT_SMS_VERIZON_GATEWAY    = "vtext.com"

_FT3_ALERT_SMS_ATT_RECIPIENT        = lambda cell: "{:}@{:}".format(str(cell), _FT3_ALERT_SMS_ATT_GATEWAY)
_FT3_ALERT_SMS_TMOBILE_RECIPIENT    = lambda cell: "{:}@{:}".format(str(cell), _FT3_ALERT_SMS_TMOBILE_GATEWAY)
_FT3_ALERT_SMS_USCELLULAR_RECIPIENT = lambda cell: "{:}@{:}".format(str(cell), _FT3_ALERT_SMS_USCELLULAR_GATEWAY)
_FT3_ALERT_SMS_VERIZON_RECIPIENT    = lambda cell: "{:}@{:}".format(str(cell), _FT3_ALERT_SMS_VERIZON_GATEWAY)


# MMS gateway helper lambda functions
# MMS gateways ref. https://en.wikipedia.org/wiki/SMS_gateway
_FT3_ALERT_MMS_ATT_GATEWAY        = "mms.att.net"
_FT3_ALERT_MMS_TMOBILE_GATEWAY    = "tmomail.net"
_FT3_ALERT_MMS_USCELLULAR_GATEWAY = "mms.uscc.net"
_FT3_ALERT_MMS_VERIZON_GATEWAY    = "vzwpix.com"

_FT3_ALERT_MMS_ATT_RECIPIENT        = lambda cell: "{:}@{:}".format(str(cell), _FT3_ALERT_MMS_ATT_GATEWAY)
_FT3_ALERT_MMS_TMOBILE_RECIPIENT    = lambda cell: "{:}@{:}".format(str(cell), _FT3_ALERT_MMS_TMOBILE_GATEWAY)
_FT3_ALERT_MMS_USCELLULAR_RECIPIENT = lambda cell: "{:}@{:}".format(str(cell), _FT3_ALERT_MMS_USCELLULAR_GATEWAY)
_FT3_ALERT_MMS_VERIZON_RECIPIENT    = lambda cell: "{:}@{:}".format(str(cell), _FT3_ALERT_MMS_VERIZON_GATEWAY)
