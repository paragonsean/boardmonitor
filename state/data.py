#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
from enum import IntEnum,unique

@unique
class AlarmState(IntEnum):
    none       = 0
    warn_low   = 1
    warn_high  = 2
    alarm_low  = 3
    alarm_high = 4
    unknown    = 5
