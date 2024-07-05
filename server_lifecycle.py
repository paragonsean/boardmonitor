#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import sys
import os

from pathlib import Path
import inspect

import dill

import numpy as np
import pandas as pd

import time
from threading import Thread

import ipaddress

import util.util as util
import board.config as cfgb
import data.config as cfgd


_FT3_SERVER_DATA_QUERY_DT = 15.000
_FT3_SERVER_DATA_SLEEP_DT = 0.050

_FT3_SERVER_DATA_SIM_NUM_POS    = num_p  = 1000
_FT3_SERVER_DATA_SIM_NUM_TIME   = num_t  = 500
_FT3_SERVER_DATA_SIM_NUM_TRAJ   = N = num_p + num_t


_FT3_SERVER_DATA_SIM_EVENTS = []
_FT3_SERVER_DATA_SIM_EVENTS += ["R:19 #Cycle start timeout"]
_FT3_SERVER_DATA_SIM_EVENTS += ["R:20 #Cycle start detected!"]
#_FT3_SERVER_DATA_SIM_EVENTS += ["R_AXIS1_INVALID_AXIS_SPECIFIER:21"]
#_FT3_SERVER_DATA_SIM_EVENTS += ["R_ERROR:2 #Syntax error, bad command number"]
#_FT3_SERVER_DATA_SIM_EVENTS += ["R_ERROR:2 #Syntax error"]
_FT3_SERVER_DATA_SIM_EVENTS += ["R_AXIS1_AUTO_NULL_SUCCESS:25 #-310"]
_FT3_SERVER_DATA_SIM_EVENTS += ["RETRACT_VALVE_SET"]
_FT3_SERVER_DATA_SIM_EVENTS += ["R_POS1EOS"]
_FT3_SERVER_DATA_SIM_EVENTS += ["R_At home detected:27"]

_FT3_SERVER_DATA_SIM_EVENTS_ALWAYS = [False] * len(_FT3_SERVER_DATA_SIM_EVENTS)
_FT3_SERVER_DATA_SIM_EVENTS_ALWAYS[1] = True
_FT3_SERVER_DATA_SIM_EVENTS_ALWAYS[-2] = True
_FT3_SERVER_DATA_SIM_EVENTS_ALWAYS[-1] = True

f = inspect.getfile(inspect.currentframe())
_FT3_SERVER_DATA_SIM_SHOT_RELPATH  = os.path.join("sim","data")
_FT3_SERVER_DATA_SIM_SHOT_ABSPATH  = os.path.join(Path(f).resolve().parent, _FT3_SERVER_DATA_SIM_SHOT_RELPATH)

_FT3_SERVER_DATA_SIM_SHOT_FILENAME = "ft3_ad.pkl"


