#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import numpy as np

from distutils.version import StrictVersion
import bokeh

import param.config as cfgp


_FT3_ALARM_PARAMETER_PYTHON_MOUSEUP_POLICY_MIN_VERSION = "1.2.0"
_FT3_ALARM_PARAMETER_BOKEH_PYTHON_MOUSEUP_POLICY_AVAILABLE = StrictVersion(bokeh.__version__) >= StrictVersion(_FT3_ALARM_PARAMETER_PYTHON_MOUSEUP_POLICY_MIN_VERSION)


_FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_TEXT   = '<b>Parameter Warn/Alarm Limits and Wires</b>'
_FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_STYLE  = {"text-align":"left", "font-size":"115%", "color":"#1F77B4"}
_FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_PX_W   = 1200
_FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_PX_H   = 30
_FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_MARGIN = [15, 5, 5, 5]
_FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_NAME   = "ft3_alarm_parameter_table_header_div"


_FT3_ALARM_PARAMETER_TABLE_FIELDS = ["parameter","units","target",
                                     "limit_warn_low","wire_warn_low",
                                     "limit_warn_high","wire_warn_high",
                                     "limit_alarm_low","wire_alarm_low",
                                     "limit_alarm_high","wire_alarm_high"]
_FT3_ALARM_PARAMETER_TABLE_TITLES = ["Parameter","Units","Target",
                                     "Warning (Low)","Wire",
                                     "Warning (High)","Wire",
                                     "Alarm (Low)","Wire",
                                     "Alarm (High)","Wire"]

_FT3_ALARM_PARAMETER_TABLE_REORDERABLE = False
_FT3_ALARM_PARAMETER_TABLE_SORTABLE    = False

_FT3_ALARM_PARAMETER_TABLE_WIDTHS = [200] + [100] * (len(_FT3_ALARM_PARAMETER_TABLE_FIELDS) - 1)
_FT3_ALARM_PARAMETER_TABLE_PX_ROW = 30
_FT3_ALARM_PARAMETER_TABLE_MARGIN = [5, 5, 5, 5]

_FT3_ALARM_PARAMETER_TABLE_PX_W = np.sum(_FT3_ALARM_PARAMETER_TABLE_WIDTHS)
_FT3_ALARM_PARAMETER_TABLE_PX_H = _FT3_ALARM_PARAMETER_TABLE_PX_ROW * (cfgp._FT3_ALARM_PARAMETERS_NUM + 1)

_FT3_ALARM_PARAMETER_TABLE_HEADER_ROW = True

_FT3_ALARM_PARAMETER_TABLE_INDEX_HEADER   = None
_FT3_ALARM_PARAMETER_TABLE_INDEX_POSITION = None

_TEMPL = """
<b><div><%= (value).toFixed({0:}) %></div></b>
"""
_FCN = lambda x:_TEMPL.format(x) if x is not None else None
_FT3_ALARM_PARAMETER_TABLE_PRECISION = []
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [None]
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [None]
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [3]
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [3]
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [0]
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [3]
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [0]
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [3]
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [0]
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [3]
_FT3_ALARM_PARAMETER_TABLE_PRECISION += [0]
_FT3_ALARM_PARAMETER_TABLE_FORMAT = [_FCN(p) for p in _FT3_ALARM_PARAMETER_TABLE_PRECISION]

_FT3_ALARM_PARAMETER_TABLE_NAME = "ft3_alarm_parameter_table"


_FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_FORMAT = '<b>Selected Parameter: <span style="color:#000000"> {:s}</span></b>'
_FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_STYLE  = {"text-align":"left", "font-size":"115%", "color":"#1F77B4"}
_FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_PX_W   = 1200
_FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_PX_H   = 30
_FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_MARGIN = [15, 5, 5, 5]
_FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_NAME   = "ft3_alarm_parameter_active_param_div"


_FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_FORMAT = "{:.3f}"
_FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_VALUE  = None

_FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_PX_W   = 100
_FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_PX_H   = 30
_FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_MARGIN = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_TITLE  = "TARGET"
_FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_NAME   = "ft3_alarm_parameter_target_text_input"


_FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_PX_W   = 300
_FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_PX_H   = 30
_FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_MARGIN = [5, 5, 5, 5]

_FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_ORIENTATION = "vertical"

_FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_LABELS = ["Limits Range Sliders","Limits Text Inputs"]
_FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_ACTIVE = 0

_FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_NAME = "ft3_alarm_parameter_limits_ui_radio_group"


_FT3_ALARM_PARAMETER_LIMITS_RNG_SLIDER_RESOLUTION = 1.0E-3

_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_START = 0.0
_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_END   = 50.0
_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_STEP  = 0.1
_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_VALUE = (10.0,30.0)

if _FT3_ALARM_PARAMETER_BOKEH_PYTHON_MOUSEUP_POLICY_AVAILABLE:
    _FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_CB_POLICY  = "mouseup"
else:
    _FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_CB_POLICY  = "throttle"  
_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_CB_THROTTLE_MS = 100

_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_PX_W      = 210
_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_PX_H      = 30
_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_MARGIN    = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_BAR_COLOR = "#DE2D26"
_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_FORMAT    = "0[.]000"

_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_TITLE   = "LOW LIMITS"
_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_VISIBLE = True
_FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_NAME    = "ft3_alarm_parameter_limits_low_rng_slider"


_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_PX_W      = 210
_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_PX_H      = 30
_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_MARGIN    = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_BAR_COLOR = "#DE2D26"
_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_FORMAT    = "0[.]000"

_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_START = 50.0
_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_END   = 100.0
_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_STEP  = 0.1
_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_VALUE = (70.0,90.0)

if _FT3_ALARM_PARAMETER_BOKEH_PYTHON_MOUSEUP_POLICY_AVAILABLE:
    _FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_CB_POLICY  = "mouseup"
else:
    _FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_CB_POLICY  = "throttle"  
_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_CB_THROTTLE_MS = 100

_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_TITLE   = "HIGH LIMITS"
_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_VISIBLE = True
_FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_NAME    = "ft3_alarm_parameter_limits_high_rng_slider"


_FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_FORMAT  = "{:.3f}"
_FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_VALUE   = None

_FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_PX_W    = 100
_FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_PX_H    = 30
_FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_MARGIN  = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_TITLE   = "LOW WARN"
_FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_VISIBLE = False
_FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_NAME    = "ft3_alarm_parameter_limit_warn_low_text_input"


_FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_FORMAT  = "{:.3f}"
_FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_VALUE   = None

_FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_PX_W    = 100
_FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_PX_H    = 30
_FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_MARGIN  = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_TITLE   = "HIGH WARN"
_FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_VISIBLE = False
_FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_NAME    = "ft3_alarm_parameter_limit_warn_high_text_input"


_FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_FORMAT  = "{:.3f}"
_FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_VALUE   = None

_FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_PX_W    = 100
_FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_PX_H    = 30
_FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_MARGIN  = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_TITLE   = "LOW ALARM"
_FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_VISIBLE = False
_FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_NAME    = "ft3_alarm_parameter_limit_alarm_low_text_input"


_FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_FORMAT  = "{:.3f}"
_FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_VALUE   = None

_FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_PX_W    = 100
_FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_PX_H    = 30
_FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_MARGIN  = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_TITLE   = "HIGH ALARM"
_FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_VISIBLE = False
_FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_NAME    = "ft3_alarm_parameter_limit_alarm_high_text_input"


_FT3_ALARM_PARAMETER_WIRE_NONE    = "None"
_FT3_ALARM_PARAMETER_WIRE_NUM_MIN = 1
_FT3_ALARM_PARAMETER_WIRE_NUM_MAX = 16

_FT3_ALARM_PARAMETER_WIRE_WARN_LOW_SEL_PX_W   = 100
_FT3_ALARM_PARAMETER_WIRE_WARN_LOW_SEL_MARGIN = [25, 5, 5, 5]

