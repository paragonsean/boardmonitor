#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import numpy as np

import state.data as data


_FT3_ALARM_STATE_MAP = {}
_FT3_ALARM_STATE_MAP.update(none = data.AlarmState.none)
_FT3_ALARM_STATE_MAP.update(warn_low = data.AlarmState.warn_low)
_FT3_ALARM_STATE_MAP.update(warn_high = data.AlarmState.warn_high)
_FT3_ALARM_STATE_MAP.update(alarm_low = data.AlarmState.alarm_low)
_FT3_ALARM_STATE_MAP.update(alarm_high = data.AlarmState.alarm_high)


_FT3_ALARM_STATE_SHOT_VARIABLE = "shot"

_FT3_ALARM_STATE_MACHINE_LIMIT_EPS = np.finfo(dtype=float).eps

_FT3_ALARM_STATE_PRECISION         = 5
_FT3_ALARM_STATE_RESOLUTION        = 1.0E-4
_FT3_ALARM_STATE_RESOLUTION_H      = _FT3_ALARM_STATE_RESOLUTION/2.0