class FT3_Server(object):
    def __init__(self, server, verbose=util.VerboseLevel.debug):
        self.server = server

        self.data_t0 = np.ceil(time.time())
        self.data_thread = Thread(target=self._data_cb, daemon=False)

        self.verbose = verbose

    def _data_cb(self):
        """Simulated data periodic callback
        """
        _methodname = self._data_cb.__name__

        # FasTrak3 shot data A/D measurements
        f = os.path.join(_FT3_SERVER_DATA_SIM_SHOT_ABSPATH,_FT3_SERVER_DATA_SIM_SHOT_FILENAME)
        fid = open(f, "rb")
        ft3_ad = dill.load(fid)
        fid.close()

        while True:
            # Wait to simulate data acquisition / rx
            while (time.time() - self.data_t0 < _FT3_SERVER_DATA_QUERY_DT):
                time.sleep(_FT3_SERVER_DATA_SLEEP_DT)

            t = time.time()
            t0 = self.data_t0
            self.data_t0 += _FT3_SERVER_DATA_QUERY_DT

            if self.verbose >= util.VerboseLevel.debug:
                util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
                print("FasTrak3 data received SERVER {}".format(self.server))
                util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
                print("t {:.3f}   t0 {:.3f}   dt {:.3f}".format(t,t0,t-t0))
                print("")
                sys.stdout.flush()

            for i,ss in enumerate(self.server.sessions):
                try:
                    # FasTrak3 board data reference
                    _cx = ss.document.session_context
                    B = _cx.board
                    Bd = _cx.board.data

                    if ipaddress.ip_address(B.ip) != cfgb._FT3_BOARD_IP_LOCALHOST:
                        continue

                except Exception as e:
                    if self.verbose >= util.VerboseLevel.error:
                        util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                        print("FasTrak3 board access exception e: {}".format(e))
                        print("")
                        sys.stdout.flush()
                        continue

                try:
                    # Temporary demo shot number
                    _cx.shot += 1
                    s = _cx.shot
                except Exception as e:
                    if self.verbose >= util.VerboseLevel.error:
                        util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                        print("FasTrak3 demo shot number exception e: {}".format(e))
                        print("")
                        sys.stdout.flush()
                        continue

                # Simulated shot data (1)
                # NB: Preparation of shot data to enable calculation of consistent metadata.
                #     Metadata and events passed to FasTrak3 web interface application prior
                #     to shot data b/c of alarm-parameter calculator logic via callback ...
                try:
                    # Randomly selected shot from FasTrak3 A/D database
                    s_ii = np.random.choice(ft3_ad.shot.unique())
                    s_ad = ft3_ad[ft3_ad.shot==s_ii].reset_index(drop=True).drop(columns="id")
                    s_ad.shot = s # Consistent demo shot number

                    df = _cx.board.convert_ad(s_ad)
                    num_p = (df.type == 'P').sum()
                    num_t = (df.type == 'T').sum()

                    # Random noise
                    N = len(df)
                    df.pos[num_p:] *= (1.00 + 0.0001*np.random.randn(num_t))
                    df.vel *= (1.00 + 0.01*np.random.randn(N))
                    df.press_head *= (1.00 + 0.01*np.random.randn(N))
                    df.press_rod *= (1.00 + 0.01*np.random.randn(N))

                except:
                    # Placeholder shot A/D measurements
                    s_ad = pd.DataFrame(data=None, columns=cfgd._FT3_DATA_AD_DATAFRAME_VARIABLES)

                    _shot = pd.Series(data=[s]*N, name="shot")
                    _type = pd.Series(data=['P']*num_p + ['T']*num_t, name="type")
    
                    _t = pd.Series(data=np.linspace(start=0.0, stop=1.0, num=N), name="t")
                    _pos = pd.Series(data=np.linspace(start=0.0, stop=1.0, num=N), name="pos")
                    _vel = pd.Series(data=np.random.randn(N), name="vel")
    
                    _press_head = pd.Series(data=np.random.randn(N), name="press_head")
                    _press_rod = pd.Series(data=np.random.randn(N), name="press_rod")
                
                    df = pd.concat((_shot,_type,_t,_pos,_vel,_press_head,_press_rod), axis=1)
                
                
                # Simulated shot metadata
                _shot = pd.Series(data=[s], name="shot")
                _t0 = pd.Series(data=[pd.Timestamp.now()], name="t0")
                _t1 = pd.Series(data=[pd.Timestamp.now() + pd.Timedelta(seconds=3)], name="t1")
                _num_p = pd.Series(data=[num_p], name="num_pos_samples")
                _num_t = pd.Series(data=[num_t], name="num_time_samples")
                
                Bd.meta += pd.concat((_shot,_t0,_t1,_num_p,_num_t), axis=1)
    
        
                # Simulated event data
                _prob = np.random.rand(len(_FT3_SERVER_DATA_SIM_EVENTS))
                _ii = (_prob > 0.50) | _FT3_SERVER_DATA_SIM_EVENTS_ALWAYS
                _ev = np.array(_FT3_SERVER_DATA_SIM_EVENTS)[_ii]
                num_ev = len(_ev)
    
                _shot = pd.Series(data=[s]*num_ev, name="shot")
                _t = []
                for i in range(num_ev):
                    _t += [pd.Timestamp.now() + pd.Timedelta(seconds=0.5*i)]
                _t = pd.Series(data=_t, name="t")
                
                _event = pd.Series(data=_ev, name="event")
                Bd.events += pd.concat((_shot,_t,_event), axis=1)


                # Profile/debug
                if self.verbose >= util.VerboseLevel.debug:
                    t1 = util._FT3_UTIL_NOW_TS()

                # Shot A/D measurements
                Bd.ad += s_ad
        
                # Simulated shot data (2)
                Bd.shot += df

                # SQL database
                _cx.board.sql_write()

                # Profile/debug
                if self.verbose >= util.VerboseLevel.debug:
                    tf = util._FT3_UTIL_NOW_TS()
                    util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
                    print("session shot data profile            {:.3f}s".format((tf-t1).total_seconds()))
                    util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
                    print("dataset lengths M:{:4d} E:{:4d} S:{:4d} P:{:4d}".format(len(Bd.meta.data),len(Bd.events.data),len(Bd.shot.data),len(Bd.param.data)))
                    print("")
                    sys.stdout.flush()

    def go(self):
        _methodname = self.go.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("FasTrak3 server started")
            print("")
            sys.stdout.flush()

        self.data_thread.start()

def on_server_loaded(server_context):
    """Initialize FasTrak3 web interface application server
       (called at bokeh server start)
    """
    S = FT3_Server(server=server_context)
    S.go()

def on_session_created(session_context):
    """Initialize FasTrak3 web interface application server session
       (called prior to per-session execution of main.py)
    """
    setattr(session_context, 'board', None)
    setattr(session_context, 'shot', 0)
