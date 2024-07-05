#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import numpy as np
import units.units as units

_FT3_ALARM_PARAMETERS_NUM = 10

# Alarm parameter names
_FT3_ALARM_PARAMETER_NAMES = []
_FT3_ALARM_PARAMETER_NAMES += ["fill_time"]
_FT3_ALARM_PARAMETER_NAMES += ["ss_vel_avg"]
_FT3_ALARM_PARAMETER_NAMES += ["fs_vel_avg"]
_FT3_ALARM_PARAMETER_NAMES += ["biscuit_size"]
_FT3_ALARM_PARAMETER_NAMES += ["intens_squeeze_dist"]
_FT3_ALARM_PARAMETER_NAMES += ["intens_rise_time"]
_FT3_ALARM_PARAMETER_NAMES += ["csfs"]
_FT3_ALARM_PARAMETER_NAMES += ["cycle_time"]
_FT3_ALARM_PARAMETER_NAMES += ["peak_intens_press"]
_FT3_ALARM_PARAMETER_NAMES += ["ss_var_rate"]

# Alarm parameter descriptions
_FT3_ALARM_PARAMETER_DESCR = []
_FT3_ALARM_PARAMETER_DESCR += ["Fill Time"]
_FT3_ALARM_PARAMETER_DESCR += ["Average Slow Shot Velocity"]
_FT3_ALARM_PARAMETER_DESCR += ["Average Fast Shot Velocity"]
_FT3_ALARM_PARAMETER_DESCR += ["Biscuit Size"]
_FT3_ALARM_PARAMETER_DESCR += ["Intensification Squeeze Distance"]
_FT3_ALARM_PARAMETER_DESCR += ["Intensification Rise Time"]
_FT3_ALARM_PARAMETER_DESCR += ["Calculated Start of Fast Shot"]
_FT3_ALARM_PARAMETER_DESCR += ["Cycle Time"]
_FT3_ALARM_PARAMETER_DESCR += ["Peak Intensification Pressure"]
_FT3_ALARM_PARAMETER_DESCR += ["Slow Shot Variation Rate"]

# Alarm parameter units (SI,BG)
_FT3_ALARM_PARAMETER_UNITS = []
_FT3_ALARM_PARAMETER_UNITS += [("ms","ms")]
_FT3_ALARM_PARAMETER_UNITS += [("mm/s","in/s")]
_FT3_ALARM_PARAMETER_UNITS += [("mm/s","in/s")]
_FT3_ALARM_PARAMETER_UNITS += [("mm","in")]
_FT3_ALARM_PARAMETER_UNITS += [("mm","in")]
_FT3_ALARM_PARAMETER_UNITS += [("ms","ms")]
_FT3_ALARM_PARAMETER_UNITS += [("mm","in")]
_FT3_ALARM_PARAMETER_UNITS += [("s","s")]
_FT3_ALARM_PARAMETER_UNITS += [("MPa","psi")]
_FT3_ALARM_PARAMETER_UNITS += [("   ","   ")]
_FT3_ALARM_PARAMETER_UNITS = np.array(_FT3_ALARM_PARAMETER_UNITS)

# Alarm parameter unit conversions
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS = []
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS += [(1.00,1.00)]
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS += [(1.00,units._FT3_UNITS_MM_TO_IN)]
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS += [(1.00,units._FT3_UNITS_MM_TO_IN)]
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS += [(1.00,units._FT3_UNITS_MM_TO_IN)]
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS += [(1.00,units._FT3_UNITS_MM_TO_IN)]
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS += [(1.00,1.00)]
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS += [(1.00,units._FT3_UNITS_MM_TO_IN)]
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS += [(1.00,1.00)]
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS += [(1.00,units._FT3_UNITS_MPA_TO_PSI)]
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS += [(1.00,1.00)]
_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS = np.array(_FT3_ALARM_PARAMETER_UNIT_CONVERSIONS)

# Alarm parameter default target (in-range) value, SI units
_FT3_ALARM_PARAMETER_TARGET_VALUES = []
_FT3_ALARM_PARAMETER_TARGET_VALUES += [  25.00]
_FT3_ALARM_PARAMETER_TARGET_VALUES += [ 400.00]
_FT3_ALARM_PARAMETER_TARGET_VALUES += [4500.00]
_FT3_ALARM_PARAMETER_TARGET_VALUES += [  28.00]
_FT3_ALARM_PARAMETER_TARGET_VALUES += [  28.00]
_FT3_ALARM_PARAMETER_TARGET_VALUES += [ 225.00]
_FT3_ALARM_PARAMETER_TARGET_VALUES += [ 444.50]
_FT3_ALARM_PARAMETER_TARGET_VALUES += [  15.00]
_FT3_ALARM_PARAMETER_TARGET_VALUES += [  27.58]
_FT3_ALARM_PARAMETER_TARGET_VALUES += [   5.00]
_FT3_ALARM_PARAMETER_TARGET_VALUES = np.array(_FT3_ALARM_PARAMETER_TARGET_VALUES)

# Alarm parameter min/max value, SI units
_FT3_ALARM_PARAMETER_MINMAX_VALUES = []
_FT3_ALARM_PARAMETER_MINMAX_VALUES += [(0.00,  500.00)]
_FT3_ALARM_PARAMETER_MINMAX_VALUES += [(0.00, 7620.00)]
_FT3_ALARM_PARAMETER_MINMAX_VALUES += [(0.00,12700.00)]
_FT3_ALARM_PARAMETER_MINMAX_VALUES += [(0.00,  304.80)]
_FT3_ALARM_PARAMETER_MINMAX_VALUES += [(0.00,  304.80)]
_FT3_ALARM_PARAMETER_MINMAX_VALUES += [(0.00, 1000.00)]
_FT3_ALARM_PARAMETER_MINMAX_VALUES += [(0.00, 1524.00)]
_FT3_ALARM_PARAMETER_MINMAX_VALUES += [(0.00,  600.00)]
_FT3_ALARM_PARAMETER_MINMAX_VALUES += [(0.00,  689.48)]
_FT3_ALARM_PARAMETER_MINMAX_VALUES += [(0.00,  100.00)]
_FT3_ALARM_PARAMETER_MINMAX_VALUES = np.array(_FT3_ALARM_PARAMETER_MINMAX_VALUES)

# Alarm parameter default warning (low,high) limits
_FT3_ALARM_PARAMETER_WARN_FRACTION = _K = 0.10
_FT3_ALARM_PARAMETER_WARN_LOW_RATIO = _KL = (1.0 - _K)
_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO = _KH = (1.0 + _K)
_w = [(v*_KL, v*_KH) for v in _FT3_ALARM_PARAMETER_TARGET_VALUES]
_FT3_ALARM_PARAMETER_WARN_LIMITS = np.array(_w)

# Alarm parameter default alarm (low,high) limits
_FT3_ALARM_PARAMETER_ALARM_FRACTION = _K = 0.20
_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO = _KL = (1.0 - _K)
_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO = _KH = (1.0 + _K)
_a = [(v*_KL, v*_KH) for v in _FT3_ALARM_PARAMETER_TARGET_VALUES]
_FT3_ALARM_PARAMETER_ALARM_LIMITS = np.array(_a)

# Alarm parameter (low,high) warning digital I/O wire assignment
_FT3_ALARM_PARAMETER_WARN_WIRE = np.array([(0,0)] * _FT3_ALARM_PARAMETERS_NUM)

# Alarm parameter (low,high) alarm digital I/O wire assignment
_FT3_ALARM_PARAMETER_ALARM_WIRE = np.array([(0,0)] * _FT3_ALARM_PARAMETERS_NUM)
