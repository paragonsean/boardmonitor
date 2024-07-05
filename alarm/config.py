#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import board.config as cfgb

_FT3_ALARM_SQL_USER     = cfgb._FT3_BOARD_SQL_USER
_FT3_ALARM_SQL_PASSWORD = cfgb._FT3_BOARD_SQL_PASSWORD

_FT3_ALARM_SQL_SERVER   = cfgb._FT3_BOARD_SQL_SERVER
_FT3_ALARM_SQL_DATABASE = cfgb._FT3_BOARD_SQL_DATABASE

_FT3_ALARM_SQL_ALARM_METADATA_TABLE = "alarm_metadata"

_FT3_ALARM_SQL_ALARM_NONE_TABLE     = "alarm_none"
_FT3_ALARM_SQL_WARN_LOW_TABLE       = "warn_low"
_FT3_ALARM_SQL_WARN_HIGH_TABLE      = "warn_high"
_FT3_ALARM_SQL_ALARM_LOW_TABLE      = "alarm_low"
_FT3_ALARM_SQL_ALARM_HIGH_TABLE     = "alarm_high"
_FT3_ALARM_SQL_ALARM_UNKNOWN_TABLE  = "alarm_unknown"

_FT3_ALARM_SQL_ALARM_STATE_TABLE    = "alarm_state"
_FT3_ALARM_SQL_LIMITS_WIRES_TABLE   = "limits_wires"

_FT3_ALARM_SQL_CONN_PREFIX = "postgresql+psycopg2://"


_FT3_ALARM_SQL_FOREIGN_KEY = "alarm_profile"