_FT3_ALARM_PARAMETER_WIRE_WARN_LOW_SEL_TITLE  = "LOW WARN"
_FT3_ALARM_PARAMETER_WIRE_WARN_LOW_SEL_NAME   = "ft3_alarm_parameter_wire_warn_low_sel"


_FT3_ALARM_PARAMETER_WIRE_WARN_HIGH_SEL_PX_W   = 100
_FT3_ALARM_PARAMETER_WIRE_WARN_HIGH_SEL_MARGIN = [25, 5, 5, 5]

_FT3_ALARM_PARAMETER_WIRE_WARN_HIGH_SEL_TITLE  = "HIGH WARN"
_FT3_ALARM_PARAMETER_WIRE_WARN_HIGH_SEL_NAME   = "ft3_alarm_parameter_wire_warn_high_sel"


_FT3_ALARM_PARAMETER_WIRE_ALARM_LOW_SEL_PX_W   = 100
_FT3_ALARM_PARAMETER_WIRE_ALARM_LOW_SEL_MARGIN = [25, 5, 5, 5]

_FT3_ALARM_PARAMETER_WIRE_ALARM_LOW_SEL_TITLE = "LOW ALARM"
_FT3_ALARM_PARAMETER_WIRE_ALARM_LOW_SEL_NAME  = "ft3_alarm_parameter_wire_alarm_low_sel"


_FT3_ALARM_PARAMETER_WIRE_ALARM_HIGH_SEL_PX_W   = 100
_FT3_ALARM_PARAMETER_WIRE_ALARM_HIGH_SEL_MARGIN = [25, 5, 5, 5]

_FT3_ALARM_PARAMETER_WIRE_ALARM_HIGH_SEL_TITLE  = "HIGH ALARM"
_FT3_ALARM_PARAMETER_WIRE_ALARM_HIGH_SEL_NAME   = "ft3_alarm_parameter_wire_alarm_high_sel"


_FT3_ALARM_PARAMETER_WIRE_SEP_DIV_TEXT   = '<b>\u21A4 WIRES \u21A6</b>'
_FT3_ALARM_PARAMETER_WIRE_SEP_DIV_STYLE  = {"text-align":"center", "font-size":"115%", "color":"#AAAAAA"}
_FT3_ALARM_PARAMETER_WIRE_SEP_DIV_PX_W   = 95
_FT3_ALARM_PARAMETER_WIRE_SEP_DIV_PX_H   = 20
_FT3_ALARM_PARAMETER_WIRE_SEP_DIV_MARGIN = [40, 5, 5, 10]
_FT3_ALARM_PARAMETER_WIRE_SEP_DIV_NAME   = "ft3_alarm_parameter_wire_sep_div"


_FT3_ALARM_PARAMETER_REVERT_BUTTON_LABEL = u"\u21BA" + " " + "Revert"

_FT3_ALARM_PARAMETER_REVERT_BUTTON_TYPE_ENABLED  = "primary"
_FT3_ALARM_PARAMETER_REVERT_BUTTON_TYPE_DISABLED = "default"
_FT3_ALARM_PARAMETER_REVERT_BUTTON_DISABLED_INIT = True

_FT3_ALARM_PARAMETER_REVERT_BUTTON_PX_W   = 100
_FT3_ALARM_PARAMETER_REVERT_BUTTON_PX_H   = 30
_FT3_ALARM_PARAMETER_REVERT_BUTTON_MARGIN = [35, 5, 5, 15]

_FT3_ALARM_PARAMETER_REVERT_BUTTON_NAME   = "ft3_alarm_parameter_revert_button"


_FT3_ALARM_PARAMETER_APPLY_BUTTON_LABEL  = u"\u21F2" + " " + "Apply"

