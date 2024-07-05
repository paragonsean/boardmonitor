#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import sys

import numpy as np
import pandas as pd

import struct

from typing import Callable
from dataclasses import dataclass

from threading import Lock

import tcpip.msgdata as msg
import data.config as cfgd
import util.util as util


@dataclass
class CallbackMeta:
    shot : int
    t0   : pd.Timestamp
    t1   : pd.Timestamp
    num_p: int
    num_t: int

@dataclass
class CallbackEvents:
    t    : list
    event: list

@dataclass
class CallbackGroup:
    send_cmd  : Callable[[msg.CmdData  ], None]
    recv_resp : Callable[[msg.RespData ], None]
    recv_async: Callable[[msg.AsyncData], None]


class Callbacks(object):
    def __init__(self, board=None, verbose=util.VerboseLevel.info):
        _methodname = self.__init__.__name__

        self.board = board
        self.verbose = verbose

        self.mutexes = util.Mutexes(meta=Lock(),
                                    shot=Lock(),
                                    events=Lock())

        try:
            board._sql_conn()
            _meta = pd.read_sql_table(table_name=board.sql.tables.meta, con=board.sql.engine)
            _shot = _meta.shot.max()
        except  Exception as e:
            _shot = 0
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("SQL database shot number e {}".format(e))
                sys.stdout.flush()

        self._meta = CallbackMeta(shot=_shot, t0=None, t1=None, num_p=0, num_t=0)
        self._events = CallbackEvents(t=[], event=[])

        self._shot_bytes_p = b''
        self._shot_bytes_t = b''

        self.fcn = CallbackGroup(send_cmd=lambda m: None,
                                 recv_resp=self._recv_resp_cb,
                                 recv_async=self._recv_async_cb)

    def _recv_resp_cb(self, m):
        _methodname = self._recv_resp_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("FasTrak3 recv response [{}]".format(len(m.data)))
            sys.stdout.flush()

    def _recv_async_cb(self, m):
        _methodname = self._recv_async_cb.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("FasTrak3 recv async data [{}]".format(len(m.data)))
            sys.stdout.flush()

        _type = msg.AsyncDataType(m.header.bin_type)
        if _type == msg.AsyncDataType.shot_pos:
            self.mutexes.shot.acquire()
            try:
                if not self._shot_bytes_p:
                    self.mutexes.meta.acquire()
                    try:
                        self._meta.shot += 1
                        self._meta.t1 = pd.Timestamp.now()
                    except Exception as e:
                        if self.verbose >= util.VerboseLevel.error:
                            util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                            print("metadata exception e {}".format(e))
                            sys.stdout.flush()
                    self.mutexes.meta.release()

                self._shot_bytes_p += m.data
            except Exception as e:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("shot-buffer position-sample exception e {}".format(e))
                    sys.stdout.flush()
            self.mutexes.shot.release()
        elif _type == msg.AsyncDataType.shot_time:
            self.mutexes.shot.acquire()
            try:
                self._shot_bytes_t += m.data
            except Exception as e:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("shot-buffer time-sample exception e {}".format(e))
                    sys.stdout.flush()
            self.mutexes.shot.release()
        elif _type == msg.AsyncDataType.shot_comp:
            if self.verbose >= util.VerboseLevel.info:
                util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
                print("FasTrak3 shot acquired [P:{} T:{}]".format(len(self._shot_bytes_p), len(self._shot_bytes_t)))
                sys.stdout.flush()

            # Unpack position- and time- shot data streams
            self.mutexes.shot.acquire()
            try:
                _llp = [s for s in struct.iter_unpack(msg._FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT, self._shot_bytes_p)]
                _llt = [s for s in struct.iter_unpack(msg._FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT, self._shot_bytes_t)]
            except Exception as e:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("shot-buffer unpack exception e {}".format(e))
                    sys.stdout.flush()
            self.mutexes.shot.release()

            self.mutexes.meta.acquire()
            try:
                _shot  = self._meta.shot
                _num_p = self._meta.num_p = len(_llp)
                _num_t = self._meta.num_t = len(_llt)
            except Exception as e:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("metadata access exception e {}".format(e))
                    sys.stdout.flush()
            self.mutexes.meta.release()

            _pre_p = pd.DataFrame(data=[[_shot,'P']]*_num_p, columns=('shot','type'))
            _pre_t = pd.DataFrame(data=[[_shot,'T']]*_num_t, columns=('shot','type'))

            s_ad_p = pd.DataFrame(data=_llp, columns=msg._FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES)
            s_ad_t = pd.DataFrame(data=_llt, columns=msg._FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES)

            s_ad_p = pd.concat((_pre_p, s_ad_p), axis=1)
            s_ad_t = pd.concat((_pre_t, s_ad_t), axis=1)

            s_ad = pd.concat((s_ad_p, s_ad_t))
            s_ad.reset_index(drop=True, inplace=True)

            # Shot timespan
            self.mutexes.meta.acquire()
            try:
                elap_ms = s_ad.one_ms_timer.values[-1]
                self._meta.t0 = self._meta.t1 - pd.Timedelta(value=elap_ms, unit='ms')
            except Exception as e:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("metadata update exception e {}".format(e))
                    sys.stdout.flush()
            self.mutexes.meta.release()

            # Convert shot data (A/D measurements to engineering data)
            B = self.board
            Bd = B.data
            df = B.convert_ad(s_ad)

