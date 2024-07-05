#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import numpy as np

from enum import IntEnum,unique
from dataclasses import dataclass

import ad.config as cfgad


_FT3_TCPIP_MSG_FRAME_LEN = 1
_FT3_TCPIP_RESP_LEN      = 256

_FT3_TCPIP_ASYNC_BUFFER_LEN  = 1350 # Maximum length of async Tx
_FT3_TCPIP_ASYNC_HEADER_LEN  = 12   # Binary header length of async Tx
_FT3_TCPIP_ASYNC_DATA_LEN    =  _FT3_TCPIP_ASYNC_BUFFER_LEN - _FT3_TCPIP_ASYNC_HEADER_LEN

_FT3_TCPIP_ASYNC_BIT   = (1 << 7)
_FT3_TCPIP_IS_ASYNC    = lambda x: (np.uint8(x) & _FT3_TCPIP_ASYNC_BIT).any()
_FT3_TCPIP_UNSET_ASYNC = lambda x: bytes([(np.uint8(x) & ~_FT3_TCPIP_ASYNC_BIT)])


@unique
class AsyncHeaderIndex(IntEnum):
    bin_id      = 0
    bin_type    = 1
    flags       = 2
    dataset_num = 3
    packet_num  = 4
    num_packets = 5
    num_bytes   = 6
    numel       = 7

_Fi = [''] * AsyncHeaderIndex.numel
_Fi[0] = _FT3_TCPIP_ASYNC_HEADER_FORMAT_BIN_ID      = 'B'
_Fi[1] = _FT3_TCPIP_ASYNC_HEADER_FORMAT_BIN_TYPE    = 'B'
_Fi[2] = _FT3_TCPIP_ASYNC_HEADER_FORMAT_FLAGS       = 'H'
_Fi[3] = _FT3_TCPIP_ASYNC_HEADER_FORMAT_DATASET_NUM = 'H'
_Fi[4] = _FT3_TCPIP_ASYNC_HEADER_FORMAT_PACKET_NUM  = 'H'
_Fi[5] = _FT3_TCPIP_ASYNC_HEADER_FORMAT_NUM_PACKETS = 'H'
_Fi[6] = _FT3_TCPIP_ASYNC_HEADER_FORMAT_NUM_BYTES   = 'H'

_FT3_TCPIP_ASYNC_HEADER_FORMAT = '<' + ''.join(_Fi)

@dataclass
class AsyncHeader:
    bin_id     : np.uint8
    bin_type   : np.uint8
    flags      : np.uint16
    dataset_num: np.uint16
    packet_num : np.uint16
    num_packets: np.uint16
    num_bytes  : np.uint16


@unique
class AsyncShotDataIndex(IntEnum):
    ana_ch1      = 0
    ana_ch2      = 1
    ana_ch3      = 2
    ana_ch4      = 3
    ana_ch5      = 4
    ana_ch6      = 5
    ana_ch7      = 6
    ana_ch8      = 7
    vel_count_q1 = 8
    vel_count_q2 = 9
    vel_count_q3 = 10
    vel_count_q4 = 11
    isw1         = 12
    isw4         = 13
    osw1         = 14
    one_ms_timer = 15
    position     = 16
    sample_num   = 17
    numel        = 18

_Fi = [''] * AsyncShotDataIndex.numel
_Fi[0]  = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ANA_CH1      = 'H'
_Fi[1]  = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ANA_CH2      = 'H'
_Fi[2]  = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ANA_CH3      = 'H'
_Fi[3]  = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ANA_CH4      = 'H'
_Fi[4]  = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ANA_CH5      = 'H'
_Fi[5]  = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ANA_CH6      = 'H'
_Fi[6]  = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ANA_CH7      = 'H'
_Fi[7]  = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ANA_CH8      = 'H'
_Fi[8]  = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_VEL_COUNT_Q1 = 'I'
_Fi[9]  = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_VEL_COUNT_Q2 = 'I'
_Fi[10] = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_VEL_COUNT_Q3 = 'I'
_Fi[11] = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_VEL_COUNT_Q4 = 'I'
_Fi[12] = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ISW1         = 'I'
_Fi[13] = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ISW4         = 'I'
_Fi[14] = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_OSW1         = 'I'
_Fi[15] = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_ONE_MS_TIMER = 'I'
_Fi[16] = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_POSITION     = 'i'
_Fi[17] = _FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT_SAMPLE_NUM   = 'I'

_FT3_TCPIP_ASYNC_SHOT_DATA_FORMAT = '<' + ''.join(_Fi)


# Shot data parameter names
_FT3_TCPIP_ASYNC_SHOT_DATA_ANALOG_CHANNELS_NUM    = _N = 8

_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES = []
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += [cfgad._FT3_AD_CHANNEL_NAME(c) for c in range(_N)]
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += ['vel_count_q1']
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += ['vel_count_q2']
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += ['vel_count_q3']
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += ['vel_count_q4']
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += ['isw1']
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += ['isw4']
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += ['osw1']
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += ['one_ms_timer']
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += ['position']
_FT3_TCPIP_ASYNC_SHOT_DATA_PARAMETER_NAMES += ['sample_num']


@unique
class AsyncDataType(IntEnum):
    shot_pos      = 0 # Position-based sample
    shot_time     = 1 # Time-based sample
    shot_comp     = 2 # Computed parameters
    oscope        = 3
    op            = 4
    string        = 5
    io_change     = 6
    single_sample = 7
    block_sample  = 8


@dataclass
class AsyncData:
    header: AsyncHeader
    data  : bytes


@dataclass
class CmdData:
    data: bytes

@dataclass
class RespData:
    data: bytes
