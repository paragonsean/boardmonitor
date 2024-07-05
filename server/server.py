#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 web interface application
"""
import sys

from dataclasses import dataclass

from bokeh.plotting import curdoc
from bokeh.models import Toggle, Spacer, Div, Panel, Tabs

from bokeh.layouts import row, column

import machine.machine as machine
import part.part as part

import ad.ad as ad

import shot.shot as shot
import ref.ref as ref

import state.state as state
import alarm.alarm as alarm
import alert.alert as alert

import board.board as board

import server.uiprop as uips
import tcpip.config as cfgt

import util.util as util
import units.units as units

@dataclass
class Models:
    stream: Toggle
    spacer: Spacer
    logo  : Div

class Session():
    def __init__(self, names=None, ips=None, unitsys=units.UnitSystem.bg, verbose=util.VerboseLevel.info):
        """Initialize FasTrak3 web interface application
           (as a bokeh server session)
        """
        self.unitsys = unitsys
        self.verbose = verbose

        # Server session document
        D = self.document = curdoc()
        D.title = uips._FT3_SERVER_APP_TITLE

        # TODO ... Vectorize to support multiple FasTrak3 boards per FasTrak3 web server
        if names is not None and ips is not None:
            self.board = D.session_context.board = board.Board(session=self, name=names[0], ip=ips[0], unitsys=unitsys, verbose=verbose)
        else:
            self.board = D.session_context.board = board.Board(session=self, unitsys=unitsys, verbose=verbose)

        # TCP/IP heartbeat
        self.heartbeat_cb = D.add_periodic_callback(callback=self.board.client._heartbeat,
                                                    period_milliseconds=cfgt._FT3_TCPIP_HEARTBEAT_PERIOD_MS)

        self.machine = machine.Machine(session=self, verbose=verbose)
        self.part = part.Part(session=self, verbose=verbose)

        self.shot  = shot.Shot(session=self, verbose=verbose)   # FasTrak3 shots
        self.ref   = ref.Ref(session=self, verbose=verbose)     # FasTrak3 reference shot
        self.state = state.State(session=self, verbose=verbose) # Alarm-states
        self.alarm = alarm.Alarm(session=self, verbose=verbose) # Alarm database
        self.alert = alert.Alert(session=self, verbose=verbose) # E-mail/SMS alerts

        # Session UI models
        self._make_ui_models()

        # UI layout
        S = self.shot
        S.layout()

        SS = self.state
        SS.layout()

        P = self.part.param
        P.layout()

        _ch = [SS.models.layout, P.models.layout]
        _pl = [Panel(child=_ch[i], title=t) for i,t in enumerate(uips._FT3_SERVER_PANEL_TITLES)]

        m0 = row(S.models.layout.ui_info, S.models.layout.ui_ref, self.models.stream)
        m1 = column(self.models.spacer, m0)
        m2 = self.models.logo

        D.add_root(row(m1, m2))
        D.add_root(row(S.models.layout.ui_events, S.models.layout.ui_shot))
        D.add_root(Tabs(tabs=_pl))

        # Activate board
        # NB: Begins data flow to UIs
        self.board.active = True

    def _make_ui_models(self):
        """Make server UI models
        """
        self.models = Models(stream=None, spacer=None, logo=None)

        b = Toggle(label=uips._FT3_SERVER_STREAM_BUTTON_ACTIVE_LABEL,
                   button_type=uips._FT3_SERVER_STREAM_BUTTON_ACTIVE_TYPE,
                   active=True,
                   width=uips._FT3_SERVER_STREAM_BUTTON_PX_W,
                   height=uips._FT3_SERVER_STREAM_BUTTON_PX_H,
                   margin=uips._FT3_SERVER_STREAM_BUTTON_MARGIN,
                   name=uips._FT3_SERVER_STREAM_BUTTON_NAME)
        b.on_click(self._stream_cb)
        self.models.stream = b

        h = Spacer(width=uips._FT3_SERVER_BANNER_SPACER_PX_W,
                   height=uips._FT3_SERVER_BANNER_SPACER_PX_H,
                   margin=uips._FT3_SERVER_BANNER_SPACER_MARGIN,
                   name=uips._FT3_SERVER_BANNER_SPACER_NAME)
        self.models.spacer = h

        ll = Div(text=uips._FT3_SERVER_VISITRAK_LOGO_DIV_TEXT,
                 width=uips._FT3_SERVER_VISITRAK_LOGO_DIV_PX_W,
                 height=uips._FT3_SERVER_VISITRAK_LOGO_DIV_PX_H,
                 margin=uips._FT3_SERVER_VISITRAK_LOGO_DIV_MARGIN,
                 name=uips._FT3_SERVER_VISITRAK_LOGO_DIV_NAME)
        self.models.logo = ll

    def _stream_cb(self, en):
        """Data stream callback
        """
        _methodname = self._stream_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("data stream callback [{:}]".format(en))
            sys.stdout.flush()

        if en:
            self.board.active = True
            self.models.stream.label = uips._FT3_SERVER_STREAM_BUTTON_ACTIVE_LABEL
            self.models.stream.button_type = uips._FT3_SERVER_STREAM_BUTTON_ACTIVE_TYPE
        else:
            self.board.active = False
            self.models.stream.label = uips._FT3_SERVER_STREAM_BUTTON_INACTIVE_LABEL
            self.models.stream.button_type = uips._FT3_SERVER_STREAM_BUTTON_INACTIVE_TYPE
