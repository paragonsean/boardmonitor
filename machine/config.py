#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import os

import numpy as np
from enum import IntEnum, unique

from pathlib import Path
import inspect

import util.util as util
import units.units as units

@unique
class RodType(IntEnum):
    tpi_20 = 0
    pmm_2  = 1
    pmm_4  = 2

# TODO ... understand how cold-/hot- chamber machine type is used in legacy TrueTrak software
@unique
class MachineType(IntEnum):
    cold_chamber = 0
    hot_chamber  = 1


f = inspect.getfile(inspect.currentframe())
_FT3_MACHINE_MACHINES_RELPATH = 'machines'
_FT3_MACHINE_MACHINES_ABSPATH = os.path.join(Path(f).resolve().parent, _FT3_MACHINE_MACHINES_RELPATH)

_FT3_MACHINE_MACHINES_FILENAME_PREFIX = 'machine'

_FT3_MACHINE_NAME_DEFAULT = 'Machine' + ' ' + util._FT3_UTIL_NOW_FID()


_FT3_MACHINE_ROD_TYPE_DEFAULT = RodType.tpi_20


_FT3_MACHINE_HEAD_AREA_MM_SQ    = 2.00 / (units._FT3_UNITS_MM_TO_IN ** 2)
_FT3_MACHINE_ROD_AREA_MM_SQ     = 2.00 / (units._FT3_UNITS_MM_TO_IN ** 2)
_FT3_MACHINE_PLUNGER_AREA_MM_SQ = 2.00 / (units._FT3_UNITS_MM_TO_IN ** 2)


_FT3_MACHINE_QUADRATURE_DIVISOR_MIN     = np.uint8(1)
_FT3_MACHINE_QUADRATURE_DIVISOR_MAX     = np.uint8(255)
_FT3_MACHINE_QUADRATURE_DIVISOR_DEFAULT = np.uint8(1)


_FT3_MACHINE_DOWN_TIMEOUT_DEFAULT_S = 60.0
_FT3_MACHINE_CYCLE_TIME_DEFAULT_S   = 15.0
