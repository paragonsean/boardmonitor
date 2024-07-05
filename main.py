#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import sys
import getopt

import pandas as pd

import ipaddress

import server.server as server

import board.config as cfgb
import alert.config as cfga

import util.util as util
import units.units as units

# Initialize program arguments.
lo = True
names = [cfgb._FT3_BOARD_NAME_DEFAULT]
ips = [cfgb._FT3_BOARD_IP_DEFAULT]
verbose = True
unitsys = units.UnitSystem.bg


# Parse program arguments.
opts,args = getopt.getopt(sys.argv[1:], "hl:n:i:u:p:", ["help", "localhost=", "name=", "ip=", "units=", "print="])
for opt,arg in opts:
    if opt in ("-h", "--help"):
        print("")
        print("")
        print("{} USAGE ...".format(__name__))
        print("    bokeh serve ft3server.py --port=5006 --allow-websocket-origin=* --args -h")
        print("    bokeh serve ft3server.py --port=5006 --allow-websocket-origin=* --args --help")
        print("    bokeh serve ft3server.py --port=5006 --allow-websocket-origin=* --args -l <yes|no> -n <unitname,...> -i <#.#.#.#,...> -u=<bg|si> -v <yes|no>")
        print("    bokeh serve ft3server.py --port=5006 --allow-websocket-origin=* --args --looalhost=<yes|no> --name=<unitname,...> --ip=<#.#.#.#,...> --units=<bg|si> --verbose=<yes|no>")
        print("")
        print("where:")
        print("--args are arguments to the FasTrak3 web server, i.e.")
        print("    -h, --help      Switch to print this help message.")
        print("    -l, --localhost Localhost FasTrak3 data Boolean.")
        print("    -n, --name      Name(s) of FasTrak3 unit(s).")
        print("    -i, --ip        IP(s) of FasTrak3 unit(s).")
        print("    -u, --units     Unit system.")
        print("    -v, --verbose   Verbose printout Boolean.")
        print("")
        print("Default settings for unspecified arguments are --localhost=y --name={} --ip={} --units=bg --verbose=n".format(cfgb._FT3_BOARD_NAME_DEFAULT,cfgb._FT3_BOARD_IP_DEFAULT))
        print("")
        print("NB: -l/--localhost option uses FasTrak3 example dataset maintained locally on server,")
        print("                   ignoring (name,ip) arguments")
        print("    -n/--name and -i/--ip options define FasTrak3 units to connect to and stream shot")
        print("                   datasets if not using the localhost mode")
        print("")
        print("")
        sys.stdout.flush()
    elif opt in ("-l", "--localhost"):
        if arg in ("YES", "Yes", "yes", "Y", "y", "TRUE", "True", "true", "T", "t", "1"):
            lo = True
        else:
            lo = False
    elif opt in ("-n", "--name"):
        names = arg.split(',')
    elif opt in ("-i", "--ip"):
        boards = arg.replace(' ','').split(',')
        ips = [ipaddress.ip_address(board) for board in boards]
    elif opt in ("-u", "--units"):
        if arg in ("si", "SI"):
            unitsys = units.UnitSystem.si
    elif opt in ("-v", "--verbose"):
        if arg in ("YES", "Yes", "yes", "Y", "y", "TRUE", "True", "true", "T", "t", "1"):
            verbose = util.VerboseLevel.profile
        else:
            verbose = util.VerboseLevel.off

if lo:
    names = [cfgb._FT3_BOARD_NAME_LOCALHOST]
    ips = [cfgb._FT3_BOARD_IP_LOCALHOST]
else:
    names = [n.strip() for n in names]


util._FT3_UTIL_VERBOSE_INFO_WITH_TS("main")
print("FasTrak3 web interface application server session")
print("")
sys.stdout.flush()

S = server.Session(names=names, ips=ips, unitsys=unitsys, verbose=verbose)

# TEMPORARY ... simulator/demo support
try:
    Bd = S.board
    Bd._sql_conn()
    _meta = pd.read_sql_table(table_name=Bd.sql.tables.meta, con=Bd.sql.engine)
    S.document.session_context.shot = _meta.shot.max()
except Exception as e:
    if verbose >= util.VerboseLevel.error:
         util._FT3_UTIL_VERBOSE_ERROR_WITH_TS('main')
         print("SQL maximum shot query exception e {}".format(e))
         print("")
         sys.stdout.flush()

# TEMPORARY ... simulator/demo support
try:
    A = S.alert

    # Subscribe an e-mail recipient to (low,high) alarm notifications
    # NB: subscribe() supports repeated calls for multiple recipients
    email = 'mproske@visi-trak.com'
    A.subscribe(email=email)

    # Subscribe a mobile/SMS recipient to (low,high) alarm notifications
    # NB: subscribe() supports repeated calls for multiple recipients
    sms = cfga._FT3_ALERT_MMS_ATT_RECIPIENT(3306762135)
    A.subscribe(sms=sms)
    sms = cfga._FT3_ALERT_MMS_VERIZON_RECIPIENT(2165700418)
    A.subscribe(sms=sms)
    sms = cfga._FT3_ALERT_MMS_VERIZON_RECIPIENT(2163181005)
    A.subscribe(sms=sms)

except Exception as e:
    if verbose >= util.VerboseLevel.error:
        util._FT3_UTIL_VERBOSE_ERROR_WITH_TS('main')
        print("E-mail/SMS alert exception e {}".format(e))
        print("")
        sys.stdout.flush()
