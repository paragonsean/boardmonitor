#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 alarm parameter limits/wires management
"""
import sys

import copy

import numpy as np
import pandas as pd

from dataclasses import dataclass
from enum import IntEnum,unique

from bokeh.models import ColumnDataSource
from bokeh.models import DataTable, TableColumn, HTMLTemplateFormatter

from bokeh.models import Div, RadioGroup, RangeSlider, Select, TextInput, Button
from bokeh.layouts import row, column

import param.uiprop as uipp
import param.config as cfgp

import util.util as util
import units.units as units


@dataclass
class Limits:
    value: np.array
    ratio: np.array # default threshold as percentage of parameter target value
    wire : np.array

@dataclass
class Data:
    """Data for UIs
    """
    limits_wires: pd.DataFrame
    profile     : pd.Timestamp

@dataclass
class Sources:
    """Bokeh model column data source interfaces to data for UIs
    """
    limits_wires: ColumnDataSource

@dataclass
class Models:
    layout           : column = None

    limits_wires     : DataTable = None
    param_header     : Div = None

    active_param     : Div = None

    target           : TextInput = None

    limits_layout    : RadioGroup = None

    limits_low       : RangeSlider = None
    limits_high      : RangeSlider = None
    
    limit_warn_low   : TextInput = None
    limit_warn_high  : TextInput = None
    limit_alarm_low  : TextInput = None
    limit_alarm_high : TextInput = None

    wire_warn_low    : Select = None
    wire_warn_high   : Select = None
    wire_alarm_low   : Select = None
    wire_alarm_high  : Select = None
    wire_sep         : Div = None

    revert_param     : Button = None
    apply_param      : Button = None

    ratios_header    : Div = None
    warn_low_header  : Div = None
    warn_low_ratio   : TextInput = None
    warn_high_header : Div = None
    warn_high_ratio  : TextInput = None
    alarm_low_header : Div = None
    alarm_low_ratio  : TextInput = None
    alarm_high_header: Div = None
    alarm_high_ratio : TextInput = None


@unique
class ModelLayout(IntEnum):
    default = 0

@unique
class CallbackSource(IntEnum):
    ui             = 0
    sel_param_cb   = 1
    target_cb      = 2
    layout_cb      = 3
    limits_cb      = 4
    wires_cb       = 5
    revert_cb      = 6
    apply_cb       = 7
    limit_ratio_cb = 8

@unique
class LimitUIID(IntEnum):
    warn_low   = 0
    warn_high  = 1
    alarm_low  = 2
    alarm_high = 3
    both_low   = 4
    both_high  = 5


class Param(object):
    def __init__(self, session=None, verbose=util.VerboseLevel.info):
        """Initialize FasTrak3 alarm parameters
        """        
        self.session = session
        self.verbose = verbose

        if session is not None:
            self.unitsys = session.unitsys
        else:
            self.unitsys = units._FT3_UNITS_SYSTEM_DEFAULT

        self.num = cfgp._FT3_ALARM_PARAMETERS_NUM

        self.names = cfgp._FT3_ALARM_PARAMETER_DESCR
        self.units = cfgp._FT3_ALARM_PARAMETER_UNITS

        self.target = cfgp._FT3_ALARM_PARAMETER_TARGET_VALUES

        _v = cfgp._FT3_ALARM_PARAMETER_WARN_LIMITS[:,0]
        _r = cfgp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO
        _w = cfgp._FT3_ALARM_PARAMETER_WARN_WIRE[:,0]
        self.warn_low = Limits(value=_v, ratio=_r, wire=_w)

        _v = cfgp._FT3_ALARM_PARAMETER_WARN_LIMITS[:,1]
        _r = cfgp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO
        _w = cfgp._FT3_ALARM_PARAMETER_WARN_WIRE[:,1]
        self.warn_high = Limits(value=_v, ratio=_r, wire=_w)

        _v = cfgp._FT3_ALARM_PARAMETER_ALARM_LIMITS[:,0]
        _r = cfgp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO
        _w = cfgp._FT3_ALARM_PARAMETER_ALARM_WIRE[:,0]
        self.alarm_low = Limits(value=_v, ratio=_r, wire=_w)

        _v = cfgp._FT3_ALARM_PARAMETER_ALARM_LIMITS[:,1]
        _r = cfgp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO
        _w = cfgp._FT3_ALARM_PARAMETER_ALARM_WIRE[:,1]
        self.alarm_high = Limits(value=_v, ratio=_r, wire=_w)

        self.sel_param = None
        self.models = Models()

        self._make_data()
        self._make_models()

    def layout(self, mode=ModelLayout.default):
        """UI layout
        """
        _methodname = self.layout.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("parameter targets/limits/wires layout")
            sys.stdout.flush()

        if mode == ModelLayout.default:
            # Parameter headers
            _uir = []
            _uir += [row(self.models.param_header, self.models.ratios_header)]
            
            # Parameter limits and wires and global default warn/alarm ratios
            _rr = []
            _rr += [row(self.models.alarm_low_label, self.models.alarm_low_ratio)]
            _rr += [row(self.models.warn_low_label, self.models.warn_low_ratio)]
            _rr += [row(self.models.warn_high_label, self.models.warn_high_ratio)]
            _rr += [row(self.models.alarm_high_label, self.models.alarm_high_ratio)]
            _uir += [row(self.models.limits_wires, column(_rr))]

            # Active parameter identifier
            _uir += [self.models.active_param]
            
            # Parameter limits UI-type selector
            _uir += [self.models.limits_layout]

            # Parameter target and limits
            _uir += [row(self.models.limits_low, self.models.limit_alarm_low, self.models.limit_warn_low,
                         self.models.target,
                         self.models.limit_warn_high, self.models.limit_alarm_high, self.models.limits_high,
                         self.models.revert_param)]

            _uir += [row(self.models.wire_alarm_low, self.models.wire_warn_low, self.models.wire_sep,
                         self.models.wire_warn_high, self.models.wire_alarm_high, self.models.apply_param)]

            self.models.layout = column(_uir)
        else:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("unknown UI layout {}".format(mode))
                sys.stdout.flush()
            return
            
    def _make_data(self):
        """Make parameter datasets and sources.
        """
        _methodname = self._make_data.__name__

        # Parameter limits and wires
        s = []
        s += [pd.Series(data=self.names, name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[0])]
        try:
            s += [pd.Series(data=self.units[:,self.unitsys], name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[1])]
        except Exception as e:
            s += [pd.Series(data=self.units[:,0], name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[1])]
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("unit system exception e {}".format(e))
                sys.stdout.flush()

        # Engineering units conversions
        _Eu = cfgp._FT3_ALARM_PARAMETER_UNIT_CONVERSIONS[:,self.unitsys]

        s += [pd.Series(data=self.target * _Eu, name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[2])]
        s += [pd.Series(data=self.warn_low.value * _Eu, name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[3])]
        s += [pd.Series(data=self.warn_low.wire, name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[4])]
        s += [pd.Series(data=self.warn_high.value * _Eu, name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[5])]
        s += [pd.Series(data=self.warn_high.wire, name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[6])]
        s += [pd.Series(data=self.alarm_low.value * _Eu, name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[7])]
        s += [pd.Series(data=self.alarm_low.wire, name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[8])]
        s += [pd.Series(data=self.alarm_high.value * _Eu, name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[9])]
        s += [pd.Series(data=self.alarm_high.wire, name=uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS[10])]

        limits_wires = pd.concat(s, axis = 1)


        # UI data and bokeh model column data sources
        self.data = Data(limits_wires=limits_wires, profile=pd.Timestamp.now())
        self.sources = Sources(limits_wires=ColumnDataSource(limits_wires))

        # Register callback
        self.sources.limits_wires.selected.on_change('indices', self._sel_param_cb)

    def _make_models(self):
        """Make Bohel models
        """
        # Parameter limits and wires table
        _fields = uipp._FT3_ALARM_PARAMETER_TABLE_FIELDS
        _titles = uipp._FT3_ALARM_PARAMETER_TABLE_TITLES
        _widths = uipp._FT3_ALARM_PARAMETER_TABLE_WIDTHS
        _format = uipp._FT3_ALARM_PARAMETER_TABLE_FORMAT

        _columns = [TableColumn(field=f, title=_titles[k], width=_widths[k]) for k,f in enumerate(_fields)]
        for k,fmt in enumerate(_format):
            if fmt is not None:
                _columns[k].formatter = HTMLTemplateFormatter(template=fmt)
        
        p = DataTable(source=self.sources.limits_wires, columns=_columns,
                      reorderable=uipp._FT3_ALARM_PARAMETER_TABLE_REORDERABLE,
                      sortable=uipp._FT3_ALARM_PARAMETER_TABLE_SORTABLE,
                      width=uipp._FT3_ALARM_PARAMETER_TABLE_PX_W,
                      height=uipp._FT3_ALARM_PARAMETER_TABLE_PX_H,
                      margin=uipp._FT3_ALARM_PARAMETER_TABLE_MARGIN,
                      row_height=uipp._FT3_ALARM_PARAMETER_TABLE_PX_ROW,
                      index_header=uipp._FT3_ALARM_PARAMETER_TABLE_INDEX_HEADER,
                      index_position=uipp._FT3_ALARM_PARAMETER_TABLE_INDEX_POSITION,
                      tags=[CallbackSource.ui],
                      name=uipp._FT3_ALARM_PARAMETER_TABLE_NAME)
        self.models.limits_wires = p

        # Parameter warn/alarm limits and wires header
        mdl = Div(text=uipp._FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_TEXT,
                  style=uipp._FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_STYLE,
                  width=uipp._FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_PX_W,
                  height=uipp._FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_PX_H,
                  margin=uipp._FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_MARGIN,
                  name=uipp._FT3_ALARM_PARAMETER_TABLE_HEADER_DIV_NAME)
        self.models.param_header = mdl


        # Active parameter
        mdl = Div(text=uipp._FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_FORMAT.format(""),
                  style=uipp._FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_STYLE,
                  width=uipp._FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_PX_W,
                  height=uipp._FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_PX_H,
                  margin=uipp._FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_MARGIN,
                  name=uipp._FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_NAME)
        self.models.active_param = mdl


        # Parameter target
        mdl = TextInput(value=uipp._FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_VALUE,
                        width=uipp._FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_PX_W,
                        height=uipp._FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_PX_H,
                        margin=uipp._FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_MARGIN,
                        title=uipp._FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_TITLE,
                        tags=[CallbackSource.ui],
                        name=uipp._FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_NAME)
        self.models.target = mdl
        self.models.target.on_change('value', self._target_cb)


        # Warn/alarm limit layout selector
        mdl = RadioGroup(width=uipp._FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_PX_W,
                         height=uipp._FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_PX_H,
                         margin=uipp._FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_MARGIN,
                         orientation=uipp._FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_ORIENTATION,
                         labels=uipp._FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_LABELS,
                         active=uipp._FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_ACTIVE,
                         tags=[CallbackSource.ui],
                         name=uipp._FT3_ALARM_PARAMETER_LIMITS_UI_RADIO_GROUP_NAME)
        self.models.limits_layout = mdl
        self.models.limits_layout.on_click(self._limits_layout_cb)

                                      
        # Low warn/alarm limits 
        mdl = RangeSlider(start=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_START,
                          end=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_END,
                          step=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_STEP,
                          value=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_VALUE,
                          #callback_policy=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_CB_POLICY,
                          #callback_throttle=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_CB_THROTTLE_MS,
                          width=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_PX_W,
                          height=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_PX_H,
                          margin=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_MARGIN,
                          format=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_FORMAT,
                          bar_color=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_BAR_COLOR,
                          title=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_TITLE,
                          visible=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_VISIBLE,
                          tags=[CallbackSource.ui],
                          name=uipp._FT3_ALARM_PARAMETER_LIMITS_LOW_RNG_SLIDER_NAME)
        self.models.limits_low = mdl

        # High warn/alarm limits 
        mdl = RangeSlider(start=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_START,
                          end=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_END,
                          step=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_STEP,
                          value=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_VALUE,
                          #callback_policy=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_CB_POLICY,
                          #callback_throttle=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_CB_THROTTLE_MS,
                          width=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_PX_W,
                          height=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_PX_H,
                          margin=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_MARGIN,
                          format=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_FORMAT,
                          bar_color=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_BAR_COLOR,
                          title=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_TITLE,
                          visible=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_VISIBLE,
                          tags=[CallbackSource.ui],
                          name=uipp._FT3_ALARM_PARAMETER_LIMITS_HIGH_RNG_SLIDER_NAME)
        self.models.limits_high = mdl

        # Register warn/alarm limits callbacks
        try:
            # RangeSlider value_throttled property added in bokeh 1.2.0
            self.models.limits_low.on_change('value_throttled',
                lambda attr,old,new,ui=LimitUIID.both_low: self._limits_cb(attr, old, new, ui))
        except:
            self.models.limits_low.on_change('value',
                lambda attr,old,new,ui=LimitUIID.both_low: self._limits_cb(attr, old, new, ui))
        try:
            # RangeSlider value_throttled property added in bokeh 1.2.0
            self.models.limits_high.on_change('value_throttled',
                lambda attr,old,new,ui=LimitUIID.both_high: self._limits_cb(attr, old, new, ui))
        except:
            self.models.limits_high.on_change('value',
                lambda attr,old,new,ui=LimitUIID.both_high: self._limits_cb(attr, old, new, ui))


        #  Warn/alarm limits via alternate UIs
        mdl = TextInput(value=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_VALUE,
                        width=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_PX_W,
                        height=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_PX_H,
                        margin=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_MARGIN,
                        title=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_TITLE,
                        visible=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_VISIBLE,
                        tags=[CallbackSource.ui],
                        name=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_NAME)
        self.models.limit_warn_low = mdl

        mdl = TextInput(value=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_VALUE,
                        width=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_PX_W,
                        height=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_PX_H,
                        margin=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_MARGIN,
                        title=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_TITLE,
                        visible=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_VISIBLE,
                        tags=[CallbackSource.ui],
                        name=uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_NAME)
        self.models.limit_warn_high = mdl

        mdl = TextInput(value=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_VALUE,
                        width=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_PX_W,
                        height=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_PX_H,
                        margin=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_MARGIN,
                        title=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_TITLE,
                        visible=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_VISIBLE,
                        tags=[CallbackSource.ui],
                        name=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_NAME)
        self.models.limit_alarm_low = mdl

        mdl = TextInput(value=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_VALUE,
                        width=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_PX_W,
                        height=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_PX_H,
                        margin=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_MARGIN,
                        title=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_TITLE,
                        visible=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_VISIBLE,
                        tags=[CallbackSource.ui],
                        name=uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_NAME)
        self.models.limit_alarm_high = mdl

        # Register warn/alarm limits callbacks
        self.models.limit_warn_low.on_change('value',
                lambda attr,old,new,ui=LimitUIID.warn_low: self._limits_cb(attr, old, new, ui))
        self.models.limit_warn_high.on_change('value',
                lambda attr,old,new,ui=LimitUIID.warn_high: self._limits_cb(attr, old, new, ui))
        self.models.limit_alarm_low.on_change('value',
                lambda attr,old,new,ui=LimitUIID.alarm_low: self._limits_cb(attr, old, new, ui))
        self.models.limit_alarm_high.on_change('value',
                lambda attr,old,new,ui=LimitUIID.alarm_high: self._limits_cb(attr, old, new, ui))


        # Warn/alarm wires
        w = [uipp._FT3_ALARM_PARAMETER_WIRE_NONE]
        w += list(map(str,np.arange(start=uipp._FT3_ALARM_PARAMETER_WIRE_NUM_MIN,
                                    stop=uipp._FT3_ALARM_PARAMETER_WIRE_NUM_MAX+1,
                                    step=1, dtype=int)))
        mdl = Select(value=w[0], options=w,
                     width=uipp._FT3_ALARM_PARAMETER_WIRE_WARN_LOW_SEL_PX_W,
                     margin=uipp._FT3_ALARM_PARAMETER_WIRE_WARN_LOW_SEL_MARGIN,
                     title=uipp._FT3_ALARM_PARAMETER_WIRE_WARN_LOW_SEL_TITLE,
                     tags=[CallbackSource.ui],
                     name=uipp._FT3_ALARM_PARAMETER_WIRE_WARN_LOW_SEL_NAME)
        self.models.wire_warn_low = mdl

        mdl = Select(value=w[0], options=w,
                     width=uipp._FT3_ALARM_PARAMETER_WIRE_WARN_HIGH_SEL_PX_W,
                     margin=uipp._FT3_ALARM_PARAMETER_WIRE_WARN_HIGH_SEL_MARGIN,
                     title=uipp._FT3_ALARM_PARAMETER_WIRE_WARN_HIGH_SEL_TITLE,
                     tags=[CallbackSource.ui],
                     name=uipp._FT3_ALARM_PARAMETER_WIRE_WARN_HIGH_SEL_NAME)
        self.models.wire_warn_high = mdl

        mdl = Select(value=w[0], options=w,
                     width=uipp._FT3_ALARM_PARAMETER_WIRE_ALARM_LOW_SEL_PX_W,
                     margin=uipp._FT3_ALARM_PARAMETER_WIRE_ALARM_LOW_SEL_MARGIN,
                     title=uipp._FT3_ALARM_PARAMETER_WIRE_ALARM_LOW_SEL_TITLE,
                     tags=[CallbackSource.ui],
                     name=uipp._FT3_ALARM_PARAMETER_WIRE_ALARM_LOW_SEL_NAME)
        self.models.wire_alarm_low = mdl

        mdl = Select(value=w[0], options=w,
                     width=uipp._FT3_ALARM_PARAMETER_WIRE_ALARM_HIGH_SEL_PX_W,
                     margin=uipp._FT3_ALARM_PARAMETER_WIRE_ALARM_HIGH_SEL_MARGIN,
                     title=uipp._FT3_ALARM_PARAMETER_WIRE_ALARM_HIGH_SEL_TITLE,
                     tags=[CallbackSource.ui],
                     name=uipp._FT3_ALARM_PARAMETER_WIRE_ALARM_HIGH_SEL_NAME)
        self.models.wire_alarm_high = mdl

        # Register warn/alarm wire callbacks
        self.models.wire_warn_low.on_change('value',
            lambda attr,old,new,ui=LimitUIID.warn_low: self._wires_cb(attr, old, new, ui))
        self.models.wire_warn_high.on_change('value',
            lambda attr,old,new,ui=LimitUIID.warn_high: self._wires_cb(attr, old, new, ui))
        self.models.wire_alarm_low.on_change('value',
            lambda attr,old,new,ui=LimitUIID.alarm_low: self._wires_cb(attr, old, new, ui))
        self.models.wire_alarm_high.on_change('value',
            lambda attr,old,new,ui=LimitUIID.alarm_high: self._wires_cb(attr, old, new, ui))       

        # Wire layout separator
        mdl = Div(text=uipp._FT3_ALARM_PARAMETER_WIRE_SEP_DIV_TEXT,
                  style=uipp._FT3_ALARM_PARAMETER_WIRE_SEP_DIV_STYLE,
                  width=uipp._FT3_ALARM_PARAMETER_WIRE_SEP_DIV_PX_W,
                  height=uipp._FT3_ALARM_PARAMETER_WIRE_SEP_DIV_PX_H,
                  margin=uipp._FT3_ALARM_PARAMETER_WIRE_SEP_DIV_MARGIN,
                  name=uipp._FT3_ALARM_PARAMETER_WIRE_SEP_DIV_NAME)
        self.models.wire_sep = mdl

        # Revert selected-parameter limits/wires
        b = Button(label=uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_LABEL,
                   button_type=uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_TYPE_DISABLED,
                   disabled=uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_DISABLED_INIT,
                   width=uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_PX_W,
                   height=uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_PX_H,
                   margin=uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_MARGIN,
                   tags=[CallbackSource.ui],
                   name=uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_NAME)
        b.on_click(self._revert_param_cb)
        self.models.revert_param = b
        
        # Apply selected-parameter limits/wires
        b = Button(label=uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_LABEL,
                   button_type=uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_TYPE_DISABLED,
                   disabled=uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_DISABLED_INIT,
                   width=uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_PX_W,
                   height=uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_PX_H,
                   margin=uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_MARGIN,
                   tags=[CallbackSource.ui],
                   name=uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_NAME)
        b.on_click(self._apply_param_cb)
        self.models.apply_param = b

        # Global warn/alarm default percentage-of-target ratios
        mdl = Div(text=uipp._FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_TEXT,
                  style=uipp._FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_STYLE,
                  width=uipp._FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_PX_W,
                  height=uipp._FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_PX_H,
                  margin=uipp._FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_MARGIN,
                  name=uipp._FT3_ALARM_PARAMETER_TARGET_RATIOS_HEADER_DIV_NAME)
        self.models.ratios_header = mdl

        # Global low-warn default percentage-of-target ratio
        mdl = Div(text=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_TEXT,
                  style=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_STYLE,
                  width=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_PX_W,
                  height=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_PX_H,
                  margin=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_MARGIN,
                  name=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_DIV_NAME)
        self.models.warn_low_label = mdl
        
        mdl = TextInput(value=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_VALUE,
                        width=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_PX_W,
                        height=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_PX_H,
                        margin=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_MARGIN,
                        title=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_TITLE,
                        tags=[CallbackSource.ui],
                        name=uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_NAME)
        self.models.warn_low_ratio = mdl

        # Global high-warn default percentage-of-target ratio
        mdl = Div(text=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_TEXT,
                  style=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_STYLE,
                  width=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_PX_W,
                  height=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_PX_H,
                  margin=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_MARGIN,
                  name=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_DIV_NAME)
        self.models.warn_high_label = mdl
        
        mdl = TextInput(value=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_VALUE,
                        width=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_PX_W,
                        height=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_PX_H,
                        margin=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_MARGIN,
                        title=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_TITLE,
                        tags=[CallbackSource.ui],
                        name=uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_NAME)
        self.models.warn_high_ratio = mdl
        
        # Global low-alarm default percentage-of-target ratio
        mdl = Div(text=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_TEXT,
                  style=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_STYLE,
                  width=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_PX_W,
                  height=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_PX_H,
                  margin=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_MARGIN,
                  name=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_DIV_NAME)
        self.models.alarm_low_label = mdl
        
        mdl = TextInput(value=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_VALUE,
                        width=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_PX_W,
                        height=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_PX_H,
                        margin=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_MARGIN,
                        title=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_TITLE,
                        tags=[CallbackSource.ui],
                        name=uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_NAME)
        self.models.alarm_low_ratio = mdl

        # Global high-alarm default percentage-of-target ratio
        mdl = Div(text=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_TEXT,
                  style=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_STYLE,
                  width=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_PX_W,
                  height=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_PX_H,
                  margin=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_MARGIN,
                  name=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_DIV_NAME)
        self.models.alarm_high_label = mdl
        
        mdl = TextInput(value=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_VALUE,
                        width=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_PX_W,
                        height=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_PX_H,
                        margin=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_MARGIN,
                        title=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_TITLE,
                        tags=[CallbackSource.ui],
                        name=uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_NAME)
        self.models.alarm_high_ratio = mdl

        # Register warn/alarm default percentage-of-target ratio callbacks
        self.models.warn_low_ratio.on_change('value',
            lambda attr,old,new,ui=LimitUIID.warn_low: self._limit_ratio_cb(attr, old, new, ui))
        self.models.warn_high_ratio.on_change('value',
            lambda attr,old,new,ui=LimitUIID.warn_high: self._limit_ratio_cb(attr, old, new, ui))
        self.models.alarm_low_ratio.on_change('value',
            lambda attr,old,new,ui=LimitUIID.alarm_low: self._limit_ratio_cb(attr, old, new, ui))
        self.models.alarm_high_ratio.on_change('value',
            lambda attr,old,new,ui=LimitUIID.alarm_high: self._limit_ratio_cb(attr, old, new, ui))
        
    def _sel_param_cb(self, attr, old, new):
        """Selected-parameter properties
        """
        _methodname = self._sel_param_cb.__name__
        
        if self.verbose >= util.VerboseLevel.debug:
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("selected parameter properties {}".format(new))
            sys.stdout.flush()

        # Selected parameter
        p = self.sel_param = new[0]
        
        if p is None:
            return

        # Engineering units conversions
        _Eu = cfgp._FT3_ALARM_PARAMETER_UNIT_CONVERSIONS[p,self.unitsys]

        # UI interaction management
        me = self.models.limits_wires
        if me.tags == [CallbackSource.ui]:
            cb = CallbackSource.sel_param_cb
            self.models.target.tags = [cb]
            self.models.limits_low.tags = [cb]
            self.models.limits_high.tags = [cb]
            self.models.limit_warn_low.tags = [cb]
            self.models.limit_warn_high.tags = [cb]
            self.models.limit_alarm_low.tags = [cb]
            self.models.limit_alarm_high.tags = [cb]
            self.models.wire_warn_low.tags = [cb]
            self.models.wire_warn_high.tags = [cb]
            self.models.wire_alarm_low.tags = [cb]
            self.models.wire_alarm_high.tags = [cb]
        else:
            me.tags = [CallbackSource.ui]
            #return

        _df = self.sources.limits_wires.to_df()

        # Selected parameter
        _p_name = _df.parameter[p]
        self.models.active_param.text = uipp._FT3_ALARM_PARAMETER_ACTIVE_PARAM_DIV_FORMAT.format(_p_name)
        
        # Selected-parameter target
        target = _df.target[p]
        self.models.target.value = uipp._FT3_ALARM_PARAMETER_TARGET_TEXT_INPUT_FORMAT.format(target)

        # Selected parameter low warn/alarm limits
        _l = cfgp._FT3_ALARM_PARAMETER_MINMAX_VALUES[p,:][0] * _Eu
        _ds = (target - _l) * uipp._FT3_ALARM_PARAMETER_LIMITS_RNG_SLIDER_RESOLUTION
        _wL = _df.limit_warn_low[p]
        _aL = _df.limit_alarm_low[p]
        self.models.limits_low.start = _l
        self.models.limits_low.end = target
        self.models.limits_low.step = _ds
        try:
            # RangeSlider value_throttled property added in bokeh 1.2.0
            self.models.limits_low.value_throttled = self.models.limits_low.value = (_aL,_wL)
        except:
            self.models.limits_low.value = (_aL,_wL)

        # Selected parameter high warn/alarm limits
        _h = cfgp._FT3_ALARM_PARAMETER_MINMAX_VALUES[p,:][1] * _Eu
        _ds = (_h - target) * uipp._FT3_ALARM_PARAMETER_LIMITS_RNG_SLIDER_RESOLUTION
        _wH = _df.limit_warn_high[p]
        _aH = _df.limit_alarm_high[p]
        self.models.limits_high.start = target
        self.models.limits_high.end = _h
        self.models.limits_high.step = _ds
        try:
            # RangeSlider value_throttled property added in bokeh 1.2.0
            self.models.limits_high.value_throttled = self.models.limits_high.value = (_wH,_aH)            
        except:
            self.models.limits_high.value = (_wH,_aH)

        self.models.limit_warn_low.value = uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_LOW_TEXT_INPUT_FORMAT.format(_wL)
        self.models.limit_warn_high.value = uipp._FT3_ALARM_PARAMETER_LIMIT_WARN_HIGH_TEXT_INPUT_FORMAT.format(_wH)
        self.models.limit_alarm_low.value = uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_LOW_TEXT_INPUT_FORMAT.format(_aL)
        self.models.limit_alarm_high.value = uipp._FT3_ALARM_PARAMETER_LIMIT_ALARM_HIGH_TEXT_INPUT_FORMAT.format(_aH)

        # Selected parameter low warn wire
        el = _df.wire_warn_low[p]
        opt = self.models.wire_warn_low.options
        self.models.wire_warn_low.value = opt[el]

        # Selected parameter high warn wire
        el = _df.wire_warn_high[p]
        opt = self.models.wire_warn_high.options
        self.models.wire_warn_high.value = opt[el]

        # Selected parameter low alarm wire
        el = _df.wire_alarm_low[p]
        opt = self.models.wire_alarm_low.options
        self.models.wire_alarm_low.value = opt[el]

        # Selected parameter high alarm wire
        el = _df.wire_alarm_high[p]
        opt = self.models.wire_alarm_high.options
        self.models.wire_alarm_high.value = opt[el]

        # UI interaction management
        cb = CallbackSource.ui
        self.models.target.tags = [cb]
        self.models.limits_low.tags = [cb]
        self.models.limits_high.tags = [cb]
        self.models.limit_warn_low.tags = [cb]
        self.models.limit_warn_high.tags = [cb]
        self.models.limit_alarm_low.tags = [cb]
        self.models.limit_alarm_high.tags = [cb]
        self.models.wire_warn_low.tags = [cb]
        self.models.wire_warn_high.tags = [cb]
        self.models.wire_alarm_low.tags = [cb]
        self.models.wire_alarm_high.tags = [cb]

    def _target_cb(self, attr, old, new):
        """Selected-parameter target
        """
        _methodname = self._target_cb.__name__

        if self.verbose >= util.VerboseLevel.debug:
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("selected-parameter target {}".format(new))
            sys.stdout.flush()

        # Selected parameter
        p = self.sel_param
        
        if p is None:
            return

        # Engineering units conversions
        _Eu = cfgp._FT3_ALARM_PARAMETER_UNIT_CONVERSIONS[p,self.unitsys]

        # UI interaction management
        me = self.models.target
        if me.tags == [CallbackSource.sel_param_cb]:
            me.tags = [CallbackSource.ui]
            return

        # Parameter target
        _p0,_p1 = cfgp._FT3_ALARM_PARAMETER_MINMAX_VALUES[p,:] * _Eu
        _dp = _p1 - _p0
        _pvv = self.target[p] = min(max(np.float(new), _p0 + 1.e-06*_dp), _p1 - 1.e-06*_dp)

        # Warn/alarm limits as percentages of revised target
        _w0 = max(_pvv * np.float(self.models.warn_low_ratio.value), _p0)
        _w1 = min(_pvv * np.float(self.models.warn_high_ratio.value), _p1)
        _a0 = max(_pvv * np.float(self.models.alarm_low_ratio.value), _p0)
        _a1 = min(_pvv * np.float(self.models.alarm_high_ratio.value), _p1)

        # Parameter limits/wires data table consistency
        data_patch = {}
        data_patch.update(target = [(p, _pvv)])
        data_patch.update(limit_warn_low = [(p, _w0)])
        data_patch.update(limit_warn_high = [(p, _w1)])
        data_patch.update(limit_alarm_low = [(p, _a0)])
        data_patch.update(limit_alarm_high = [(p, _a1)])
        self.sources.limits_wires.patch(data_patch)

        # Selected-parameter widgets consistency
        self.models.limits_wires.tags = [CallbackSource.target_cb]
        self._sel_param_cb(None, None, [p])

        self.models.apply_param.disabled = False
        self.models.apply_param.button_type = uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_TYPE_ENABLED

        self.models.revert_param.disabled = False
        self.models.revert_param.button_type = uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_TYPE_ENABLED

    def _limits_layout_cb(self, new):
        """Warn/alarm limits layout selector
        """
        _methodname = self._limits_layout_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("warn/alarm limits layout [{}]".format(new))
            sys.stdout.flush()

        M0 = [self.models.limits_low, self.models.limits_high]
        M1 = [self.models.limit_warn_low, self.models.limit_warn_high,
              self.models.limit_alarm_low, self.models.limit_alarm_high]

        if new:
            # Warn/alarm limits via keyboard
            for m in M1:
                m.visible = True
            for m in M0:
                m.visible = False
        else:
            # Warn/alarm limits via range-sliders
            for m in M0:
                m.visible = True
            for m in M1:
                m.visible = False

    def _limits_cb(self, attr, old, new, ui):
        """Selected-parameter low warn/alarm or high warn/alarm limits
        """
        _methodname = self._limits_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("selected-parameter limits {} [{}]".format(new, ui))
            sys.stdout.flush()

        # Selected parameter
        p = self.sel_param
        
        if p is None:
            return

        # Parameter limits/wires data table consistency
        if ui == LimitUIID.warn_low:
            # UI interaction management
            me = self.models.limit_warn_low
            if me.tags == [CallbackSource.sel_param_cb]:
                me.tags = [CallbackSource.ui]
                return

            self.sources.limits_wires.patch({"limit_warn_low": [(p, np.float(new))]})

        elif ui == LimitUIID.warn_high:
            # UI interaction management
            me = self.models.limit_warn_high
            if me.tags == [CallbackSource.sel_param_cb]:
                me.tags = [CallbackSource.ui]
                return

            self.sources.limits_wires.patch({"limit_warn_high": [(p, np.float(new))]})

        elif ui == LimitUIID.alarm_low:
            # UI interaction management
            me = self.models.limit_alarm_low
            if me.tags == [CallbackSource.sel_param_cb]:
                me.tags = [CallbackSource.ui]
                return

            self.sources.limits_wires.patch({"limit_alarm_low": [(p, np.float(new))]})

        elif ui == LimitUIID.alarm_high:
            # UI interaction management
            me = self.models.limit_alarm_high
            if me.tags == [CallbackSource.sel_param_cb]:
                me.tags = [CallbackSource.ui]
                return

            self.sources.limits_wires.patch({"limit_alarm_high": [(p, np.float(new))]})

        elif ui == LimitUIID.both_low:
            # UI interaction management
            me = self.models.limits_low
            if me.tags == [CallbackSource.sel_param_cb]:
                me.tags = [CallbackSource.ui]
                return

            try:
                _a,_w = self.models.limits_low.value_throttled                
            except:
                _a,_w = self.models.limits_low.value

            self.alarm_low.value,self.warn_low.value = _a,_w

            data_patch = {}
            data_patch.update(limit_warn_low = [(p, _w)])
            data_patch.update(limit_alarm_low = [(p, _a)])

            self.sources.limits_wires.patch(data_patch)

        elif ui == LimitUIID.both_high:
            # UI interaction management
            me = self.models.limits_high
            if me.tags == [CallbackSource.sel_param_cb]:
                me.tags = [CallbackSource.ui]
                return

            try:
                _w,_a = self.models.limits_high.value_throttled
            except:
                _w,_a = self.models.limits_high.value

            self.alarm_high.value,self.warn_high.value = _a,_w

            data_patch = {}
            data_patch.update(limit_warn_high = [(p, _w)])
            data_patch.update(limit_alarm_high = [(p, _a)])

            self.sources.limits_wires.patch(data_patch)
 
        else:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("unknown limit UIID property {}".format(ui))
                sys.stdout.flush()
            return

        # Selected-parameter UI consistency update
        self.models.limits_wires.tags = [CallbackSource.layout_cb]
        self._sel_param_cb(None, None, [p])

        self.models.apply_param.disabled = False
        self.models.apply_param.button_type = uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_TYPE_ENABLED

        self.models.revert_param.disabled = False
        self.models.revert_param.button_type = uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_TYPE_ENABLED

    def _wires_cb(self, attr, old, new, ui):
        """Selected-parameter wire
        """
        _methodname = self._wires_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("selected-parameter wire {} [{}]".format(new, ui))
            sys.stdout.flush()

        # Selected parameter
        p = self.sel_param
        
        if p is None:
            return

        # Parameter limits/wires data table consistency
        if ui == LimitUIID.warn_low:
            # UI interaction management
            me = self.models.wire_warn_low
            if me.tags == [CallbackSource.sel_param_cb]:
                me.tags = [CallbackSource.ui]
                return

            el = self.models.wire_warn_low.options.index(new)
            self.warn_low.wire[p] = el
            self.sources.limits_wires.patch({"wire_warn_low": [(p, el)]})

        elif ui == LimitUIID.warn_high:
            me = self.models.wire_warn_high
            if me.tags == [CallbackSource.sel_param_cb]:
                me.tags = [CallbackSource.ui]
                return

            el = self.models.wire_warn_high.options.index(new)
            self.warn_high.wire[p] = el
            self.sources.limits_wires.patch({"wire_warn_high": [(p, el)]})

        elif ui == LimitUIID.alarm_low:
            me = self.models.wire_alarm_low
            if me.tags == [CallbackSource.sel_param_cb]:
                me.tags = [CallbackSource.ui]
                return

            el = self.models.wire_alarm_low.options.index(new)
            self.alarm_low.wire[p] = el
            self.sources.limits_wires.patch({"wire_alarm_low": [(p, el)]})

        elif ui == LimitUIID.alarm_high:
            me = self.models.wire_alarm_high
            if me.tags == [CallbackSource.sel_param_cb]:
                me.tags = [CallbackSource.ui]
                return

            el = self.models.wire_alarm_high.options.index(new)
            self.alarm_high.wire[p] = el
            self.sources.limits_wires.patch({"wire_alarm_high": [(p, el)]})

        else:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("unknown limit UIID property {}".format(ui))
                sys.stdout.flush()
            return

        self.models.apply_param.disabled = False
        self.models.apply_param.button_type = uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_TYPE_ENABLED

        self.models.revert_param.disabled = False
        self.models.revert_param.button_type = uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_TYPE_ENABLED

    def _revert_param_cb(self):
        """Revert parameter targets/limits/wires
        """
        _methodname = self._revert_param_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("revert parameter targets/limits/wires")
            sys.stdout.flush()

        # Parameter limits/wires data table reversion
        d = self.data.limits_wires
        p = slice(self.num)

        data_patch = {}
        data_patch.update(target = [(p, d.target)])
        data_patch.update(limit_warn_low = [(p, d.limit_warn_low)])
        data_patch.update(limit_warn_high = [(p, d.limit_warn_high)])
        data_patch.update(limit_alarm_low = [(p, d.limit_alarm_low)])
        data_patch.update(limit_alarm_high = [(p, d.limit_alarm_high)])
        data_patch.update(wire_warn_low = [(p, d.wire_warn_low)])
        data_patch.update(wire_warn_high = [(p, d.wire_warn_high)])
        data_patch.update(wire_alarm_low = [(p, d.wire_alarm_low)])
        data_patch.update(wire_alarm_high = [(p, d.wire_alarm_high)])        

        self.sources.limits_wires.patch(data_patch)

        # Selected-parameter UI consistency update
        self.models.limits_wires.tags = [CallbackSource.revert_cb]

        p = self.sel_param
        self._sel_param_cb(None, None, [p])

        self.models.apply_param.disabled = True
        self.models.apply_param.button_type = uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_TYPE_DISABLED

        self.models.revert_param.disabled = True
        self.models.revert_param.button_type = uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_TYPE_DISABLED

    def _apply_param_cb(self):
        """Apply parameter targets/limits/wires
        """
        _methodname = self._apply_param_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("apply parameter targets/limits/wires")
            sys.stdout.flush()

        # Parameter limits/wires data table update
        self.data.limits_wires = self.sources.limits_wires.to_df()
        self.data.limits_wires.drop(columns="index", inplace=True)

        self.models.apply_param.disabled = True
        self.models.apply_param.button_type = uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_TYPE_DISABLED

        self.models.revert_param.disabled = True
        self.models.revert_param.button_type = uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_TYPE_DISABLED

        # Alarm/warn parameter limits
        self.session.state.param_limits_update()

        # Alarm state
        self.session.state.update()

        # SQL database
        self.data.profile = pd.Timestamp.now()
        self.session.alarm.sql_write()

    def _limit_ratio_cb(self, attr, old, new, ui):
        """Global parameter warn/alarm limits as percentage of targets
        """
        _methodname = self._limit_ratio_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("parameter warn/alarm limits (% of target) {} [{}]".format(new, ui))
            sys.stdout.flush()

        # Engineering units conversions
        _Eu = cfgp._FT3_ALARM_PARAMETER_UNIT_CONVERSIONS[:,self.unitsys]

        lim = np.float(new)

        if ui == LimitUIID.warn_low:
            _w = min(max(lim, self.alarm_low.ratio), 1.00)

            self.warn_low.ratio = np.float(_w)
            self.models.warn_low_ratio.value = uipp._FT3_ALARM_PARAMETER_WARN_LOW_RATIO_TEXT_INPUT_FORMAT.format(_w)

            W = self.warn_low.value = np.array([(v * _w) for v in self.target])
            self.sources.limits_wires.patch({"limit_warn_low": [(slice(self.num), W * _Eu)]})

        elif ui == LimitUIID.warn_high:
            _w = min(max(lim, 1.00), self.alarm_high.ratio)

            self.warn_high.ratio = np.float(_w)
            self.models.warn_high_ratio.value = uipp._FT3_ALARM_PARAMETER_WARN_HIGH_RATIO_TEXT_INPUT_FORMAT.format(_w)

            W = self.warn_high.value = np.array([(v * _w) for v in self.target])
            self.sources.limits_wires.patch({"limit_warn_high": [(slice(self.num), W * _Eu)]})

        elif ui == LimitUIID.alarm_low:
            _a = min(max(lim, 0.00), self.warn_low.ratio)

            self.alarm_low.ratio = np.float(_a)
            self.models.alarm_low_ratio.value = uipp._FT3_ALARM_PARAMETER_ALARM_LOW_RATIO_TEXT_INPUT_FORMAT.format(_a)

            A = self.alarm_low.value = np.array([(v * _a) for v in self.target])
            self.sources.limits_wires.patch({"limit_alarm_low": [(slice(self.num), A * _Eu)]})

        elif ui == LimitUIID.alarm_high:
            _a = min(max(lim, self.warn_high.ratio), 10.00)

            self.alarm_high.ratio = np.float(_a)
            self.models.alarm_high_ratio.value = uipp._FT3_ALARM_PARAMETER_ALARM_HIGH_RATIO_TEXT_INPUT_FORMAT.format(_a)

            A = self.alarm_high.value = np.array([(v * _a) for v in self.target])
            self.sources.limits_wires.patch({"limit_alarm_high": [(slice(self.num), A * _Eu)]})

        else:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("unknown limit UIID property {}".format(ui))
                sys.stdout.flush()
            return

        # Selected-parameter UI consistency update
        self.models.limits_wires.tags = [CallbackSource.target_cb]

        p = self.sel_param
        self._sel_param_cb(None, None, [p])

        self.models.apply_param.disabled = False
        self.models.apply_param.button_type = uipp._FT3_ALARM_PARAMETER_APPLY_BUTTON_TYPE_ENABLED

        self.models.revert_param.disabled = False
        self.models.revert_param.button_type = uipp._FT3_ALARM_PARAMETER_REVERT_BUTTON_TYPE_ENABLED

    def __deepcopy__(self, memo):
        """Overloaded deepcopy method to support save of part/parameters via part class
           without copies of UI sources, models, and selected-parameter reference
        """
        _methodname = self.__deepcopy__.__name__

        cls = self.__class__
        rv = cls.__new__(cls)

        memo[id(self)] = rv
        llex = ['sources','models','sel_param']

        for k, v in self.__dict__.items():
            if k in llex:
                setattr(rv, k, None)
            else:
                try:
                    setattr(rv, k, copy.deepcopy(v, memo))
                except Exception as e:
                    setattr(rv, k, None)
                    if self.verbose >= util.VerboseLevel.error:
                        util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                        print("deepcopy exception e {}".format(e))
                        sys.stdout.flush()

        return rv
