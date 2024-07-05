#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import numpy as np

import param.config as cfgp


_FT3_ALARM_STATE_STATUS_PLOT_ROWS  = cfgp._FT3_ALARM_PARAMETERS_NUM
_FT3_ALARM_STATE_STATUS_PLOT_COLS  = 50

_FT3_ALARM_STATE_STATUS_PLOT_NUMEL = _FT3_ALARM_STATE_STATUS_PLOT_ROWS * _FT3_ALARM_STATE_STATUS_PLOT_COLS

_FT3_ALARM_STATE_STATUS_PLOT_PX_W  = 1125
_FT3_ALARM_STATE_STATUS_PLOT_PX_H  = (_FT3_ALARM_STATE_STATUS_PLOT_PX_W * (_FT3_ALARM_STATE_STATUS_PLOT_ROWS + 1)) // (_FT3_ALARM_STATE_STATUS_PLOT_COLS + 2)
_FT3_ALARM_STATE_STATUS_PLOT_PX_BORDER = 1

_L  = -1.00
_H  = _FT3_ALARM_STATE_STATUS_PLOT_COLS
_DX = 0.60
_FT3_ALARM_STATE_STATUS_PLOT_XRANGE = (_L-_DX,_H+_DX)

_L  = -1.00
_H  = _FT3_ALARM_STATE_STATUS_PLOT_ROWS - 1.00
_DY = 0.60
_FT3_ALARM_STATE_STATUS_PLOT_YRANGE = (_H+_DY,_L-_DY)

_FT3_ALARM_STATE_STATUS_PLOT_VISIBLE_XAXIS = False
_FT3_ALARM_STATE_STATUS_PLOT_VISIBLE_XGRID = True
_FT3_ALARM_STATE_STATUS_PLOT_TICKER_XGRID  = np.arange(0,_FT3_ALARM_STATE_STATUS_PLOT_COLS,1)

_FT3_ALARM_STATE_STATUS_PLOT_VISIBLE_YAXIS = False
_FT3_ALARM_STATE_STATUS_PLOT_VISIBLE_YGRID = True
_FT3_ALARM_STATE_STATUS_PLOT_TICKER_YGRID  = np.arange(0,_FT3_ALARM_STATE_STATUS_PLOT_ROWS,1)

_FT3_ALARM_STATE_STATUS_PLOT_LOC_TOOLS = None

_FT3_ALARM_STATE_STATUS_PLOT_BACKGROUND     = "#FAFAFA"
_FT3_ALARM_STATE_STATUS_PLOT_OUTPUT_BACKEND = "webgl"

_FT3_ALARM_STATE_STATUS_PLOT_NAME = "ft3_alarm_state_status_plot"


_FT3_ALARM_STATE_STATUS_RECT_W = 0.80
_FT3_ALARM_STATE_STATUS_RECT_H = 0.80

_FT3_ALARM_STATE_STATUS_RECT_COLOR_EMPTY = _FT3_ALARM_STATE_STATUS_PLOT_BACKGROUND

_FT3_ALARM_STATE_STATUS_RECT_COLOR_NONE  = "#31A354" # Brewer 3-class Greens palette
_FT3_ALARM_STATE_STATUS_RECT_COLOR_WARN  = "#FD8D3C" # Brewer 5-class YlOrRd palette
_FT3_ALARM_STATE_STATUS_RECT_COLOR_ALARM = "#DE2D26" # Brewer 3-class Reds palette
_FT3_ALARM_STATE_STATUS_RECT_COLOR_UNK   = "#BDBDBD" # Brewer 3-class Greys palette

_FT3_ALARM_STATE_STATUS_RECT_COLOR_MAP   = (_FT3_ALARM_STATE_STATUS_RECT_COLOR_NONE,
                                            _FT3_ALARM_STATE_STATUS_RECT_COLOR_WARN,
                                            _FT3_ALARM_STATE_STATUS_RECT_COLOR_WARN,
                                            _FT3_ALARM_STATE_STATUS_RECT_COLOR_ALARM,
                                            _FT3_ALARM_STATE_STATUS_RECT_COLOR_ALARM,
                                            _FT3_ALARM_STATE_STATUS_RECT_COLOR_UNK)

_FT3_ALARM_STATE_STATUS_RECT_ALPHA = 0.70

_FT3_ALARM_STATE_STATUS_RECT_NAME = "ft3_alarm_state_status_rect"


_FT3_ALARM_STATE_ACTIVE_RECT_W = _FT3_ALARM_STATE_STATUS_RECT_W + 0.10
_FT3_ALARM_STATE_ACTIVE_RECT_H = cfgp._FT3_ALARM_PARAMETERS_NUM

_FT3_ALARM_STATE_ACTIVE_RECT_COLOR = None

_FT3_ALARM_STATE_ACTIVE_RECT_LINE_COLOR = "#000000"
_FT3_ALARM_STATE_ACTIVE_RECT_LINE_WIDTH = 1.50

_FT3_ALARM_STATE_ACTIVE_RECT_ALPHA = 1.00

_FT3_ALARM_STATE_ACTIVE_RECT_NAME = "ft3_alarm_state_active_rect"


_FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_X = -1.00
_FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_Y = (_FT3_ALARM_STATE_STATUS_PLOT_ROWS - 1.00) / 2.00

_FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_SIZE  = 18
_FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_ANGLE = np.pi/2.0

_FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_FILL_COLOR = "#1F77B4"
_FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_FILL_ALPHA = 1.00

_FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_LINE_COLOR = "#1F77B4"
_FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_LINE_WIDTH = 1.00

_FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_NAME = "ft3_alarm_state_prev_shot_triangle"


_FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_X = _FT3_ALARM_STATE_STATUS_PLOT_COLS
_FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_Y = (_FT3_ALARM_STATE_STATUS_PLOT_ROWS - 1.00) / 2.00

_FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_SIZE  = 18
_FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_ANGLE = -np.pi/2.0

_FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_FILL_COLOR = "#1F77B4"
_FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_FILL_ALPHA = 1.00

_FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_LINE_COLOR = "#1F77B4"
_FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_LINE_WIDTH = 1.00

_FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_NAME = "ft3_alarm_state_next_shot_triangle"


_FT3_ALARM_STATE_SHOT_INFO_LABELSET_TEXT_COLOR = "#1F77B4"
_FT3_ALARM_STATE_SHOT_INFO_LABELSET_FONT_SIZE  = "8pt"
_FT3_ALARM_STATE_SHOT_INFO_LABELSET_FONT_STYLE = "bold"

_FT3_ALARM_STATE_SHOT_INFO_LABELSET_LEVEL      = "glyph"
_FT3_ALARM_STATE_SHOT_INFO_LABELSET_ALIGN      = "center"
_FT3_ALARM_STATE_SHOT_INFO_LABELSET_BASELINE   = "middle"

_FT3_ALARM_STATE_SHOT_INFO_LABELSET_OFFSET_X   = 0.00
_FT3_ALARM_STATE_SHOT_INFO_LABELSET_OFFSET_Y   = 0.00

_FT3_ALARM_STATE_SHOT_INFO_LABELSET_FORMAT     = "{0:04d}"

_FT3_ALARM_STATE_SHOT_INFO_LABELSET_NAME = "ft3_alarm_shot_info_labelset"


_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_PX_W      = 400
_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_PX_H      = _FT3_ALARM_STATE_STATUS_PLOT_PX_H
_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_PX_BORDER = _FT3_ALARM_STATE_STATUS_PLOT_PX_BORDER

_L  = 0.00
_H  = 4.00
_DX = 0.10
_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_XRANGE = (_L-_DX,_H+_DX)

_L  = -1.00
_H  = _FT3_ALARM_STATE_STATUS_PLOT_ROWS - 1.00
_DY = 0.60
_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_YRANGE = (_H+_DY,_L-_DY)

_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_VISIBLE_XAXIS = False
_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_VISIBLE_XGRID = False
_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_TICKER_XGRID  = None

_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_VISIBLE_YAXIS = False
_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_VISIBLE_YGRID = True
_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_TICKER_YGRID  = np.arange(0,_FT3_ALARM_STATE_STATUS_PLOT_ROWS,1)

_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_LOC_TOOLS = None

_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_BACKGROUND     = "#FAFAFA"
_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_OUTPUT_BACKEND = "webgl"

_FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_NAME = "ft3_alarm_state_active_shot_plot"


_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_ORIGIN_X = 4.00

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_SIZE_PTS = 8.00

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_COLOR = "#1F77B4"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_ALPHA = 0.50

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_NAME = "ft3_alarm_state_active_shot_param_metadata_circle"


_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_HOVER_ATTACHMENT = "below"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_HOVER_MODE       = "hline"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_HOVER_NAME       = "ft3_alarm_state_active_shot_param_metadata_hover"


_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_ORIGIN_X   = 0.00
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_ORIGIN_Y   = -1.00

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_TEXT       = "Parameter"

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_TEXT_COLOR = "#1F77B4"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_FONT_SIZE  = "12pt"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_FONT_STYLE = "bold"

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_LEVEL      = "glyph"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_ALIGN      = "left"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_BASELINE   = "middle"

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_OFFSET_X   = 0.00
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_OFFSET_Y   = 0.00

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_NAME = "ft3_alarm_state_active_shot_param_header_label"


_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_ORIGIN_X = 0.00

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_TEXT_COLOR = "#000000"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_FONT_SIZE  = "10pt"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_FONT_STYLE = "normal"

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_LEVEL    = "glyph"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_ALIGN    = "left"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_BASELINE = "middle"

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_OFFSET_X = 0.00
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_OFFSET_Y = 0.00

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_NAME = "ft3_alarm_state_active_shot_param_name_labelset"


_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_ORIGIN_X = 3.33

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_FONT_SIZE  = "10pt"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_FONT_STYLE = "normal"

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_LEVEL    = "glyph"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_ALIGN    = "right"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_BASELINE = "middle"

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_OFFSET_X = 0.00
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_OFFSET_Y = 0.00

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_FORMAT = "{0:+.2f}"

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_NAME = "ft3_alarm_state_active_shot_param_data_labelset"


_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_ORIGIN_X = 3.50

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_TEXT_COLOR = "#000000"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_FONT_SIZE  = "10pt"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_FONT_STYLE = "normal"

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_LEVEL    = "glyph"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_ALIGN    = "left"
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_BASELINE = "middle"

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_OFFSET_X = 0.00
_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_OFFSET_Y = 0.00

_FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_NAME = "ft3_alarm_state_active_shot_param_units_labelset"

_FT3_ALARM_STATE_LAYOUT_SIZING_MODE = "scale_both"