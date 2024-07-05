#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 position- and time-based shot trajectories
"""
import sys

from functools import partial
from threading import Lock
from tornado import gen

import pandas as pd

from dataclasses import dataclass
from enum import IntEnum,unique

from bokeh.models import ColumnDataSource, HoverTool
from bokeh.models import DataTable, TableColumn, DateFormatter

from bokeh.models import Div, Button, Select, CheckboxGroup

from bokeh.models.tools import CustomJSHover

from bokeh.plotting import figure
from bokeh.layouts import row, column, gridplot

import shot.uiprop as uips

import util.util as util
import units.units as units


@dataclass
class Data:
    """FasTrak3 shot data and data for UIs
    """
    ui_meta  : pd.DataFrame # Active-shot metadata
    ui_shot_p: pd.DataFrame # Active-shot position-based data
    ui_shot_t: pd.DataFrame # Active-shot time-based data
    ui_events: pd.DataFrame # Active-shot events
    ui_ref_p : pd.DataFrame # Reference shot position-based data
    ui_ref_t : pd.DataFrame # Reference shot time-based data

@dataclass
class Sources:
    """Bokeh model column data source interfaces to data for UIs
    """
    ui_shot_p: ColumnDataSource
    ui_shot_t: ColumnDataSource
    ui_events: ColumnDataSource
    ui_ref_p : ColumnDataSource
    ui_ref_t : ColumnDataSource


@dataclass
class Layout:
    ui_conn  : row
    ui_info  : row
    ui_shot  : gridplot
    ui_events: column
    ui_ref   : row

@dataclass
class UIConn:
    board: Select
    conn : Button

@dataclass
class UIInfo:
    shot: Div

@dataclass
class UIShot:
    plot_ul: figure
    plot_ur: figure
    plot_ll: figure
    plot_lr: figure

@dataclass
class UIEvents:
    header: Div
    table : DataTable

@dataclass
class UIRef:
    header: Div
    view  : CheckboxGroup
    save  : Button

@dataclass
class Models:
    layout   : Layout
    ui_conn  : UIConn   # FasTrak3 board connector
    ui_info  : UIInfo   # Active shot information
    ui_shot  : UIShot   # Active-shot plots
    ui_events: UIEvents # Active-shot events
    ui_ref   : UIRef    # Reference shot UI controls
    ln_ref   : list     # Reference shot trajectory / quad-chart lines


@unique
class ModelLayout(IntEnum):
    default = 0


class Shot(object):
    def __init__(self, session=None, verbose=util.VerboseLevel.info):
        """Initialize FasTrak3 active-shot interface
        """
        self.session = session
        self.verbose = verbose

        self.unitsys = self.session.unitsys

        self.sel_shot = None

        self.data = Data(ui_meta=pd.DataFrame(),
                         ui_shot_p=pd.DataFrame(),
                         ui_shot_t=pd.DataFrame(),
                         ui_events=pd.DataFrame(),
                         ui_ref_p=pd.DataFrame(),
                         ui_ref_t=pd.DataFrame())

        self.sources = Sources(ui_shot_p=None,
                               ui_shot_t=None,
                               ui_events=None,
                               ui_ref_p=None,
                               ui_ref_t=None)

        self.mutexes = util.Mutexes(meta=Lock(),
                                    shot=Lock(),
                                    events=Lock())

        _layout = Layout(ui_conn=None,
                         ui_info=None,
                         ui_shot=None,
                         ui_events=None,
                         ui_ref=None)
        _ui_conn = UIConn(board=None,
                          conn=None)
        _ui_info = UIInfo(shot=None)
        _ui_shot = UIShot(plot_ul=None,
                          plot_ur=None,
                          plot_ll=None,
                          plot_lr=None)
        _ui_events= UIEvents(header=None,
                             table=None)
        _ui_ref = UIRef(header=None,
                        view=None,
                        save=None)
        self.models = Models(layout=_layout,
                             ui_conn=_ui_conn,
                             ui_info=_ui_info,
                             ui_shot=_ui_shot,
                             ui_events=_ui_events,
                             ui_ref=_ui_ref,
                             ln_ref=[])

    def layout(self, mode=ModelLayout.default):
        """UI layout
        """
        _methodname = self.layout.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("FasTrak3 active-shot layout")
            sys.stdout.flush()

        if mode == ModelLayout.default:
            self._make_info()
            self._make_shot()
            self._make_events()
            self._make_ref()

            #self.layout.ui_conn = row(self.models.ui_conn.board, self.models.ui_conn.conn)
            self.models.layout.ui_info = row(self.models.ui_info.shot)

            pl = []
            pl += [self.models.ui_shot.plot_ul]
            pl += [self.models.ui_shot.plot_ur]
            pl += [self.models.ui_shot.plot_ll]
            pl += [self.models.ui_shot.plot_lr]
            self.models.layout.ui_shot = gridplot(pl, ncols=2)

            self.models.layout.ui_events = column([self.models.ui_events.header,
                                                   self.models.ui_events.table])

            self.models.layout.ui_ref = row([self.models.ui_ref.header,
                                             self.models.ui_ref.view,
                                             self.models.ui_ref.save])

        else:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("unknown UI layout {}".format(mode))
                sys.stdout.flush()
            return

    def update(self, sel_shot=None):
        """Schedule active-shot plots and events
        """
        _methodname = self.update.__name__

        # Profile/debug
        if self.verbose >= util.VerboseLevel.profile:
            t0 = util._FT3_UTIL_NOW_TS()

        # Board data reference
        Bd = self.session.board.data

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("schedule active-shot plots and events (#:{})".format(sel_shot))
            sys.stdout.flush()

        if sel_shot is None:
            # Maximum shot as selected (active) shot
            ii = self.sel_shot = Bd.index.max()
        elif self.sel_shot != sel_shot:
            # Caller-provided selected (active) shot
            ii = self.sel_shot = sel_shot
        else:
            # Selected shot already active
            return


        # Active-shot metadata
        self.mutexes.meta.acquire()
        try:
            data = Bd.meta.data
            dfmeta = data[data.shot==ii]
            dfmeta.reset_index(drop=True, inplace=True)
            self.data.ui_meta = dfmeta
        except Exception as e:
            self.data.ui_meta = pd.DataFrame()
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("active-shot metadata exception e {}".format(e))
                sys.stdout.flush()
        self.mutexes.meta.release()


        # Active-shot shot data
        self.mutexes.shot.acquire()
        try:
            data = Bd.shot.data[ii]
            dfp = data[(data.type=='P')]
            dft = data[(data.type=='T')]

            # Drop invalid first sample of datasets owing to one-based start
            # indexes of position- and time- sampled data in the FasTrak2(3)
            # firmware.
            dfp = dfp.drop(dfp.head(2).index)
            dft = dft.drop(dft.head(2).index)

            dfp.reset_index(drop=True, inplace=True)
            dft.reset_index(drop=True, inplace=True)
        
            self.data.ui_shot_p = dfp
            self.data.ui_shot_t = dft

            # Drop invalid first sample of datasets owing to one-based start
            # indexes of position- and time- sampled data in the FasTrak2(3)
            # firmware.
            dfp = dfp.drop(dfp.head(2).index)
            dft = dft.drop(dft.head(2).index)

            dfp.reset_index(drop=True, inplace=True)
            dft.reset_index(drop=True, inplace=True)
        
            self.data.ui_shot_p = dfp
            self.data.ui_shot_t = dft
        except Exception as e:
            self.data.ui_shot_p = pd.DataFrame()
            self.data.ui_shot_t = pd.DataFrame()
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("active-shot shot data exception e {}".format(e))
                sys.stdout.flush()
        self.mutexes.shot.release()


        # Active-shot events
        self.mutexes.events.acquire()
        try:
            data = Bd.events.data
            dfev = data[ii]
            dfev.reset_index(drop=True, inplace=True)
            self.data.ui_events = dfev
        except Exception as e:
            self.data.ui_events = pd.DataFrame()
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("active-shot events exception e {}".format(e))
                sys.stdout.flush()
        self.mutexes.events.release()


        # Profile/debug
        if self.verbose >= util.VerboseLevel.profile:
            tf = util._FT3_UTIL_NOW_TS()
            util._FT3_UTIL_VERBOSE_PROFILE_WITH_TS(_methodname)
            print("mutex-protected shot-data acq profile  {:.3f}s".format((tf-t0).total_seconds()))
            sys.stdout.flush()


        # Schedule UI updates
        _doc = self.models.ui_info.shot.document
        _doc.add_next_tick_callback(partial(self._threadsafe_update_cb))


        # Profile/debug
        if self.verbose >= util.VerboseLevel.profile:
            tf = util._FT3_UTIL_NOW_TS()
            util._FT3_UTIL_VERBOSE_PROFILE_WITH_TS(_methodname)
            print("shot-module total profile              {:.3f}s".format((tf-t0).total_seconds()))
            print("")
            sys.stdout.flush()

    @gen.coroutine
    def _threadsafe_update_cb(self):
        """Threadsafe shot-data callback
        """
        _methodname = self._threadsafe_update_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("plot active-shot trajectories and list active-shot events")
            sys.stdout.flush()


        # Active-shot metadata
        self.mutexes.meta.acquire()
        try:
            _dfmeta = self.data.ui_meta.copy()
        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("active-shot metadata exception e {}".format(e))
                sys.stdout.flush()
        self.mutexes.meta.release()

        m = self.models.ui_info.shot
        if _dfmeta.empty:
            m.text = uips._FT3_SHOT_SEL_SHOT_DIV_TEXT_INIT
        else:
            m.text = uips._FT3_SHOT_SEL_SHOT_DIV_TEXT(_dfmeta.shot, _dfmeta.t0, _dfmeta.t1)

        # Active-shot shot data
        self.mutexes.shot.acquire()
        try:
            _dfp = self.data.ui_shot_p.copy()
            _dft = self.data.ui_shot_t.copy()
        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("active-shot shot data exception e {}".format(e))
                sys.stdout.flush()
        self.mutexes.shot.release()

        _Sp = self.sources.ui_shot_p
        _Sp.data = dict(ColumnDataSource(_dfp).data)

        _St = self.sources.ui_shot_t
        _St.data = dict(ColumnDataSource(_dft).data)

        # Quad-plot ranges
        if self.unitsys == units.UnitSystem.si:
            self.models.ui_shot.plot_ul.x_range.end = _dfp.pos.max()
        elif self.unitsys == units.UnitSystem.bg:
            self.models.ui_shot.plot_ul.x_range.end = _dfp.pos.max() * units._FT3_UNITS_MM_TO_IN
        self.models.ui_shot.plot_ur.x_range.end = _dft.t.max()

        # Active-shot events
        self.mutexes.events.acquire()
        try:
            _dfev = self.data.ui_events.copy()
        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("active-shot events exception e {}".format(e))
                sys.stdout.flush()
        self.mutexes.events.release()

        _Sev = self.sources.ui_events
        _Sev.data = dict(ColumnDataSource(_dfev).data)


        # Enable
        # Save selected shot as reference shot
        self.models.ui_ref.save.disabled = False
        self.models.ui_ref.save.button_type = uips._FT3_SHOT_REF_SAVE_BUTTON_TYPE_ENABLED

    def _make_info(self):
        """Make active-shot information 
        """
        _methodname= self._make_info.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("make active-shot information UI Bokeh models")
            sys.stdout.flush()

        h = Div(text=uips._FT3_SHOT_SEL_SHOT_DIV_TEXT_INIT,
                style=uips._FT3_SHOT_SEL_SHOT_DIV_STYLE,
                width=uips._FT3_SHOT_SEL_SHOT_DIV_PX_W,
                height=uips._FT3_SHOT_SEL_SHOT_DIV_PX_H,
                margin=uips._FT3_SHOT_SEL_SHOT_DIV_MARGIN,
                name=uips._FT3_SHOT_SEL_SHOT_DIV_NAME)
        
        self.models.ui_info.shot = h
        
    def _make_shot(self):
        """Make FasTrak3 shot quad plot
        """
        _methodname = self._make_shot.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("make FasTrak3 shot quad plot")
            sys.stdout.flush()
        # Shot quad-plot
        N = 4

        _w = uips._FT3_SHOT_QUAD_PLOT_ARRAY_PX_W
        _h = uips._FT3_SHOT_QUAD_PLOT_ARRAY_PX_H
        _b = uips._FT3_SHOT_QUAD_PLOT_ARRAY_PX_BORDER

        _lt = uips._FT3_SHOT_QUAD_PLOT_ARRAY_TOOLBAR_LOC
        _lx = uips._FT3_SHOT_QUAD_PLOT_ARRAY_X_AXIS_LOC
        _ly = uips._FT3_SHOT_QUAD_PLOT_ARRAY_Y_AXIS_LOC

        # TODO ... revisit whether to include explicit x- and y- ranges
        # 2019-09-09: x-range set at figure creation to avoid race condition
        #             if plot data are updated and explicit limits are also
        #             required to avoid perceived "missing" data in quad-plot
        #             at lefthand (position-based) and righthand (time-based)
        #             boundary.
        #             See also https://github.com/bokeh/bokeh/issues/7281
        _xr = uips._FT3_SHOT_QUAD_PLOT_ARRAY_X_RANGE
        #_yr = (None,None)

        _ttl = uips._FT3_SHOT_QUAD_PLOT_ARRAY_TITLE
        _names = uips._FT3_SHOT_QUAD_PLOT_ARRAY_NAME

        _rgb = uips._FT3_SHOT_QUAD_PLOT_ARRAY_BACKGROUND

        if self.unitsys == units.UnitSystem.bg:
            _llx = uips._FT3_SHOT_QUAD_PLOT_ARRAY_X_AXIS_LABEL_BG
            _lly = uips._FT3_SHOT_QUAD_PLOT_ARRAY_Y_AXIS_LABEL_BG
        elif self.unitsys == units.UnitSystem.si:
            _llx = uips._FT3_SHOT_QUAD_PLOT_ARRAY_X_AXIS_LABEL_SI
            _lly = uips._FT3_SHOT_QUAD_PLOT_ARRAY_Y_AXIS_LABEL_SI
        elif self.verbose >= util.VerboseLevel.warn:
            util._FT3_UTIL_VERBOSE_WARN_WITH_TS(_methodname)
            print("unknown unit system {}".format(self.unitsys))
            sys.stdout.flush()

        # TODO ... revisit whether to include explicit x- and y- ranges
        pl = [figure(plot_width=_w[i], plot_height=_h[i], min_border=_b[i],
                     toolbar_location=_lt[i], x_axis_location=_lx[i], y_axis_location=_ly[i],
                     x_range=_xr[i], #y_range=_yr[i],
                     title=_ttl[i], name=_names[i]) for i in range(N)]

        # Plot-range links
        pl[1].y_range = pl[0].y_range
        pl[2].x_range = pl[0].x_range
        pl[3].x_range = pl[1].x_range

        for i,p in enumerate(pl):
            p.background_fill_color = _rgb[i]
            p.xaxis.axis_label = _llx[i]
            p.yaxis.axis_label = _lly[i]

        self.models.ui_shot.plot_ul = pl[0]
        self.models.ui_shot.plot_ur = pl[1]
        self.models.ui_shot.plot_ll = pl[2]
        self.models.ui_shot.plot_lr = pl[3]

        # Placeholder position-based and time-based data
        _dfp = self.data.ui_shot_p = pd.DataFrame(data=None, columns=("pos","press_head","press_rod","vel"))
        _dft = self.data.ui_shot_t = pd.DataFrame(data=None, columns=("t","press_head","press_rod","pos"))

        _Sp = self.sources.ui_shot_p = ColumnDataSource(_dfp)
        _St = self.sources.ui_shot_t = ColumnDataSource(_dft)

        _dfp_ref = self.data.ui_ref_p = pd.DataFrame(data=None, columns=("pos","press_head","press_rod","vel"))
        _dft_ref = self.data.ui_ref_t = pd.DataFrame(data=None, columns=("t","press_head","press_rod","pos"))

        _Sp_ref = self.sources.ui_ref_p = ColumnDataSource(_dfp_ref)
        _St_ref = self.sources.ui_ref_t = ColumnDataSource(_dft_ref)


        # Reference-shot trajectory quad-chart lines
        ln = self.models.ln_ref = []


        # Shot-plot variables incl. unit system conversions if req'd
        # Tooltips per unit system
        if self.unitsys == units.UnitSystem.bg:
            _press_head_ln = uips._FT3_SHOT_LINE_PRESS_HEAD_BG
            _press_rod_ln = uips._FT3_SHOT_LINE_PRESS_ROD_BG
            _pos_ln = uips._FT3_SHOT_LINE_POS_BG
            _vel_ln = uips._FT3_SHOT_LINE_VEL_BG

            _pos_press_head_tt = uips._FT3_SHOT_POS_PRESS_HEAD_HOVER_TOOLTIPS_BG
            _pos_press_rod_tt = uips._FT3_SHOT_POS_PRESS_ROD_HOVER_TOOLTIPS_BG
            _time_press_head_tt = uips._FT3_SHOT_TIME_PRESS_HEAD_HOVER_TOOLTIPS_BG
            _time_press_rod_tt = uips._FT3_SHOT_TIME_PRESS_ROD_HOVER_TOOLTIPS_BG
            _pos_vel_tt = uips._FT3_SHOT_POS_VEL_HOVER_TOOLTIPS_BG
            _time_pos_tt = uips._FT3_SHOT_TIME_POS_HOVER_TOOLTIPS_BG
        elif self.unitsys == units.UnitSystem.si:
            _press_head_ln = uips._FT3_SHOT_LINE_PRESS_HEAD_SI
            _press_rod_ln = uips._FT3_SHOT_LINE_PRESS_ROD_SI
            _pos_ln = uips._FT3_SHOT_LINE_POS_SI
            _vel_ln = uips._FT3_SHOT_LINE_VEL_SI

            _pos_press_head_tt = uips._FT3_SHOT_POS_PRESS_HEAD_HOVER_TOOLTIPS_SI
            _pos_press_rod_tt = uips._FT3_SHOT_POS_PRESS_ROD_HOVER_TOOLTIPS_SI
            _time_press_head_tt = uips._FT3_SHOT_TIME_PRESS_HEAD_HOVER_TOOLTIPS_SI
            _time_press_rod_tt = uips._FT3_SHOT_TIME_PRESS_ROD_HOVER_TOOLTIPS_SI
            _pos_vel_tt = uips._FT3_SHOT_POS_VEL_HOVER_TOOLTIPS_SI
            _time_pos_tt = uips._FT3_SHOT_TIME_POS_HOVER_TOOLTIPS_SI
        elif self.verbose >= util.VerboseLevel.warn:
            util._FT3_UTIL_VERBOSE_WARN_WITH_TS(_methodname)
            print("unknown unit system {}".format(self.unitsys))
            sys.stdout.flush()


        # Quad-plot upper-left
        # Head pressure vs position
        # Rod pressuress vs position
        p = pl[0]
        p.line(x=_pos_ln, y=_press_head_ln, source=_Sp,
               line_alpha=uips._FT3_SHOT_POS_PRESS_HEAD_LINE_ALPHA,
               line_width=uips._FT3_SHOT_POS_PRESS_HEAD_LINE_WIDTH,
               line_color=uips._FT3_SHOT_POS_PRESS_HEAD_LINE_COLOR,
               name=uips._FT3_SHOT_POS_PRESS_HEAD_LINE_NAME)
        ln += [p.line(x=_pos_ln, y=_press_head_ln, source=_Sp_ref,
                      line_alpha=uips._FT3_REF_POS_PRESS_HEAD_LINE_ALPHA,
                      line_width=uips._FT3_REF_POS_PRESS_HEAD_LINE_WIDTH,
                      line_color=uips._FT3_REF_POS_PRESS_HEAD_LINE_COLOR,
                      name=uips._FT3_REF_POS_PRESS_HEAD_LINE_NAME)]

        _pos_press_head_fmt = {'pos': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_X),
                               'press_head': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_Y)}
        p.add_tools(HoverTool(names=uips._FT3_SHOT_POS_PRESS_HEAD_HOVER_NAMES,
                              tooltips=_pos_press_head_tt,
                              formatters=_pos_press_head_fmt,
                              mode=uips._FT3_SHOT_POS_PRESS_HEAD_HOVER_MODE))

        p.line(x=_pos_ln, y=_press_rod_ln, source=_Sp,
               line_alpha=uips._FT3_SHOT_POS_PRESS_ROD_LINE_ALPHA,
               line_width=uips._FT3_SHOT_POS_PRESS_ROD_LINE_WIDTH,
               line_color=uips._FT3_SHOT_POS_PRESS_ROD_LINE_COLOR,
               name=uips._FT3_SHOT_POS_PRESS_ROD_LINE_NAME)
        ln += [p.line(x=_pos_ln, y=_press_rod_ln, source=_Sp_ref,
                      line_alpha=uips._FT3_REF_POS_PRESS_ROD_LINE_ALPHA,
                      line_width=uips._FT3_REF_POS_PRESS_ROD_LINE_WIDTH,
                      line_color=uips._FT3_REF_POS_PRESS_ROD_LINE_COLOR,
                      name=uips._FT3_REF_POS_PRESS_ROD_LINE_NAME)]

        _pos_press_rod_fmt = {'pos': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_X),
                              'press_rod': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_Y)}
        p.add_tools(HoverTool(names=uips._FT3_SHOT_POS_PRESS_ROD_HOVER_NAMES,
                              tooltips=_pos_press_rod_tt,
                              formatters=_pos_press_rod_fmt,
                              mode=uips._FT3_SHOT_POS_PRESS_ROD_HOVER_MODE))

        # Quad-plot upper right
        # Head pressure vs time
        # Rod pressuress vs time
        p = pl[1]
        p.line(x="t", y=_press_head_ln, source=_St,
               line_alpha=uips._FT3_SHOT_TIME_PRESS_HEAD_LINE_ALPHA,
               line_width=uips._FT3_SHOT_TIME_PRESS_HEAD_LINE_WIDTH,
               line_color=uips._FT3_SHOT_TIME_PRESS_HEAD_LINE_COLOR,
               name=uips._FT3_SHOT_TIME_PRESS_HEAD_LINE_NAME)
        ln += [p.line(x="t", y=_press_head_ln, source=_St_ref,
                      line_alpha=uips._FT3_REF_TIME_PRESS_HEAD_LINE_ALPHA,
                      line_width=uips._FT3_REF_TIME_PRESS_HEAD_LINE_WIDTH,
                      line_color=uips._FT3_REF_TIME_PRESS_HEAD_LINE_COLOR,
                      name=uips._FT3_REF_TIME_PRESS_HEAD_LINE_NAME)]

        _time_press_head_fmt = {'t': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_X),
                                'press_head': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_Y)}
        p.add_tools(HoverTool(names=uips._FT3_SHOT_TIME_PRESS_HEAD_HOVER_NAMES,
                              tooltips=_time_press_head_tt,
                              formatters=_time_press_head_fmt,
                              mode=uips._FT3_SHOT_TIME_PRESS_HEAD_HOVER_MODE))

        p.line(x="t", y=_press_rod_ln, source=_St,
               line_alpha=uips._FT3_SHOT_TIME_PRESS_ROD_LINE_ALPHA,
               line_width=uips._FT3_SHOT_TIME_PRESS_ROD_LINE_WIDTH,
               line_color=uips._FT3_SHOT_TIME_PRESS_ROD_LINE_COLOR,
               name=uips._FT3_SHOT_TIME_PRESS_ROD_LINE_NAME)
        ln += [p.line(x="t", y=_press_rod_ln, source=_St_ref,
                      line_alpha=uips._FT3_REF_TIME_PRESS_ROD_LINE_ALPHA,
                      line_width=uips._FT3_REF_TIME_PRESS_ROD_LINE_WIDTH,
                      line_color=uips._FT3_REF_TIME_PRESS_ROD_LINE_COLOR,
                      name=uips._FT3_REF_TIME_PRESS_ROD_LINE_NAME)]

        _time_press_rod_fmt = {'t': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_X),
                               'press_rod': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_Y)}
        p.add_tools(HoverTool(names=uips._FT3_SHOT_TIME_PRESS_ROD_HOVER_NAMES,
                              tooltips=_time_press_rod_tt,
                              formatters=_time_press_rod_fmt,
                              mode=uips._FT3_SHOT_TIME_PRESS_ROD_HOVER_MODE))

        # Quad-plot lower-left
        # Velocity vs position
        p = pl[2]
        p.line(x=_pos_ln, y=_vel_ln, source=_Sp,
               line_alpha=uips._FT3_SHOT_POS_VEL_LINE_ALPHA,
               line_width=uips._FT3_SHOT_POS_VEL_LINE_WIDTH,
               line_color=uips._FT3_SHOT_POS_VEL_LINE_COLOR,
               name=uips._FT3_SHOT_POS_VEL_LINE_NAME)
        ln += [p.line(x=_pos_ln, y=_vel_ln, source=_Sp_ref,
                      line_alpha=uips._FT3_REF_POS_VEL_LINE_ALPHA,
                      line_width=uips._FT3_REF_POS_VEL_LINE_WIDTH,
                      line_color=uips._FT3_REF_POS_VEL_LINE_COLOR,
                      name=uips._FT3_REF_POS_VEL_LINE_NAME)]
   
        _pos_vel_fmt = {'pos': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_X),
                        'vel': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_Y)}
        p.add_tools(HoverTool(names=uips._FT3_SHOT_POS_VEL_HOVER_NAMES,
                              tooltips=_pos_vel_tt,
                              formatters=_pos_vel_fmt,
                              mode=uips._FT3_SHOT_POS_VEL_HOVER_MODE))

        # Quad-plot lower right
        # Position vs time
        p = pl[3]
        p.line(x="t", y=_pos_ln, source=_St,
               line_alpha=uips._FT3_SHOT_TIME_POS_LINE_ALPHA,
               line_width=uips._FT3_SHOT_TIME_POS_LINE_WIDTH,
               line_color=uips._FT3_SHOT_TIME_POS_LINE_COLOR,
               name=uips._FT3_SHOT_TIME_POS_LINE_NAME)
        ln += [p.line(x="t", y=_pos_ln, source=_St_ref,
                      line_alpha=uips._FT3_REF_TIME_POS_LINE_ALPHA,
                      line_width=uips._FT3_REF_TIME_POS_LINE_WIDTH,
                      line_color=uips._FT3_REF_TIME_POS_LINE_COLOR,
                      name=uips._FT3_REF_TIME_POS_LINE_NAME)]

        _time_pos_fmt = {'t': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_X),
                         'pos': CustomJSHover(code=uips._FT3_JS_HOVER_CODE_Y)}
        p.add_tools(HoverTool(names=uips._FT3_SHOT_TIME_POS_HOVER_NAMES,
                              tooltips=_time_pos_tt,
                              formatters=_time_pos_fmt,
                              mode=uips._FT3_SHOT_TIME_POS_HOVER_MODE))
       
    def _make_events(self):
        """Make FasTrak3 shot events table
        """
        _methodname = self._make_events.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("make FasTrak3 events table")
            sys.stdout.flush()

        # Shot events table header
        h = Div(text=uips._FT3_SHOT_EVENTS_TABLE_HEADER_DIV_TEXT,
                style=uips._FT3_SHOT_EVENTS_TABLE_HEADER_DIV_STYLE,
                width=uips._FT3_SHOT_EVENTS_TABLE_HEADER_DIV_PX_W,
                height=uips._FT3_SHOT_EVENTS_TABLE_HEADER_DIV_PX_H,
                margin=uips._FT3_SHOT_EVENTS_TABLE_HEADER_DIV_MARGIN,
                name=uips._FT3_SHOT_EVENTS_TABLE_HEADER_DIV_NAME)
        
        # Shot events table
        _fields = uips._FT3_SHOT_EVENTS_TABLE_FIELDS
        _titles = uips._FT3_SHOT_EVENTS_TABLE_TITLES
        _widths = uips._FT3_SHOT_EVENTS_TABLE_WIDTHS
        _format = uips._FT3_SHOT_EVENTS_TABLE_FORMAT

        _columns = [TableColumn(field=f, title=_titles[k], width=_widths[k]) for k,f in enumerate(_fields)]
        for k,fmt in enumerate(_format):
            if fmt is not None:
                _columns[k].formatter = DateFormatter(format=fmt)

        ds = self.data.ui_events = pd.DataFrame(data=None, columns=_fields)
        self.sources.ui_events = ColumnDataSource(ds)

        p = DataTable(source=self.sources.ui_events, columns=_columns,
                      reorderable=uips._FT3_SHOT_EVENTS_TABLE_REORDERABLE,
                      sortable=uips._FT3_SHOT_EVENTS_TABLE_SORTABLE,
                      width=uips._FT3_SHOT_EVENTS_TABLE_PX_W,
                      height=uips._FT3_SHOT_EVENTS_TABLE_PX_H,
                      margin=uips._FT3_SHOT_EVENTS_TABLE_MARGIN,
                      row_height=uips._FT3_SHOT_EVENTS_TABLE_PX_ROW,
                      index_header=uips._FT3_SHOT_EVENTS_TABLE_INDEX_HEADER,
                      index_position=uips._FT3_SHOT_EVENTS_TABLE_INDEX_POSITION,
                      name=uips._FT3_SHOT_EVENTS_TABLE_NAME)

        self.models.ui_events.header = h
        self.models.ui_events.table = p

    def _make_ref(self):
        """Make reference-shot controls
        """
        _methodname = self._make_ref.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("make FasTrak3 reference-shot controls")
            sys.stdout.flush()

        # Reference shot header
        h = Div(text=uips._FT3_SHOT_REF_HEADER_DIV_TEXT,
                style=uips._FT3_SHOT_REF_HEADER_DIV_STYLE,
                width=uips._FT3_SHOT_REF_HEADER_DIV_PX_W,
                height=uips._FT3_SHOT_REF_HEADER_DIV_PX_H,
                margin=uips._FT3_SHOT_REF_HEADER_DIV_MARGIN,
                name=uips._FT3_SHOT_REF_HEADER_DIV_NAME)

        # View checkbox (reference shot trajectories)
        x = CheckboxGroup(labels=uips._FT3_SHOT_REF_VIEW_CHECKBOX_LABELS,
                          active=uips._FT3_SHOT_REF_VIEW_CHECKBOX_ACTIVE,
                          width=uips._FT3_SHOT_REF_VIEW_CHECKBOX_PX_W,
                          height=uips._FT3_SHOT_REF_VIEW_CHECKBOX_PX_H,
                          margin=uips._FT3_SHOT_REF_VIEW_CHECKBOX_MARGIN,
                          name=uips._FT3_SHOT_REF_VIEW_CHECKBOX_NAME)
        x.on_click(self._ref_view_cb)

        # Save button  (active-shot as reference)
        b = Button(label=uips._FT3_SHOT_REF_SAVE_BUTTON_LABEL,
                   button_type=uips._FT3_SHOT_REF_SAVE_BUTTON_TYPE_DISABLED,
                   disabled=uips._FT3_SHOT_REF_SAVE_BUTTON_DISABLED_INIT,
                   width=uips._FT3_SHOT_REF_SAVE_BUTTON_PX_W,
                   height=uips._FT3_SHOT_REF_SAVE_BUTTON_PX_H,
                   margin=uips._FT3_SHOT_REF_SAVE_BUTTON_MARGIN,
                   name=uips._FT3_SHOT_REF_SAVE_BUTTON_NAME)
        b.on_click(self._ref_save_cb)

        self.models.ui_ref.header = h
        self.models.ui_ref.view = x
        self.models.ui_ref.save = b

    def _ref_view_cb(self, active):
        """Reference-shot view callback
        """
        _methodname = self._ref_view_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("reference-shot view {}".format(active))
            sys.stdout.flush()

        # Reference shot data and sources
        _data = self.session.ref.data
        _dfp = _data.shot[_data.shot.type == "P"]
        _dft = _data.shot[_data.shot.type == "T"]

        # Drop invalid first sample of datasets owing to one-based start 
        # indexes of position- and time- sampled data in the FasTrak2(3)
        # firmware.

        _dfp = _dfp.drop(_dfp.head(2).index)
        _dft = _dft.drop(_dft.head(2).index)

        _dfp.reset_index(drop=True, inplace=True)
        _dft.reset_index(drop=True, inplace=True)

        _Sp_ref = self.sources.ui_ref_p
        _Sp_ref.data = dict(ColumnDataSource(_dfp).data)

        _St_ref = self.sources.ui_ref_t
        _St_ref.data = dict(ColumnDataSource(_dft).data)

        
        if active:
            _visible = True
        else:
            _visible = False
            
        for m in self.models.ln_ref:
            m.visible = _visible

    def _ref_save_cb(self):
        """Reference-shot save callback
        """
        _methodname = self._ref_save_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("reference-shot save")
            sys.stdout.flush()

        # Board data reference
        Bd = self.session.board.data

        # Disable
        # Save selected (active) shot as reference shot
        #self.models.ui_ref.save.disabled = False
        #self.models.ui_ref.save.button_type = uips._FT3_SHOT_REF_SAVE_BUTTON_TYPE_DISABLED

        ii = self.sel_shot

        _R = self.session.ref

        # Selected-shot metadata
        self.mutexes.meta.acquire()
        try:
            data = Bd.meta.data
            _R._data.meta = data[data.shot==ii]
        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("active-shot metadata exception e {}".format(e))
                sys.stdout.flush()
        self.mutexes.meta.release()

        # Selected-shot shot data
        self.mutexes.shot.acquire()
        try:
            data = Bd.shot.data
            _R._data.shot = data[ii]
        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("active-shot shot data exception e {}".format(e))
                sys.stdout.flush()
        self.mutexes.shot.release()

        # Active-shot events
        self.mutexes.events.acquire()
        try:
            data = Bd.events.data
            _R._data.events = data[ii]
        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("active-shot events exception e {}".format(e))
                sys.stdout.flush()
        self.mutexes.events.release()

        # Save reference shot to SQL
        _R.write()
