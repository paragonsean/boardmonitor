#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import pandas as pd

from dataclasses import dataclass
from enum import IntEnum,unique

from threading import Lock


_FT3_UTIL_NOW    = lambda: pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
_FT3_UTIL_NOW_TS = lambda: pd.Timestamp.now()

_FT3_UTIL_NOW_FID = lambda: pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

_FT3_UTIL_VERBOSE_ERROR_WITH_TS   = lambda m: print("{0:} {1:}() ERROR ".format(_FT3_UTIL_NOW(), m), end='')
_FT3_UTIL_VERBOSE_WARN_WITH_TS    = lambda m: print("{0:} {1:}() WARN ".format(_FT3_UTIL_NOW(), m), end='')
_FT3_UTIL_VERBOSE_PROFILE_WITH_TS = lambda m: print("{0:} {1:}() PROFILE ".format(_FT3_UTIL_NOW(), m), end='')
_FT3_UTIL_VERBOSE_INFO_WITH_TS    = lambda m: print("{0:} {1:}() INFO ".format(_FT3_UTIL_NOW(), m), end='')
_FT3_UTIL_VERBOSE_DEBUG_WITH_TS   = lambda m: print("{0:} {1:}() DEBUG ".format(_FT3_UTIL_NOW(), m), end='')


@unique
class VerboseLevel(IntEnum):
    off     = 0
    error   = 1
    warn    = 2
    profile = 3
    info    = 4
    debug   = 5


@dataclass
class Mutexes:
    meta  : Lock
    shot  : Lock
    events: Lock
