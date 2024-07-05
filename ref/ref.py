#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import sys

import pandas as pd

from dataclasses import dataclass

import sqlalchemy as sqla
import sqlalchemy_utils as sqlu

import ref.config as cfgr
import util.util as util


@dataclass
class Data:
    meta  : pd.DataFrame
    shot  : pd.DataFrame
    events: pd.DataFrame

@dataclass
class SQLDatabase:
    name: str
    pdio: pd.io.sql.SQLDatabase
    
@dataclass
class SQLTables:
    ref_meta  : str
    ref_shot  : str
    ref_events: str

@dataclass
class RefSQL:
    engine  : sqla.engine.base.Engine

    user    : str
    password: str
    server  : str
    
    database: SQLDatabase
    tables  : SQLTables


class Ref(object):
    def __init__(self, session=None, read=True, verbose=util.VerboseLevel.info):
        """Initialize FasTrak3 reference shot
        """
        self.session = session
        self.verbose = verbose

        self._data = Data(meta=pd.DataFrame(),
                          shot=pd.DataFrame(),
                          events=pd.DataFrame())

        _db = SQLDatabase(name=cfgr._FT3_REF_SQL_DATABASE+'_'+str(session.board.ip).replace('.','_'),
                          pdio=None)
        _tables = SQLTables(ref_meta=cfgr._FT3_REF_SQL_META_TABLE,
                            ref_shot=cfgr._FT3_REF_SQL_SHOT_TABLE,
                            ref_events=cfgr._FT3_REF_SQL_EVENTS_TABLE)

        self.sql = RefSQL(engine=None,
                          user=cfgr._FT3_REF_SQL_USER,
                          password=cfgr._FT3_REF_SQL_PASSWORD,
                          server=cfgr._FT3_REF_SQL_SERVER,
                          database=_db,
                          tables=_tables)

        if read:
            self.read()

    def read(self):
        """Read FasTrak3 reference shot
        """
        _methodname = self.read.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("read FasTrak3 reference shot")
            sys.stdout.flush()

        try:
            self._sql_conn()

            engine = self.sql.engine

            # Reference metadata, shot, and events
            self._data.meta = pd.read_sql_table(table_name=self.sql.tables.ref_meta, con=engine)
            self._data.shot = pd.read_sql_table(table_name=self.sql.tables.ref_shot, con=engine)
            self._data.events = pd.read_sql_table(table_name=self.sql.tables.ref_events, con=engine)

        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("read SQL database exception e {}".format(e))
                sys.stdout.flush()
            
    def write(self):
        """Write FasTrak3 reference shot
        """
        _methodname = self.write.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("write FasTrak3 reference shot")
            sys.stdout.flush()

        try:
            self._sql_conn()

            engine = self.sql.engine
            sqldb = self.sql.database.pdio


            # Reference metadata
            df = self._data.meta

            # Create reference metadata table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.ref_meta):
                args = [self.sql.tables.ref_meta, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

            df.to_sql(name=self.sql.tables.ref_meta, con=engine, if_exists="replace", index=False)


            # Reference shot data
            df = self._data.shot

            # Create reference shot table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.ref_shot):
                args = [self.sql.tables.ref_shot, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

            df.to_sql(name=self.sql.tables.ref_shot, con=engine, if_exists="replace", index=False)


            # Reference events
            df = self._data.events

            # Create reference events table
            # NB: Pandas io.sql.SQLDatabase() function
            #     to include autoincrement primary key
            if not sqldb.has_table(name=self.sql.tables.ref_events):
                args = [self.sql.tables.ref_events, sqldb]
                kwargs = {
                    "frame" : df,
                    "index" : True, 
                    "index_label" : "id",
                    "keys" : "id"}
                pd.io.sql.SQLTable(*args, **kwargs).create()

            df.to_sql(name=self.sql.tables.ref_events, con=engine, if_exists="replace", index=False)

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
                conn = cfgr._FT3_REF_SQL_CONN_PREFIX
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

    @property
    def data(self):
        """Get reference data
        """
        return self._data

    @data.setter
    def data(self, value):
        """Set reference data
        """
        self._data = value
        self._write()
