#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 alarm state visualizations
"""
import sys

from functools import partial
from tornado import gen

import numpy as np
import pandas as pd

from dataclasses import dataclass
from enum import IntEnum,unique

from bokeh.models import ColumnDataSource
from bokeh.models import Label, LabelSet, HoverTool

from bokeh.events import Tap, DoubleTap

from bokeh.plotting import figure
from bokeh.layouts import row, column

import state.config as cfgss
import state.data as datas
import state.uiprop as uipss

import param.config as cfgp

import util.util as util


@dataclass
class UIIndexes:
    """UI indexes of displayed shot and alarm data
    """
    min_shot: int # Alarm-state window mininum shot index
    max_shot: int # Alarm-state window maximum shot index
    sel_shot: int # Alarm-state window selected shot index
    num_view: int # Alarm-state window shot span
    num_shot: int # Number of shots in FasTrak3 shot database

@dataclass
class Data:
    """Data for UIs
    """
    alarm_state : pd.DataFrame
    alarm_hist  : pd.Series
    ui_sel_state: pd.DataFrame
    ui_sel_param: pd.DataFrame
    ui_shot_info: pd.DataFrame

@dataclass
class Sources:
    """Bokeh model column data source interfaces to data for UIs
    """
    alarm_view  : ColumnDataSource
    ui_sel_state: ColumnDataSource
    ui_sel_param: ColumnDataSource
    ui_shot_info: ColumnDataSource

@dataclass
class Models:
    layout     : column
    alarm_state: figure
    sel_shot   : figure


@unique
class ModelLayout(IntEnum):
    default = 0


class State(object):
    def __init__(self, session=None, verbose=util.VerboseLevel.info):
        """Initiailze FasTrak3 alarm state
        """
        self.session = session
        self.verbose = verbose

        self.unitsys = session.unitsys

        self.data = Data(alarm_state=pd.DataFrame(),
                         alarm_hist=pd.Series(),
                         ui_sel_state=pd.DataFrame(),
                         ui_sel_param=pd.DataFrame(),
                         ui_shot_info=pd.DataFrame())

        self.sources = Sources(alarm_view=None,
                               ui_sel_state=None,
                               ui_sel_param=None,
                               ui_shot_info=None)

        self.models = Models(layout=None,
                             alarm_state=None,
                             sel_shot=None)

        self._make_ui_data()
        self._make_ui_models()

    def read(self):
        """Read SQL database alarm-state table
        """
        pass

    def write(self):
        """Write SQL database alarm-state table
        """
        pass
    
    def layout(self, mode=ModelLayout.default):
        """UI layout
        """
        _methodname = self.layout.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("parameter targets/limits/wires layout")
            sys.stdout.flush()

        if mode == ModelLayout.default:
            _uir = []

            # Alarm state
            _uir += [row(self.models.sel_shot, self.models.alarm_state)]

            self.models.layout = column(_uir)

    def update(self, init=False):
        """Schedule alarm state updates
           (Alarm state data, sources, and UIs)
        """
        _methodname = self.update.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("alarm state data, sources, and UIs (init={})".format(init))
            sys.stdout.flush()

        # Shot parameter data
        _spdf = self.session.board.data.param.data

        _s = _spdf.shot.copy()
        _S = _spdf.drop(columns=cfgss._FT3_ALARM_STATE_SHOT_VARIABLE)

        _P = self.session.part.param
        _L = _P.data.limits_wires

        # Machine resolution (to guarantee unique bin edges for alarm-state classification)
        _res = cfgss._FT3_ALARM_STATE_RESOLUTION
        _resh = cfgss._FT3_ALARM_STATE_RESOLUTION_H

        # Engineering units conversions
        _Eu = cfgp._FT3_ALARM_PARAMETER_UNIT_CONVERSIONS[:,self.unitsys]


        # Profile/debug
        if self.verbose >= util.VerboseLevel.profile:
            t0 = util._FT3_UTIL_NOW_TS()

        
        lbls = ["alarm_low","warn_low","none","warn_high","alarm_high"]
        p = []
        for i in range(_P.num):
            lw = _L.loc[i]
            bins = [-np.inf,lw.limit_alarm_low-_res,lw.limit_warn_low-_resh,lw.limit_warn_high+_resh,lw.limit_alarm_high+_res,np.inf]
            p += [pd.cut(_S.iloc[:,i] * _Eu[i], bins=bins, labels=lbls, precision=cfgss._FT3_ALARM_STATE_PRECISION)]


        # Profile/debug
        if self.verbose >= util.VerboseLevel.profile:
            tf = util._FT3_UTIL_NOW_TS()
            util._FT3_UTIL_VERBOSE_PROFILE_WITH_TS(_methodname)
            print("alarm-parameter classification profile {:.3f}s".format((tf-t0).total_seconds()))
            sys.stdout.flush()
            t1 = tf


        _alarm_state = pd.concat(p, axis=1)
        _alarm_state = _alarm_state.replace(cfgss._FT3_ALARM_STATE_MAP, inplace=False)

        # E-mail/SMS alerts
        try:
            if not _alarm_state.empty:
                _cat = _alarm_state.iloc[-1].values
                _oobL = _cat == datas.AlarmState.alarm_low
                _oobH = _cat == datas.AlarmState.alarm_high

                _errL = ['<{:}>: low alarm'.format(cfgp._FT3_ALARM_PARAMETER_DESCR[i]) for i in range(_P.num) if _oobL[i]]
                _errH = ['<{:}>: high alarm'.format(cfgp._FT3_ALARM_PARAMETER_DESCR[i]) for i in range(_P.num) if _oobH[i]]
                _err = _errL + _errH

                if _err:
                    self.session.alert.push(_err)
        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("email/SMS exception e {:}".format(e))
                print("")
                sys.stdout.flush()

        # Alarm state, all shots
        cmap = uipss._FT3_ALARM_STATE_STATUS_RECT_COLOR_MAP
        _c = list(map(lambda x: cmap[x], _alarm_state.values.flatten()))
        _c += [uipss._FT3_ALARM_STATE_STATUS_RECT_COLOR_EMPTY] * (uipss._FT3_ALARM_STATE_STATUS_PLOT_NUMEL - len(_c))
        c = pd.Series(data=_c, name="color")


        # Profile/debug
        if self.verbose >= util.VerboseLevel.profile:
            tf = util._FT3_UTIL_NOW_TS()
            util._FT3_UTIL_VERBOSE_PROFILE_WITH_TS(_methodname)
            print("alarm-state buildup profile            {:.3f}s".format((tf-t1).total_seconds()))
            sys.stdout.flush()
            t1 = tf


        uiid = pd.Series(data=_s.index, name="uiid").repeat(10).reset_index(drop=True)
        shot = _s.repeat(cfgp._FT3_ALARM_PARAMETERS_NUM).reset_index(drop=True)
        _alarm_hist = pd.concat((uiid,shot,c), axis=1)

        # Alarm state data
        self.data.alarm_state = pd.concat((_s,_alarm_state), axis=1)
        self.data.alarm_hist = _alarm_hist

        if init:
            # Alarm state, UI shot window view
            _x,_y = np.meshgrid(range(0,uipss._FT3_ALARM_STATE_STATUS_PLOT_ROWS),
                                range(0,uipss._FT3_ALARM_STATE_STATUS_PLOT_COLS))
            x = pd.Series(data=_x.flatten(order='C'), name="parameter")
            y = pd.Series(data=_y.flatten(order='C'), name="shot")

            _alarm_view = pd.concat(
                              (x,y,c[-(uipss._FT3_ALARM_STATE_STATUS_PLOT_NUMEL):].reset_index(drop=True)),
                              axis=1)
            self.sources.alarm_view = ColumnDataSource(_alarm_view)
        else:
            # Schedule UI updates
            # Alarm state sources and UIs
            _doc = self.models.alarm_state.document
            _doc.add_next_tick_callback(partial(self._threadsafe_update_cb))


        # Profile/debug
        if self.verbose >= util.VerboseLevel.profile:
            tf = util._FT3_UTIL_NOW_TS()
            util._FT3_UTIL_VERBOSE_PROFILE_WITH_TS(_methodname)
            print("alarm history and cb scheduler profile {:.3f}s".format((tf-t1).total_seconds()))
            util._FT3_UTIL_VERBOSE_PROFILE_WITH_TS(_methodname)
            print("state-module total profile             {:.3f}s".format((tf-t0).total_seconds()))
            print("")
            sys.stdout.flush()

    @gen.coroutine
    def _threadsafe_update_cb(self):
        """Threadsafe alarm-state callback
        """
        _methodname = self._threadsafe_update_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("plot warn/alarm state parameters")
            sys.stdout.flush()

        event = Tap(model=None, x=uipss._FT3_ALARM_STATE_STATUS_PLOT_COLS)
        self._sel_shot_cb(event=event, sequp=False)

    def param_limits_update(self):
        """Update parameter limits
           (Targets/limits in alarm-state parameter hover tooltips)
        """
        _methodname = self.param_limits_update.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("targets/limits in alarm-state parameter hover tooltips")
            sys.stdout.flush()

        p = slice(self.session.part.param.num)
        lw = self.session.part.param.data.limits_wires
        
        data_patch = {}
        data_patch.update(p_target = [(p, lw.target)])
        data_patch.update(p_warn_low = [(p, lw.limit_warn_low)])
        data_patch.update(p_warn_high = [(p, lw.limit_warn_high)])
        data_patch.update(p_alarm_low = [(p, lw.limit_alarm_low)])
        data_patch.update(p_alarm_high = [(p, lw.limit_alarm_high)])

        s = self.sources.ui_sel_param
        s.patch(data_patch)

    def _make_ui_data(self):
        """Make alarm-state datasets and sources
        """
        # Alarm state
        self.update(init=True)

        # Shot parameter data
        _spdf = self.session.board.data.param.data

        # Initial UI shot indexes and shot data dimensions
        # NB: UI shot indexes are not equal to shot numbers in general
        num_shot = len(_spdf)
        num_view = min(num_shot,uipss._FT3_ALARM_STATE_STATUS_PLOT_COLS)
        min_shot = (num_shot - num_view)
        sel_shot = max_shot = max((num_shot - 1), 0)
        self.uii = UIIndexes(min_shot=min_shot,
                             max_shot=max_shot,
                             sel_shot=sel_shot,
                             num_view=num_view,
                             num_shot=num_shot)

        # Selected-shot alarm-state UI highlight origin
        ui_sel_state = pd.DataFrame(data=np.array([[0.0,(uipss._FT3_ALARM_STATE_STATUS_PLOT_ROWS - 1.0)/2.0]]), columns=("x","y"))


        # Selected-shot parameters and metadata
        x_lbl = pd.Series(data=np.zeros(cfgp._FT3_ALARM_PARAMETERS_NUM) +
                          uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_ORIGIN_X, name="x_lbl")
        x_data = pd.Series(data=np.zeros(cfgp._FT3_ALARM_PARAMETERS_NUM) +
                           uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_ORIGIN_X, name="x_data")
        x_units = pd.Series(data=np.zeros(cfgp._FT3_ALARM_PARAMETERS_NUM) +
                            uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_ORIGIN_X, name="x_units")        
        x_meta = pd.Series(data=np.zeros(cfgp._FT3_ALARM_PARAMETERS_NUM) +
                           uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_ORIGIN_X, name="x_meta")

        ui_sel_param = pd.concat((x_lbl,x_data,x_units,x_meta), axis=1)

        p_num = pd.Series(data=np.arange(0,cfgp._FT3_ALARM_PARAMETERS_NUM,1), name="p_num")
        p_descr = pd.Series(data=cfgp._FT3_ALARM_PARAMETER_DESCR, name="p_descr")

        if num_shot > 0:
            shot_data = pd.Series(data=_spdf.values[sel_shot], name="shot_data")
        else:
            shot_data = pd.Series(data=[np.nan]*cfgp._FT3_ALARM_PARAMETERS_NUM, name="shot_data")
        p_data = shot_data.apply(lambda x: uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_FORMAT.format(x))
        p_data.name = "p_data"

        p_color = pd.Series(data=["#000000"] * cfgp._FT3_ALARM_PARAMETERS_NUM, name="p_color")
        p_units = pd.Series(data=cfgp._FT3_ALARM_PARAMETER_UNITS[:,self.unitsys], name="p_units")

        ui_sel_param = pd.concat((ui_sel_param,p_num,p_descr,p_data,p_color,p_units), axis=1)

        # Parameter warn/alarm limits
        _lw = self.session.part.param.data.limits_wires

        p_target = pd.Series(data=_lw.target, name="p_target")
        p_warn_low = pd.Series(data=_lw.limit_warn_low, name="p_warn_low")
        p_warn_high = pd.Series(data=_lw.limit_warn_high, name="p_warn_high")
        p_alarm_low = pd.Series(data=_lw.limit_alarm_low, name="p_alarm_low")
        p_alarm_high = pd.Series(data=_lw.limit_alarm_high, name="p_alarm_high")
        
        ui_sel_param = pd.concat((ui_sel_param,p_warn_low,p_warn_high,p_target,p_alarm_low,p_alarm_high), axis=1)


        # UI shot info (selected, min, max) shot indexes to shot numbers
        ui_x = pd.Series(data=[0.0, 0.0, max(num_view - 1.0, 0.0)], name="ui_x")
        ui_y = pd.Series(data=[-1.0] * 3, name="ui_y")

        _s = _spdf.shot

        if not _s.empty:
            ui_shot = pd.Series(data=[_s[sel_shot],_s[min_shot],_s[max_shot]], name="ui_shot")
            ui_shot = ui_shot.apply(lambda x: uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_FORMAT.format(x))
        else:
            ui_shot = pd.Series(data=["?"] * 3, name="ui_shot")

        ui_shot_info = pd.concat((ui_x,ui_y,ui_shot), axis=1)


        # UI data and bokeh model column data sources
        self.data.ui_sel_state = ui_sel_state
        self.data.ui_sel_param = ui_sel_param
        self.data.ui_shot_info = ui_shot_info

        self.sources.ui_sel_state = ColumnDataSource(ui_sel_state)
        self.sources.ui_sel_param = ColumnDataSource(ui_sel_param)
        self.sources.ui_shot_info = ColumnDataSource(ui_shot_info)
        
    def _make_ui_models(self):
        """Make Bokeh models
        """
        # Alarm state
        p = figure(plot_width=uipss._FT3_ALARM_STATE_STATUS_PLOT_PX_W,
                   plot_height=uipss._FT3_ALARM_STATE_STATUS_PLOT_PX_H,
                   min_border=uipss._FT3_ALARM_STATE_STATUS_PLOT_PX_BORDER,
                   x_range=uipss._FT3_ALARM_STATE_STATUS_PLOT_XRANGE,
                   y_range=uipss._FT3_ALARM_STATE_STATUS_PLOT_YRANGE,
                   #output_backend=uipss._FT3_ALARM_STATE_STATUS_PLOT_OUTPUT_BACKEND,
                   name=uipss._FT3_ALARM_STATE_STATUS_PLOT_NAME)

        p.background_fill_color = uipss._FT3_ALARM_STATE_STATUS_PLOT_BACKGROUND

        p.xaxis.visible = uipss._FT3_ALARM_STATE_STATUS_PLOT_VISIBLE_XAXIS
        p.xgrid.visible = uipss._FT3_ALARM_STATE_STATUS_PLOT_VISIBLE_XGRID
        p.xgrid.ticker  = uipss._FT3_ALARM_STATE_STATUS_PLOT_TICKER_XGRID

        p.yaxis.visible = uipss._FT3_ALARM_STATE_STATUS_PLOT_VISIBLE_YAXIS
        p.ygrid.visible = uipss._FT3_ALARM_STATE_STATUS_PLOT_VISIBLE_YGRID
        p.ygrid.ticker  = uipss._FT3_ALARM_STATE_STATUS_PLOT_TICKER_YGRID

        p.toolbar_location = uipss._FT3_ALARM_STATE_STATUS_PLOT_LOC_TOOLS

        s = self.sources.alarm_view
        p.rect(x="shot", y="parameter", source=s, color="color",
               width=uipss._FT3_ALARM_STATE_STATUS_RECT_W,
               height=uipss._FT3_ALARM_STATE_STATUS_RECT_H,
               alpha=uipss._FT3_ALARM_STATE_STATUS_RECT_ALPHA,
               name=uipss._FT3_ALARM_STATE_STATUS_RECT_NAME)

        s = self.sources.ui_sel_state
        p.rect(x="x", y="y", source=s,
               color=uipss._FT3_ALARM_STATE_ACTIVE_RECT_COLOR,
               line_color=uipss._FT3_ALARM_STATE_ACTIVE_RECT_LINE_COLOR,
               line_width=uipss._FT3_ALARM_STATE_ACTIVE_RECT_LINE_WIDTH,
               width=uipss._FT3_ALARM_STATE_ACTIVE_RECT_W,
               height=uipss._FT3_ALARM_STATE_ACTIVE_RECT_H,
               alpha=uipss._FT3_ALARM_STATE_ACTIVE_RECT_ALPHA,
               name=uipss._FT3_ALARM_STATE_ACTIVE_RECT_NAME)

        p.triangle(x=uipss._FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_X,
                   y=uipss._FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_Y,
                   size=uipss._FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_SIZE,
                   angle=uipss._FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_ANGLE,
                   fill_color=uipss._FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_FILL_COLOR,
                   fill_alpha=uipss._FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_FILL_ALPHA,
                   line_color=uipss._FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_LINE_COLOR,
                   line_width=uipss._FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_LINE_WIDTH,
                   name=uipss._FT3_ALARM_STATE_PREV_SHOT_TRIANGLE_NAME)

        p.triangle(x=uipss._FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_X,
                   y=uipss._FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_Y,
                   size=uipss._FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_SIZE,
                   angle=uipss._FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_ANGLE,
                   fill_color=uipss._FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_FILL_COLOR,
                   fill_alpha=uipss._FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_FILL_ALPHA,
                   line_color=uipss._FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_LINE_COLOR,
                   line_width=uipss._FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_LINE_WIDTH,
                   name=uipss._FT3_ALARM_STATE_NEXT_SHOT_TRIANGLE_NAME)

        s = self.sources.ui_shot_info
        ll = LabelSet(x='ui_x', y='ui_y', text='ui_shot', source=s,
                 text_color=uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_TEXT_COLOR,
                 text_font_size=uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_FONT_SIZE,
                 text_font_style=uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_FONT_STYLE,
                 level=uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_LEVEL,
                 text_align=uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_ALIGN,
                 text_baseline=uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_BASELINE,
                 x_offset=uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_OFFSET_X,
                 y_offset=uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_OFFSET_Y,
                 name=uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_NAME)
        p.add_layout(ll)

        # Register callbacks
        p.on_event(Tap, self._sel_shot_cb)
        p.on_event(DoubleTap, self._sel_shot_cb)

        self.models.alarm_state = p


        # Shot parameters
        p = figure(plot_width=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_PX_W,
                   plot_height=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_PX_H,
                   min_border=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_PX_BORDER,
                   x_range=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_XRANGE,
                   y_range=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_YRANGE,
                   #output_backend=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_OUTPUT_BACKEND,
                   name=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_NAME)

        p.background_fill_color = uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_BACKGROUND

        p.xaxis.visible = uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_VISIBLE_XAXIS
        p.xgrid.visible = uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_VISIBLE_XGRID
        p.xgrid.ticker  = uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_TICKER_XGRID

        p.yaxis.visible = uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_VISIBLE_YAXIS
        p.ygrid.visible = uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_VISIBLE_YGRID
        p.ygrid.ticker  = uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_TICKER_YGRID

        p.toolbar_location = uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PLOT_LOC_TOOLS

        s = self.sources.ui_sel_param
        p.circle(x="x_meta", y="p_num", source=s,
                 color=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_COLOR,
                 size=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_SIZE_PTS,
                 alpha=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_ALPHA,
                 name=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_NAME)

        ll = Label(x=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_ORIGIN_X,
                   y=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_ORIGIN_Y,
                   text=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_TEXT,
                   text_color=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_TEXT_COLOR,
                   text_font_size=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_FONT_SIZE,
                   text_font_style=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_FONT_STYLE,
                   level=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_LEVEL,
                   text_align=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_ALIGN,
                   text_baseline=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_BASELINE,
                   x_offset=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_OFFSET_X,
                   y_offset=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_OFFSET_Y,
                   name=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_HEADER_LABEL_NAME)
        p.add_layout(ll)

        ll = LabelSet(x='x_lbl', y='p_num', text='p_descr', source=s,
                 text_color=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_TEXT_COLOR,
                 text_font_size=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_FONT_SIZE,
                 text_font_style=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_FONT_STYLE,
                 level=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_LEVEL,
                 text_align=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_ALIGN,
                 text_baseline=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_BASELINE,
                 x_offset=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_OFFSET_X,
                 y_offset=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_OFFSET_Y,
                 name=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_NAME_LABELSET_NAME)
        p.add_layout(ll)

        ll = LabelSet(x='x_data', y='p_num', text='p_data', source=s,
                 text_color='p_color',
                 text_font_size=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_FONT_SIZE,
                 text_font_style=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_FONT_STYLE,
                 level=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_LEVEL,
                 text_align=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_ALIGN,
                 text_baseline=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_BASELINE,
                 x_offset=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_OFFSET_X,
                 y_offset=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_OFFSET_Y,
                 name=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_NAME)
        p.add_layout(ll)

        ll = LabelSet(x='x_units', y='p_num', text='p_units', source=s,
                 text_color=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_TEXT_COLOR,
                 text_font_size=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_FONT_SIZE,
                 text_font_style=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_FONT_STYLE,
                 level=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_LEVEL,
                 text_align=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_ALIGN,
                 text_baseline=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_BASELINE,
                 x_offset=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_OFFSET_X,
                 y_offset=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_OFFSET_Y,
                 name=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_UNITS_LABELSET_NAME)
        p.add_layout(ll)

        _tooltips = """
            <div style="width: 150px">
                <span style="color: #1F77B4; font-weight: bold">Alarm High:</span>
                <span style="color: #000000;">@p_alarm_high{%+.2f}</span>
            </div>
            <div style="width: 150px">
                <span style="color: #1F77B4; font-weight: bold">Warn High :</span>
                <span style="color: #000000;">@p_warn_high{%+.2f}</span>
            </div>
            <div style="width: 150px">
                <span style="color: #1F77B4; font-weight: bold">Target :</span>
                <span style="color: #000000;">@p_target{%+.2f}</span>
            </div>
            <div style="width: 150px">
                <span style="color: #1F77B4; font-weight: bold">Warn Low  :</span>
                <span style="color: #000000;">@p_warn_low{%+.2f}</span>
            </div>
            <div style="width: 150px">
                <span style="color: #1F77B4; font-weight: bold">Alarm Low :</span>
                <span style="color: #000000;">@p_alarm_low{%+.2f}</span>
            </div>"""
        hh = HoverTool(names=[uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_CIRCLE_NAME],
                 tooltips=_tooltips,
                 formatters={"p_alarm_high": "printf",
                             "p_warn_high": "printf",
                             "p_target": "printf",
                             "p_warn_low": "printf",
                             "p_alarm_low": "printf"},
                 attachment=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_HOVER_ATTACHMENT,
                 mode=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_HOVER_MODE,
                 name=uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_METADATA_HOVER_NAME)
        p.add_tools(hh)

        self.models.sel_shot = p

    def _sel_shot_cb(self, event, sequp=True):
        """Active shot mouse-click selector callback
        """
        _methodname = self._sel_shot_cb.__name__

        # Shot parameter data
        _spdf = self.session.board.data.param.data

        # Mouse click x- coordinate
        mx = np.round(event.x).astype(int)

        # Selected-shot UI index (NB: not equal to shot number in general)
        if (mx == -1):
            s = self.uii.sel_shot
            if (s == self.uii.min_shot) and (self.uii.min_shot > 0):
                self.uii.min_shot -= 1
                self.uii.max_shot -= 1
            if (s > 0):
                s -= 1
            else:
                return
        elif (mx == uipss._FT3_ALARM_STATE_STATUS_PLOT_COLS):
            s = self.uii.sel_shot
            if (s == self.uii.max_shot) and (self.uii.max_shot < self.uii.num_shot - 1):
                self.uii.min_shot += 1
                self.uii.max_shot += 1
            if (s < self.uii.num_shot - 1):
                s += 1
        else:
            s = self.uii.min_shot + mx

        self.uii.sel_shot = s

        # Active shot parameters
        _S = _spdf.drop(columns=cfgss._FT3_ALARM_STATE_SHOT_VARIABLE)
        V = _S.values[s] * cfgp._FT3_ALARM_PARAMETER_UNIT_CONVERSIONS[:,self.unitsys]
        p_data = [uipss._FT3_ALARM_STATE_ACTIVE_SHOT_PARAM_DATA_LABELSET_FORMAT.format(v) for v in V]

        A = self.data.alarm_hist
        p_color = list(A.color[A.uiid == s])

        s = self.sources.ui_sel_param
        s.patch({"p_data": [(slice(cfgp._FT3_ALARM_PARAMETERS_NUM), p_data)],
                 "p_color": [(slice(cfgp._FT3_ALARM_PARAMETERS_NUM), p_color)]})

        # Alarm state UI window
        c = A.color[(A.uiid >= self.uii.min_shot) & (A.uiid <= self.uii.max_shot)]
        self.sources.alarm_view.patch({"color": [(slice(len(c)),c)]})

        # Active shot selector
        self.sources.ui_sel_state.patch({'x': [(0,self.uii.sel_shot - self.uii.min_shot)]})

        # UI shot indexes and shot numbers
        _s = _spdf.shot
        U = self.data.ui_shot_info
        
        U.ui_x = [mx, 0.0, self.uii.num_view - 1.0]
        try:
            U.ui_shot = ui_shot = [uipss._FT3_ALARM_STATE_SHOT_INFO_LABELSET_FORMAT.format(x) for x in [_s[self.uii.sel_shot],_s[self.uii.min_shot],_s[self.uii.max_shot]]]
        except Exception as e:
            print("")
            print("{} ERROR exception e".format(_methodname, e))
            print("{} ERROR sel_shot {}   min_shot {}   max_shot {}".format(_methodname, self.uii.sel_shot, self.uii.min_shot, self.uii.max_shot))
            print("{} ERROR len data {}   len base {}".format(_methodname, len(_spdf), len(self.session.board.data.param_data)))
            print("")
            sys.stdout.flush()

        s = self.sources.ui_shot_info
        s.patch({"ui_x": [(slice(0,3,2), [self.uii.sel_shot - self.uii.min_shot, self.uii.num_view - 1])],
                 "ui_shot": [(slice(3), ui_shot)]})

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("min shot ID:{} #:{}   max shot ID:{} #:{}   sel_shot ID:{} #:{}".
                  format(self.uii.min_shot, _s[self.uii.min_shot],
                         self.uii.max_shot, _s[self.uii.max_shot],
                         self.uii.sel_shot, _s[self.uii.sel_shot]))
            sys.stdout.flush()

        if sequp:
            # Update selected-shot plots and events
            sel_shot = _s[self.uii.sel_shot]
            self.session.shot.update(sel_shot=sel_shot)
