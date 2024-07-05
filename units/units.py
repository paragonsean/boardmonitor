#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
from enum import IntEnum,unique

_FT3_UNITS_MM_TO_IN   = 1.00/25.4
_FT3_UNITS_MPA_TO_PSI = 145.03773800722

@unique
class UnitSystem(IntEnum):
    si = 0
    bg = 1

_FT3_UNITS_SYSTEM_DEFAULT = UnitSystem.si
