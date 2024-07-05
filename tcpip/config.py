#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import struct

import board.config as cfgb


_FT3_TCPIP_CLIENT_HOST_DEFAULT = str(cfgb._FT3_BOARD_IP_DEFAULT)
_FT3_TCPIP_CLIENT_PORT_DEFAULT = 31000

_FT3_TCPIP_CLIENT_RECV_TIMEOUT = struct.pack('ll',3,0) # 0,0 for no recv-timeout

_FT3_TCPIP_CLIENT_CONNECT_RETRY_NUM = 10
_FT3_TCPIP_CLIENT_CONNECT_RETRY_S   = 1.00


_FT3_TCPIP_SELECT_WAIT_IO_TIMEOUT_S = 5.00

_FT3_TCPIP_HEARTBEAT_PERIOD_MS = 30000
_FT3_TCPIP_HEARTBEAT_MSG       = '*\r'