_FT3_ALARM_PARAMETER_APPLY_BUTTON_TYPE_ENABLED  = "primary"
_FT3_ALARM_PARAMETER_APPLY_BUTTON_TYPE_DISABLED = "default"
_FT3_ALARM_PARAMETER_APPLY_BUTTON_DISABLED_INIT = True

_FT3_ALARM_PARAMETER_APPLY_BUTTON_PX_W   = 100
_FT3_ALARM_PARAMETER_APPLY_BUTTON_PX_H   = 30
_FT3_ALARM_PARAMETER_APPLY_BUTTON_MARGIN = [35, 5, 5, 15]

_FT3_ALARM_PARAMETER_APPLY_BUTTON_NAME   = "ft3_alarm_parameter_apply_button"


_FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_TEXT   = '<b>Parameter Warn/Alarm Default Limits</b>'
_FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_STYLE  = {"text-align":"left", "font-size":"115%", "color":"#1F77B4"}
_FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_PX_W   = 300
_FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_PX_H   = 30
_FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_MARGIN = [15, 5, 5, 15]
_FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_NAME   = "ft3_alarm_parameter_target_ratios_header_div"


_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_TEXT   = '<b>Low Warn Limit<br>(% of Target)</b>'
_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_STYLE  = {"text-align":"left", "font-size":"100%", "color":"#333333"}
_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_PX_W   = 120
_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_PX_H   = 30
_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_MARGIN = [15, 5, 5, 35]
_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_NAME   = "ft3_alarm_parameter_warn_low_ratio_div"


_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_FORMAT = "{:.3f}"
_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_VALUE  = _FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_FORMAT.format(cfgp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO)

_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_PX_W   = 100
_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_PX_H   = 30
_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_MARGIN = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_TITLE  = ""
_FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_NAME   = "ft3_alarm_parameter_warn_low_ratio_text_input"


_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_TEXT   = '<b>High Warn Limit<br>(% of Target)</b>'
_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_STYLE  = {"text-align":"left", "font-size":"100%", "color":"#333333"}
_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_PX_W   = 120
_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_PX_H   = 30
_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_MARGIN = [15, 5, 5, 35]
_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_NAME   = "ft3_alarm_parameter_warn_high_ratio_div"


_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_FORMAT = "{:.3f}"
_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_VALUE  = _FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_FORMAT.format(cfgp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO)

_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_PX_W   = 100
_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_PX_H   = 30
_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_MARGIN = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_TITLE  = ""
_FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_NAME   = "ft3_alarm_parameter_warn_high_ratio_text_input"


_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_TEXT   = '<b>Low Alarm Limit<br>(% of Target)</b>'
_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_STYLE  = {"text-align":"left", "font-size":"100%", "color":"#333333"}
_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_PX_W   = 120
_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_PX_H   = 30
_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_MARGIN = [15, 5, 5, 35]
_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_NAME   = "ft3_alarm_parameter_alarm_low_ratio_div"


_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_FORMAT = "{:.3f}"
_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_VALUE  = _FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_FORMAT.format(cfgp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO)

_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_PX_W   = 100
_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_PX_H   = 30
_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_MARGIN = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_TITLE  = ""
_FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_NAME   = "ft3_alarm_parameter_alarm_low_ratio_text_input"


_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_TEXT   = '<b>High Alarm Limit<br>% of Target)</b>'
_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_STYLE  = {"text-align":"left", "font-size":"100%", "color":"#333333"}
_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_PX_W   = 120
_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_PX_H   = 30
_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_MARGIN = [15, 5, 5, 35]
_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_NAME   = "ft3_alarm_parameter_alarm_high_ratio_div"


_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_FORMAT = "{:.3f}"
_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_VALUE  = _FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_FORMAT.format(cfgp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO)

_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_PX_W   = 100
_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_PX_H   = 30
_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_MARGIN = [15, 5, 5, 5]

_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_TITLE  = ""
_FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_NAME   = "ft3_alarm_parameter_alarm_high_ratio_text_input"


_FT3_ALARM_PARAMETER_LAYOUT_SIZING_MODE = "scale_both"
