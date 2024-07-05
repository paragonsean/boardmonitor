#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 board manager
"""
import sys
import concurrent.futures

import numpy as np
import pandas as pd

from dataclasses import dataclass
from enum import IntEnum,unique

import ipaddress

import sqlalchemy as sqla
import sqlalchemy_utils as sqlu

import data.data as data

import ad.ad as ad
import tcpip.client as client

import state.uiprop as uipss

import board.config as cfgb

import data.config as cfgd
import param.config as cfgp

import util.util as util
import units.units as units

@unique
class Version(IntEnum):
    ft3 = 3


@dataclass
class Data:
    meta  : data.FT3MetaAccessor
    shot  : data.FT3ShotAccessor
    ref   : data.FT3RefAccessor
    param : data.FT3ParamAccessor
    events: data.FT3EventsAccessor
    ad    : data.FT3AdAccessor


@dataclass
class SQLDatabase:
    name: str
    pdio: pd.io.sql.SQLDatabase
    
@dataclass
class SQLTables:
    meta  : str
    shot  : str
    events: str
    ad    : str

@dataclass
class BoardSQL:
    engine  : sqla.engine.base.Engine

    user    : str
    password: str
    server  : str
    
    database: SQLDatabase
    tables  : SQLTables


class Board(object):
    def __init__(self, session=None, version=Version.ft3, name=cfgb._FT3_BOARD_NAME_DEFAULT, ip=cfgb._FT3_BOARD_IP_DEFAULT, unitsys=units.UnitSystem.bg, verbose=util.VerboseLevel.info):
        """Initialize FasTrak3 board
        """
        self._active = False

        self.session = session
        self.verbose = verbose

        self.version = version
        self.name = name
        self.ip = ip

        self.unitsys = unitsys

        self.data = Data(meta=pd.DataFrame().ft3meta,
                         shot=pd.Series().ft3shot,
                         ref=pd.DataFrame().ft3ref,
                         param=pd.DataFrame().ft3param,
                         events=pd.Series().ft3events,
                         ad=pd.Series().ft3ad)

        _db = SQLDatabase(name=cfgb._FT3_BOARD_SQL_DATABASE+'_'+str(self.ip).replace('.','_'),
                          pdio=None)
        _tables = SQLTables(meta=cfgb._FT3_BOARD_SQL_META_TABLE,
                            shot=cfgb._FT3_BOARD_SQL_SHOT_TABLE,
                            events=cfgb._FT3_BOARD_SQL_EVENTS_TABLE,
                            ad=cfgb._FT3_BOARD_SQL_AD_TABLE)

        self.sql = BoardSQL(engine=None,
                            user=cfgb._FT3_BOARD_SQL_USER,
                            password=cfgb._FT3_BOARD_SQL_PASSWORD,
                            server=cfgb._FT3_BOARD_SQL_SERVER,
                            database=_db,
                            tables=_tables)

        self.channels = ad.Channels(session=self, verbose=verbose)

        self.client = client.Client(self, verbose=verbose) # FasTrak3 TCP/IP client
        self.client.connect()

    def sql_read(self):
        """Read SQL database
        """
        _methodname = self.sql_read.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("read SQL database")
            sys.stdout.flush()


    def sql_write(self):
        """Write SQL database
        """
        _methodname = self.sql_write.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("write SQL database")
            sys.stdout.flush()

        try:
            self._sql_conn()

            engine = self.sql.engine
            sqldb = self.sql.database.pdio

            # SQL database shot metadata table
            df = self.data.meta._data.tail(1)

            # Create empty shot metadata table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.meta):
                args = [self.sql.tables.meta, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    uq = 'alter table "{0:s}" add unique ({1:s});'
                    uq = uq.format(self.sql.tables.meta, cfgb._FT3_BOARD_SQL_FOREIGN_KEY)
                    conn.execute(uq)

            df.to_sql(name=self.sql.tables.meta, con=engine, if_exists="append", index=False)


            #SQL database shot data table
            df = self.data.shot._data.iloc[-1]

            # Create empty shot data table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.shot):
                args = [self.sql.tables.shot, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.shot, cfgb._FT3_BOARD_SQL_FOREIGN_KEY,
                                   self.sql.tables.meta, cfgb._FT3_BOARD_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.shot, con=engine, if_exists="append", index=False)


            #SQL database events table
            df = self.data.events._data.iloc[-1]

            # Create empty events table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.events):
                args = [self.sql.tables.events, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.events, cfgb._FT3_BOARD_SQL_FOREIGN_KEY,
                                   self.sql.tables.meta, cfgb._FT3_BOARD_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.events, con=engine, if_exists="append", index=False)


            #SQL database shot A/D measurements table
            df = self.data.ad._data.iloc[-1]

            # Create empty shot A/D measurements table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.ad):
                args = [self.sql.tables.ad, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.ad, cfgb._FT3_BOARD_SQL_FOREIGN_KEY,
                                   self.sql.tables.meta, cfgb._FT3_BOARD_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.ad, con=engine, if_exists="append", index=False)

        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("write SQL database exception e {}".format(e))
                sys.stdout.flush()

    def _sql_conn(self):
        """Connect SQL database
        """
        _methodname = self._sql_conn.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("connect SQL database")
            sys.stdout.flush()

        try:
            if self.sql.engine is None:
                conn = cfgb._FT3_BOARD_SQL_CONN_PREFIX
                conn += self.sql.user + ":"
                conn += self.sql.password + "@"
                conn += self.sql.server + "/"
                conn += self.sql.database.name
                
                engine = self.sql.engine = sqla.create_engine(conn, use_batch_mode=True)
                if not sqlu.database_exists(engine.url):
                    sqlu.create_database(engine.url)

                self.sql.database.pdio = pd.io.sql.SQLDatabase(self.sql.engine)

        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("write SQL database connect exception e {}".format(e))
                sys.stdout.flush()


    def _calc_cb(self, new):
        """Calculate derived-parameters for warnings/alarms
           NB: Implicit reqm't to pass metadata (and events)
               prior to shot data for current shot
        """
        _methodname = self._calc_cb.__name__

        # Profile/debug
        if self.verbose >= util.VerboseLevel.debug:
            t0 = util._FT3_UTIL_NOW_TS()

        try:
            # Machine and part references
            Sm,Sp = self.session.machine, self.session.part

            # Shot data, position- and time- subsets
            dfp = new[(new.type=='P')]
            dft = new[(new.type=='T')]

            # Drop invalid first sample of datasets owing to one-based start 
            # indexes of position- and time- sampled data in the FasTrak2(3)
            # firmware.
            dfp = dfp.drop(dfp.head(2).index)
            dft = dft.drop(dft.head(2).index)

            dfp.reset_index(drop=True, inplace=True)
            dft.reset_index(drop=True, inplace=True)

            # Shot number
            s = new.shot.values[0]

            # FILL TIME (Sect 2.1 Design Document)
            # NB: t2 calculation via searchsorted() method
            #     implies position increases monotonically
            t3,p3 = dfp.t.iloc[-1], dfp.pos.iloc[-1]
            p2 = p3 - Sp.plunger.p2_p3
            t2 = dfp.t.iloc[min(dfp.pos.searchsorted(p2),len(dfp)-1)]
            _fill_time = t3 - t2

            # intermediate/reusable indices
            _ii_fs = ((dfp.pos > Sp.csfs.min_pos) &
                      (dfp.vel > Sp.csfs.min_vel))
            _ii_csfs = _ii_fs.idxmax()

            # AVERAGE SLOW SHOT VELOCITY (Sect. 2.2 Deisgn Document)
            # NB: FasTrak2 SureTrak codebase defines initial movement
            #     of plunger as first position-sampled point
            _ss_vel_avg = dfp.vel[:_ii_csfs].mean()

            # AVERAGE FAST SHOT VELOCITY (Sect. 2.3 Design Document)
            _fs_vel_avg = dfp.vel[_ii_fs].mean()

            # BISCUIT SIZE (Sect. 2.4 Design Document)
            _biscuit_size = Sp.stroke.total - new.pos.max()

            # INTENSIFICATION SQUEEZE DISTANCE (Sect. 2.5 Design Document)
            _intens_squeeze_dist = dft.pos.max() - p3
    
            # INTENSIFICATION RISE TIME (Sect. 2.6 Design Document)
            # NB: t3 (time corresponding to p3) explicitly handled
            #     in time-sampled points from FasTrak3 board, i.e.
            #     time restarts at zero for time-sampled data
            _ii_dt = (dft.press_head >= Sp.intens.p_target).idxmax()
            _intens_rise_time = dft.t[_ii_dt]

            # CSFS (Sect. 2.7 Design Document)
            _csfs = dfp.pos[_ii_csfs]

            # CYCLE TIME (Sect. 2.8 Design Document)
            _Mh = self.data.meta.data
            if s > _Mh.shot.min():
                _cycle_time = _Mh.t0[_Mh.shot==s].values[0] - _Mh.t0[_Mh.shot==(s-1)].values[0]
                _cycle_time /= np.timedelta64(1, 's')
            else:
                # No historical prior shots to calculate cycle time
                _cycle_time = cfgp._FT3_ALARM_PARAMETER_TARGET_VALUES[-3]

            # PEAK INTENSIFICATION PRESSURE (Sect. 2.9 Design Document)
            # NB: metal pressure definition per technical interchanges
            #     with Visi-Trak 21-AUG-2019 and review of the FasTrak2
            #     SureTrak 2020 codebase.
            _mepr = ((dft.press_head * Sm.geom.head_area) -
                     (dft.press_rod * Sm.geom.rod_area  ))
            _mepr /= Sm.geom.plunger_area
            
            _ii_pk = _mepr[Sp.intens.pk_skip:].idxmax()
            _peak_intens_press = dft.press_head[_ii_pk]

            # SLOW SHOT VARIATION RATE (Sect. 2.10 Design Document)
            _ii_ss_user = ((dfp.pos >= Sp.ss_var.start_pos_user) &
                           (dfp.pos <= Sp.ss_var.end_pos_user  ))
            _ss_vel = dfp.vel[_ii_ss_user].mean()

            _ii_ss_p0 = ((dfp.pos > (Sp.ss_var.start_pos_init + Sp.ss_var.start_pos_bias)) &
                         (dfp.vel > (Sp.ss_var.start_pos_gain *_ss_vel                  ))).idxmax()
            _ii_ss_p1 = (dfp.pos <= (_csfs - Sp.ss_var.end_pos_bias)).idxmin()

            _Vss = dfp.vel[_ii_ss_p0:_ii_ss_p1]
            _ss_var_rate = 50.0 * (_Vss.max() - _Vss.min()) / _ss_vel

            if np.isnan(_ss_var_rate):
                _ss_var_rate = 100.0
            
            # Alarm parameters
            p = []
            p += [_fill_time]
            p += [_ss_vel_avg]
            p += [_fs_vel_avg]
            p += [_biscuit_size]
            p += [_intens_squeeze_dist]
            p += [_intens_rise_time]
            p += [_csfs]
            p += [_cycle_time]
            p += [_peak_intens_press]
            p += [_ss_var_rate]

            _shot = pd.Series(data=[s], name="shot")
            _p = pd.DataFrame(data=[p], columns=cfgp._FT3_ALARM_PARAMETER_NAMES)
            
            # Profile/debug
            if self.verbose >= util.VerboseLevel.debug:
                t1 = util._FT3_UTIL_NOW_TS()

            self.data.param += pd.concat((_shot,_p), axis=1)

        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("exception e {}".format(e))
                sys.stdout.flush()
            return

        if self.verbose >= util.VerboseLevel.debug:
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("fill time                        {:8.2f} ms  ".format(_fill_time))
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("average slow-shot velocity       {:8.2f} in/s".format(_ss_vel_avg))
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("average fast-shot velocity       {:8.2f} in/s".format(_fs_vel_avg))
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("biscuit size                     {:8.2f} in  ".format(_biscuit_size))
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("intensification squeeze distance {:8.2f} in  ".format(_intens_squeeze_dist))
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("intensification rise time        {:8.2f} ms  ".format(_intens_rise_time))
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("CSFS                             {:8.2f} in  ".format(_csfs))
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("cycle time                       {:8.2f} s   ".format(_cycle_time))
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("peak intensification pressure    {:8.2f} psi ".format(_peak_intens_press))
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("slow-shot variation rate         {:8.2f}     ".format(_ss_var_rate))
            sys.stdout.flush()

        # Profile/debug
        if self.verbose >= util.VerboseLevel.debug:
            tf = util._FT3_UTIL_NOW_TS()
            dt0 = (t1 - t0).total_seconds()
            dt1 = (tf - t1).total_seconds()
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("profile (t1 - t0) {:.3f}s   (tf - t1) {:.3f}s".format(dt0,dt1))
            print("")
 
    def _update_cb(self, new):
        """Update shot trajectory and parameter alarm-state UIs
        """
        _methodname = self._update_cb.__name__

        # Profile/debug
        if self.verbose >= util.VerboseLevel.debug:
            t0 = util._FT3_UTIL_NOW_TS()

        # Shot parameter data
        _spdf = self.data.param.data

        # UI shot indexes and shot data dimensions
        # NB: UI shot indexes are not equal to shot numbers in general
        _uii = self.session.state.uii

        _uii.num_shot = len(_spdf)
        _uii.num_view = min(_uii.num_shot,uipss._FT3_ALARM_STATE_STATUS_PLOT_COLS)
        _uii.min_shot = (_uii.num_shot - _uii.num_view)
        _uii.max_shot = max(_uii.num_shot - 1, 0)

        # UI consistency... paused-and-restarted data stream
        s = _uii.sel_shot
        if (s < _uii.min_shot):
            _uii.sel_shot = _uii.min_shot - 1

        # UI consistency iff state / shot-trajectory updates
        # partitioned to parallel asynchronous thread-pools
        s = _uii.sel_shot
        if (s < _uii.num_shot - 1):
            s += 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as e:
            _ = e.submit(fn=self.session.state.update)
            _ = e.submit(fn=self.session.shot.update, sel_shot=_spdf.shot[s])

        # Profile/debug
        if self.verbose >= util.VerboseLevel.debug:
            tf = util._FT3_UTIL_NOW_TS()
            print("____________________________________________________________________________________")
            util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
            print("shot-data update total profile     {:.3f}s".format((tf - t0).total_seconds()))
            print("____________________________________________________________________________________")
            
    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val):
        if val:
            self._active = True
            self.data.shot.cb = self._calc_cb
            self.data.param.cb = self._update_cb
        else:
            self._active = False
            #self.data.shot.cb = lambda new: None
            self.data.param.cb = lambda new: None

    def convert_ad(self, ad):
        """Convert A/D measurements to engineering-units data
        """
        _dfp = pd.DataFrame(data=None, columns=cfgd._FT3_DATA_SHOT_DATAFRAME_VARIABLES)
        _dft = pd.DataFrame(data=None, columns=cfgd._FT3_DATA_SHOT_DATAFRAME_VARIABLES)

        _adp = ad[ad.type=='P']
        _adt = ad[ad.type=='T']

        _dfp.shot = _adp.shot
        _dft.shot = _adt.shot
        
        _dfp.type = _adp.type
        _dft.type = _adt.type
        
        _dfp.t = _adp.one_ms_timer
        _t = _adt.one_ms_timer.values - _dfp.t.values[-1]
        _t[0] = 0.0
        _dft.t = _t

        # rod pitch, mm
        _pmm = self.session.machine.rod.pitch

        _dfp.pos = (_adp.position * _pmm)/4.0
        _dft.pos = (_adt.position * _pmm)/4.0

        _vel = (cfgb._FT3_BOARD_QUAD_COUNTS_PER_SEC * _pmm)/np.diff(_adp.vel_count_q1)
        _dfp.vel = np.append(0.0,_vel)
        _dft.vel = 0.0

        _dfp.press_head = self.channels.calc_press_head(_adp)
        _dft.press_head = self.channels.calc_press_head(_adt)

        _dfp.press_rod  = self.channels.calc_press_rod(_adp)
        _dft.press_rod  = self.channels.calc_press_rod(_adt)

        return pd.concat((_dfp,_dft)).reset_index(drop=True)

class Boards(object):
    def __init__(self, default=True, verbose=util.VerboseLevel.info):
        """Initialize active board manager
        """
        if default:
            self.boards = [Board(version=Version.ft3, name=cfgb._FT3_BOARD_NAME_DEFAULT, ip=cfgb._FT3_BOARD_IP_DEFAULT, verbose=verbose)]
        else:
            self.boards = []
        self.verbose = verbose

    def add(self, version=Version.ft3, name=None, ip=None):
        """Add device to active board manager
        """
        _methodname = self.add.__name__

        if version == Version.ft3:
            n = len(self.boards)

            names = [board.name for board in self.boards]
            ips = [int(board.ip) for board in self.boards]

            _name = name
            while _name in names or _name is None:
                n += 1
                _name = cfgb._FT3_BOARD_NAME_GENERATOR(n)
            
            _ip = ip
            if _ip in ips or _ip is None:
                try:
                    _ip = max(ips) + 1
                except ValueError:
                    _ip = int(cfgb._FT3_BOARD_IP_DEFAULT)
            
            self.boards += [cfgb.Board(version=Version.ft3, name=_name, ip=ipaddress.ip_address(_ip))]
        else:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("unknown board type {}".format(version))
                sys.stdout.flush()
    
    def rm(self, version=Version.ft3, name=None, ip=None):
        """Remove device from active board manager
        """
        _methodname = self.rm.__name__

        if name is None and ip is None:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("name or IP address required to remove device")
                sys.stdout.flush()
            return

        if version == Version.ft3:
            names = [board.name for board in self.boards]
            ips = [board.ip for board in self.boards]
            
            if name is None:
                if ip in ips:
                    index = ips.index(ip)
                else:
                    if self.verbose >= util.VerboseLevel.error:
                        util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                        print("board IP {} is not in list of actively managed FasTrak3 devices".format(ip))
                        sys.stdout.flush()
                    return                    
            elif ip is None:
                if name in names:
                    index = names.index(name)
                else:
                    if self.verbose >= util.VerboseLevel.error:
                        util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                        print("board name {} is not in list of actively managed FasTrak3 devices".format(name))
                        sys.stdout.flush()
                    return
            else:
                if name in names and ip in ips:
                    i0 = names.index(name)
                    i1 = ips.index(ip)
                    if i0 == i1:
                        index = i0
                    else:
                        if self.verbose >= util.VerboseLevel.error:
                            util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                            print("board name {}, IP {} pair not in list of actively managed FasTrak3 devices".format(name, ip))
                            sys.stdout.flush()
                        return
                else:
                    if self.verbose >= util.VerboseLevel.error:
                        util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                        print("board name {}, IP {} pair not in list of actively managed FasTrak3 devices".format(name, ip))
                        sys.stdout.flush()
                    return

            self.boards.pop(index)
        else:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("unknown board type {}".format(version))
                sys.stdout.flush()
            return
