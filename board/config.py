#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import ipaddress

_FT3_BOARD_NAME_PREFIX    = 'Visi-Trak FasTrak3'
_FT3_BOARD_NAME_GENERATOR = lambda n: _FT3_BOARD_NAME_PREFIX + ' ' + '{:03d}'.format(n)
_FT3_BOARD_NAME_DEFAULT   = _FT3_BOARD_NAME_GENERATOR(1)

_FT3_BOARD_NAME_LOCALHOST = 'Vis-Trak FasTrak3 Local Host'

_FT3_BOARD_IP_LOCALHOST = ipaddress.ip_address('127.0.0.1')
#_FT3_BOARD_IP_DEFAULT   = ipaddress.ip_address('192.168.254.99')
_FT3_BOARD_IP_DEFAULT   = ipaddress.ip_address('10.1.10.155')

_FT3_BOARD_SQL_USER     = "postgres"
_FT3_BOARD_SQL_PASSWORD = "admin"

_FT3_BOARD_SQL_SERVER   = "localhost"
_FT3_BOARD_SQL_DATABASE = "fastrak3"

_FT3_BOARD_SQL_META_TABLE   = "meta"
_FT3_BOARD_SQL_SHOT_TABLE   = "shot"
_FT3_BOARD_SQL_EVENTS_TABLE = "events"
_FT3_BOARD_SQL_AD_TABLE     = "ad"

_FT3_BOARD_SQL_CONN_PREFIX = "postgresql+psycopg2://"
_FT3_BOARD_SQL_FOREIGN_KEY = "shot"


_FT3_BOARD_PVU_CLOCK_MHZ       = 100000000.0/3.0 # 33.33 MHz
_FT3_BOARD_QUAD_COUNTS_PER_SEC = _FT3_BOARD_PVU_CLOCK_MHZ / 2.0
