#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 alarm SQL database interface
"""
import sys

import pandas as pd

from dataclasses import dataclass

import sqlalchemy as sqla
import sqlalchemy_utils as sqlu

import alarm.config as cfga

import state.data as ssdata
import state.config as cfgss

import util.util as util

@dataclass
class SQLDatabase:
    name: str
    pdio: pd.io.sql.SQLDatabase
    
@dataclass
class SQLTables:
    alarm_metadata: str
    alarm_none    : str
    warn_low      : str
    warn_high     : str
    alarm_low     : str
    alarm_high    : str
    alarm_unknown : str
    alarm_state   : str
    limits_wires  : str

@dataclass
class AlarmSQL:
    engine  : sqla.engine.base.Engine

    user    : str
    password: str
    server  : str
    
    database: SQLDatabase
    tables  : SQLTables

        
class Alarm(object):
    def __init__(self, session=None, verbose=util.VerboseLevel.info):
        """Initialize FasTrak3 alarm database
        """
        self.session = session
        self.verbose = verbose

        _db = SQLDatabase(name=cfga._FT3_ALARM_SQL_DATABASE+'_'+str(session.board.ip).replace('.','_'),
                          pdio=None)
        _tables = SQLTables(alarm_metadata=cfga._FT3_ALARM_SQL_ALARM_METADATA_TABLE,
                            alarm_none=cfga._FT3_ALARM_SQL_ALARM_NONE_TABLE,
                            warn_low=cfga._FT3_ALARM_SQL_WARN_LOW_TABLE,
                            warn_high=cfga._FT3_ALARM_SQL_WARN_HIGH_TABLE,
                            alarm_low=cfga._FT3_ALARM_SQL_ALARM_LOW_TABLE,
                            alarm_high=cfga._FT3_ALARM_SQL_ALARM_HIGH_TABLE,
                            alarm_unknown=cfga._FT3_ALARM_SQL_ALARM_UNKNOWN_TABLE,
                            alarm_state=cfga._FT3_ALARM_SQL_ALARM_STATE_TABLE,
                            limits_wires=cfga._FT3_ALARM_SQL_LIMITS_WIRES_TABLE)

        self.sql = AlarmSQL(engine=None,
                            user=cfga._FT3_ALARM_SQL_USER,
                            password=cfga._FT3_ALARM_SQL_PASSWORD,
                            server=cfga._FT3_ALARM_SQL_SERVER,
                            database=_db,
                            tables=_tables)

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

            # Parameter limits/wires profile
            # NB: Use as foreign key for SQL database tables
            _p = self.session.part.param.data.profile
            _profile = pd.Series(data=_p, name=cfga._FT3_ALARM_SQL_FOREIGN_KEY)


            # Reusable shot parameter dataframe parts and dimensions
            _A = self.session.state.data.alarm_state.drop(columns=cfgss._FT3_ALARM_STATE_SHOT_VARIABLE)
            num_shot,num_p = _A.shape

            _s = self.session.board.data.param.data.shot
            min_shot = _s.min()
            max_shot = _s.max()


            # SQL database alarm metadata table
            df = pd.DataFrame(data=[[_p,min_shot,max_shot,num_shot]],
                              columns=(cfga._FT3_ALARM_SQL_FOREIGN_KEY,"min_shot","max_shot","num_shot"))

            # Create empty alarm metadata table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.alarm_metadata):
                args = [self.sql.tables.alarm_metadata, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    uq = 'alter table "{0:s}" add unique ({1:s});'
                    uq = uq.format(self.sql.tables.alarm_metadata, cfga._FT3_ALARM_SQL_FOREIGN_KEY)
                    conn.execute(uq)

            df.to_sql(name=self.sql.tables.alarm_metadata, con=engine, if_exists="append", index=False)


            # SQL database alarm-state summary-count tables
            # corresponding to current limits/wires profile
            
            #SQL database NONE alarm-state count table
            _n = pd.DataFrame(data=_A[_A == ssdata.AlarmState.none].count().values.reshape(1,-1), columns=_A.columns)
            df = pd.concat((_profile,_n), axis=1)

            # Create empty NONE alarm-state count table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.alarm_none):
                args = [self.sql.tables.alarm_none, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.alarm_none, cfga._FT3_ALARM_SQL_FOREIGN_KEY,
                                   self.sql.tables.alarm_metadata, cfga._FT3_ALARM_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.alarm_none, con=engine, if_exists="append", index=False)


            #SQL database WARN-LOW alarm-state count table
            _n = pd.DataFrame(data=_A[_A == ssdata.AlarmState.warn_low].count().values.reshape(1,-1), columns=_A.columns)
            df = pd.concat((_profile,_n), axis=1)

            # Create empty WARN-LOW alarm-state count table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.warn_low):
                args = [self.sql.tables.warn_low, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.warn_low, cfga._FT3_ALARM_SQL_FOREIGN_KEY,
                                   self.sql.tables.alarm_metadata, cfga._FT3_ALARM_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.warn_low, con=engine, if_exists="append", index=False)


            #SQL database WARN-HIGH alarm-state count table
            _n = pd.DataFrame(data=_A[_A == ssdata.AlarmState.warn_high].count().values.reshape(1,-1), columns=_A.columns)
            df = pd.concat((_profile,_n), axis=1)

            # Create empty WARN-HIGH alarm-state count table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.warn_high):
                args = [self.sql.tables.warn_high, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.warn_high, cfga._FT3_ALARM_SQL_FOREIGN_KEY,
                                   self.sql.tables.alarm_metadata, cfga._FT3_ALARM_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.warn_high, con=engine, if_exists="append", index=False)


            #SQL database ALARM-LOW alarm-state count table
            _n = pd.DataFrame(data=_A[_A == ssdata.AlarmState.alarm_low].count().values.reshape(1,-1), columns=_A.columns)
            df = pd.concat((_profile,_n), axis=1)

            # Create empty ALARM-LOW alarm-state count table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.alarm_low):
                args = [self.sql.tables.alarm_low, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.alarm_low, cfga._FT3_ALARM_SQL_FOREIGN_KEY,
                                   self.sql.tables.alarm_metadata, cfga._FT3_ALARM_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.alarm_low, con=engine, if_exists="append", index=False)


            #SQL database ALARM-HIGH alarm-state count table
            _n = pd.DataFrame(data=_A[_A == ssdata.AlarmState.alarm_high].count().values.reshape(1,-1), columns=_A.columns)
            df = pd.concat((_profile,_n), axis=1)

            # Create empty ALARM-HIGH alarm-state count table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.alarm_high):
                args = [self.sql.tables.alarm_high, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.alarm_high, cfga._FT3_ALARM_SQL_FOREIGN_KEY,
                                   self.sql.tables.alarm_metadata, cfga._FT3_ALARM_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.alarm_high, con=engine, if_exists="append", index=False)


            #SQL database UNKNOWN alarm-state count table
            _n = pd.DataFrame(data=_A[_A == ssdata.AlarmState.unknown].count().values.reshape(1,-1), columns=_A.columns)
            df = pd.concat((_profile,_n), axis=1)

            # Create empty UNKNOWN alarm-state count table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.alarm_unknown):
                args = [self.sql.tables.alarm_unknown, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.alarm_unknown, cfga._FT3_ALARM_SQL_FOREIGN_KEY,
                                   self.sql.tables.alarm_metadata, cfga._FT3_ALARM_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.alarm_unknown, con=engine, if_exists="append", index=False)


            # SQL database parameter limits/wires table
            lw = self.session.part.param.data.limits_wires.copy()
            pid = _profile.repeat(len(lw)).reset_index(drop=True)
            df = pd.concat((pid, lw), axis=1)


            # Create empty parameter limits/wires table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.limits_wires):
                args = [self.sql.tables.limits_wires, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.limits_wires, cfga._FT3_ALARM_SQL_FOREIGN_KEY,
                                   self.sql.tables.alarm_metadata, cfga._FT3_ALARM_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.limits_wires, con=engine, if_exists="append", index=False)


            if self.verbose >= util.VerboseLevel.debug:
                ts0 = util._FT3_UTIL_NOW_TS()

            # SQL database alarm-state table
            # NB: Tabulate only alarm/warn/unknown exemplars
            _k = (_A != ssdata.AlarmState.none).any(axis=1)

            r = [e for e in ssdata.AlarmState]
            x = [e.name for e in ssdata.AlarmState]
            _A.replace(to_replace=r, value=x, inplace=True)

            pid = _profile.repeat(num_shot).reset_index(drop=True)
            df = pd.concat((pid,_s,_A), axis=1)
            df = df[_k].reset_index(drop=True)

            # Create empty parameter alarm-state table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.alarm_state):
                args = [self.sql.tables.alarm_state, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

                with engine.connect() as conn:
                    fk = 'alter table "{0:s}" add foreign key ({1:s}) references "{2:s}" ({3:s}) on delete CASCADE;'
                    fk = fk.format(self.sql.tables.alarm_state, cfga._FT3_ALARM_SQL_FOREIGN_KEY,
                                   self.sql.tables.alarm_metadata, cfga._FT3_ALARM_SQL_FOREIGN_KEY)
                    conn.execute(fk)

            df.to_sql(name=self.sql.tables.alarm_state, con=engine, if_exists="append", index=False)

            if self.verbose >= util.VerboseLevel.debug:
                ts1 = util._FT3_UTIL_NOW_TS()
                print("")
                util._FT3_UTIL_VERBOSE_DEBUG_WITH_TS(_methodname)
                print("write SQL database alarm-state table elapsed time")
                print("{} ELAPSED TIME {}".format(util._FT3_UTIL_NOW(), ts1-ts0))
                print("")
                sys.stdout.flush()

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
                conn = cfga._FT3_ALARM_SQL_CONN_PREFIX
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