# TODO ... integrate/enable shot data via FasTrak3 board rather than sim
            # Metadata
            self.mutexes.meta.acquire()
            try:
                m = self._meta
                data = [(m.shot, m.t0, m.t1, m.num_p, m.num_t)]
                Bd.meta += pd.DataFrame(data=data, columns=cfgd._FT3_DATA_META_DATAFRAME_VARIABLES)
            except Exception as e:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("metadata board-data exception e {}".format(e))
                    sys.stdout.flush()

# TODO ... integrate/enable events via FasTrak3 board rather than sim
            self.mutexes.events.acquire()
            try:
                ev = self._events
                _shot  = pd.Series(data=[m.shot]*len(ev.t), name=cfgd._FT3_DATA_EVENTS_DATAFRAME_VARIABLES[0])
                _t     = pd.Series(data=ev.t, name=cfgd._FT3_DATA_EVENTS_DATAFRAME_VARIABLES[1])
                _event = pd.Series(data=ev.event, name=cfgd._FT3_DATA_EVENTS_DATAFRAME_VARIABLES[2])
                Bd.events += pd.concat((_shot, _t, _event), axis=1)
            except Exception as e:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("events board-data exception e {}".format(e))
                    sys.stdout.flush()
            self.mutexes.events.release()
            self.mutexes.meta.release()

# TODO ... integrate/enable shot data via FasTrak3 board rather than sim
            # Shot A/D measurements
            Bd.ad += s_ad

# TODO ... integrate/enable shot data via FasTrak3 board rather than sim
            # Shot data
            Bd.shot += df

            # SQL database
            B.sql_write()

            # Clear shot-data and event buffers
            self.mutexes.shot.acquire()
            try:
                self._shot_bytes_p = b''
                self._shot_bytes_t = b''
            except Exception as e:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("shot-buffer clear exception e {}".format(e))
                    sys.stdout.flush()
            self.mutexes.shot.release()

            self.mutexes.events.acquire()
            try:
                self._events = CallbackEvents(t=[], event=[])
            except Exception as e:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("event-buffer clear exception e {}".format(e))
                    sys.stdout.flush()
            self.mutexes.events.release()

        elif _type == msg.AsyncDataType.string:
            if self.verbose >= util.VerboseLevel.info:
                util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
                print("FasTrak3 async message {} [{}]".format(m.data,len(m.data)))
                sys.stdout.flush()

            self.mutexes.events.acquire()
            try:
                self._events.t += [pd.Timestamp.now()]
                self._events.event +=[m.data.decode().strip('\\n')]
            except Exception as e:
                if self.verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("event-buffer update exception e {}".format(e))
                    sys.stdout.flush()
            self.mutexes.events.release()
