#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 TCP/IP client
"""
import sys

from threading import Thread
import select

import socket
import struct

import ipaddress

import time

import tcpip.config as cfgt
import tcpip.msgdata as msg
import tcpip.callbacks as cb

import board.config as cfgb

import util.util as util


class Client(object):
    def __init__(self, board=None, sock=None, verbose=util.VerboseLevel.info):
        """Initialize FasTrak3 TCP/IP client socket
        """
        self.board = board # FasTrak3 board reference

        self._verbose = verbose

        if sock is None:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, cfgt._FT3_TCPIP_CLIENT_RECV_TIMEOUT)
        else:
            self._socket = sock

        self._local = None
        self._peer = None

        self.cb = cb.Callbacks(board=board, verbose=verbose)

        if ipaddress.ip_address(self.board.ip) == cfgb._FT3_BOARD_IP_LOCALHOST:
            self.super_thread = None
        else:
            self.super_thread = Thread(target=self._supervisor, daemon=False)
            self.super_thread.start()

    def connect(self, port=cfgt._FT3_TCPIP_CLIENT_PORT_DEFAULT):
        """Connect to host
        """
        _methodname = self.connect.__name__

        retry = cfgt._FT3_TCPIP_CLIENT_CONNECT_RETRY_NUM
        remoh = (ipaddress.ip_address(self.board.ip) != cfgb._FT3_BOARD_IP_LOCALHOST)

        while retry and remoh:
            try:
                self._socket.connect((str(self.board.ip),port))
                break
            except OSError as e:
                retry -= 1

                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, cfgt._FT3_TCPIP_CLIENT_RECV_TIMEOUT)

                if self._verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("connect exception e {}".format(e))
                    sys.stdout.flush()
                time.sleep(cfgt._FT3_TCPIP_CLIENT_CONNECT_RETRY_S)

        c = self._local = self._socket.getsockname()
        try:
            s = self._peer = self._socket.getpeername()
        except OSError as e:
            if e.errno == 57:
                # [Errno 57] Socket is not connected
                s = self._peer = None
        
        if self._verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("socket client {}:{}".format(c[0], c[1]))
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("socket server {}:{}".format(s[0], s[1]))
            sys.stdout.flush()

    def close(self):
        """Close FasTrak3 TCP/IP client socket
        """
        _methodname = self.close.__name__

        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except OSError as e:
            if self._verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("shutdown exception e {}".format(e))
                sys.stdout.flush()

        self._socket.close()

    def reset(self):
        """Reset FasTrak3 TCP/IP client socket
           (Close and reconnect to peer)
        """
        _methodname = self.reset.__name__

        if self._verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("socket reconnect")
            sys.stdout.flush()

        self.close()
        if self._peer is not None:
            self.connect(self._peer[0], self._peer[1])

    def send(self, m):
        """Send message
        """
        _methodname = self.send.__name__

        if self._verbose >= util.VerboseLevel.info:
            h = self._socket.getpeername()
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("send data (N={:5d}) to {}:{}".format(len(m), h[0], h[1]))
            sys.stdout.flush()

        b = m.encode()
        self._socket.sendall(b)

        if self.cb.fcn.send_cmd is not None:
            _m = msg.CmdData(data=b)
            self.cb.fcn.send_cmd(_m)

    def recv(self):
        """Receive message
        """
        _methodname = self.recv.__name__

        # Message framing
        rv = self._recv_helper(msg._FT3_TCPIP_MSG_FRAME_LEN)
        if not rv:
            return
        _u = ord(rv)

        is_async = msg._FT3_TCPIP_IS_ASYNC(_u)
        rv = msg._FT3_TCPIP_UNSET_ASYNC(_u)

        if not is_async:
            # Read resp data
            rv += self._recv_helper(msg._FT3_TCPIP_RESP_LEN - 1)

            if self.cb.fcn.recv_resp is not None:
                _m = msg.RespData(data=rv)
                self.cb.fcn.recv_resp(_m)

            return
        else:
            # Read async header
            rv += self._recv_helper(msg._FT3_TCPIP_ASYNC_HEADER_LEN - 1)
            if not rv:
                return

        # Unpack async header
        try:
            hdr = msg.AsyncHeader(*struct.unpack(msg._FT3_TCPIP_ASYNC_HEADER_FORMAT, rv))
        except Exception as e:
            if self._verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("header unpack exception e {}".format(e))
                sys.stdout.flush()

            self.reset()
            return None

        # Header consistency checks
        # TODO ...

        # Read async data
        rv = self._recv_helper(hdr.num_bytes)
        if not rv:
            # None on EOF (socket closed or no data)
            if self._verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("EOF")
                sys.stdout.flush()

            self.reset()
            return None

        if self.cb.fcn.recv_async is not None:
            _m = msg.AsyncData(header=hdr, data=rv)
            self.cb.fcn.recv_async(_m)

    def _recv_helper(self, n):
        """Receive message helper
           Read n bytes
        """
        _methodname = self._recv_helper.__name__

        data = b''

        while len(data) < n:
            try:
                p = self._socket.recv(n - len(data))
                if not p:
                    # None on EOF (socket closed or no data)
                    if self._verbose >= util.VerboseLevel.error:
                        util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                        print("EOF")
                        sys.stdout.flush()
                    return None
                data += p
            #except OSError as e:
            #    #self.reset()
            #    if self._verbose >= util.VerboseLevel.error:
            #        util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
            #        print("OSError socket exception e {}".format(e))
            #        sys.stdout.flush()
            #    return None
            except Exception as e:
                if self._verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("recv exception e {}".format(e))
                    sys.stdout.flush()

        return data


    def _supervisor(self):
        """FasTrak3 TCP/IP connection supervisor
        """
        _methodname = self._supervisor.__name__

        while True:
            S = [self._socket] + [sys.stdin]

            try:
                inp,outp,err = select.select(S,[],S,
                                             cfgt._FT3_TCPIP_SELECT_WAIT_IO_TIMEOUT_S)
            except Exception as e:
                if self._verbose >= util.VerboseLevel.error:
                    util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                    print("select exception e {}".format(e))
                    sys.stdout.flush()
                inp,outp,err = select.select([sys.stdin],[],[sys.stdin],
                                             cfgt._FT3_TCPIP_SELECT_WAIT_IO_TIMEOUT_S)

            for s in inp:
                if s == sys.stdin:
                    # Get command from stdin
                    m = sys.stdin.readline()
                    if m:
                        try:
                            # Send message over command/response socket
                            self.send(m.encode())
                        except Exception as e:
                            if self._verbose >= util.VerboseLevel.error:
                                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                                print("send exception e {}".format(e))
                                sys.stdout.flush()
                else:
                    try:
                        # Receive message over command/response or data socket
                        self.recv()
                    except Exception as e:
                        if self._verbose >= util.VerboseLevel.error:
                            util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                            print("recv exception e {}".format(e))
                            sys.stdout.flush()

            for s in outp:
                if self._verbose >= util.VerboseLevel.warn:
                    util._FT3_UTIL_VERBOSE_WARN_WITH_TS(_methodname)
                    print("unhandled select output {}".format(s))
                    sys.stdout.flush()
            for s in err:
                if self._verbose >= util.VerboseLevel.warn:
                    util._FT3_UTIL_VERBOSE_WARN_WITH_TS(_methodname)
                    print("unhandled select error {}".format(s))
                    sys.stdout.flush()

        return

    def _heartbeat(self):
        """FasTrak3 TCP/IP heartbeat (echo-request) transmit
        """
        _methodname = self._heartbeat.__name__

        if self._verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("TCP/IP heartbeat transmit")
            sys.stdout.flush()

        try:
            self.send(cfgt._FT3_TCPIP_HEARTBEAT_MSG)
        except Exception as e:
            if self._verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("TCP/IP heartbeat transmit exception e {}".format(e))
                sys.stdout.flush()


    @property
    def socket(self):
        """Get socket
        """
        return self._socket
    
    @socket.setter
    def socket(self, val):
        """Set socket
        """
        self.close()
        self._socket = val

    @property
    def local(self):
        """Get local (IP,port)
        """
        return self._local

    @local.setter
    def local(self, val):
        """Set local (IP,port)
        """
        pass # Disallow manual specification of source address

    @property
    def peer(self):
        """Get peer
        """
        return self._peer

    @peer.setter
    def peer(self, val):
        """Set peer
        """
        self.close()
        self._peer = val
        self.reset()
        
    @property
    def verbose(self):
        """Get verbose Boolean
        """
        return self._verbose
    
    @verbose.setter
    def verbose(self, val):
        """Set verbose Boolean
        """
        self._verbose = val
