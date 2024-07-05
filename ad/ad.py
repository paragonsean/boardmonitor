#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 A/D channels interface
"""
import sys
import pandas as pd

from dataclasses import dataclass
from bokeh.models import ColumnDataSource

import ad.config as cfgad

import util.util as util
import units.units as units


@dataclass
class Data:
    """FasTrak 3 A/D channels data
    """
    attrib    : pd.DataFrame # A/D channel attributes
    press_head: pd.DataFrame
    press_rod : pd.DataFrame
    press_head_channel: int
    press_rod_channel : int

@dataclass
class Sources:
    """Bokeh model column data source interfaces to data for UIs
    """
    attrib: ColumnDataSource


class Channels(object):
    def __init__(self, session=None, verbose=util.VerboseLevel.info):
        """Initialize FasTrak3 A/D channels
        """
        self.session = session
        self.verbose = verbose

        # Initialize A/D channels and attributes
        self.data = Data(attrib=pd.DataFrame(),
                         press_head=pd.DataFrame(),
                         press_rod=pd.DataFrame(),
                         press_head_channel=cfgad._FT3_AD_PRESSURE_HEAD_CHANNEL_DEFAULT,
                         press_rod_channel=cfgad._FT3_AD_PRESSURE_ROD_CHANNEL_DEFAULT)

        self.sources = Sources(attrib=None)

        _attrib = self.data.attrib = pd.DataFrame(data=None, columns=cfgad._FT3_AD_CHANNELS_ATTRIBUTES_NAMES)
        for (a,p) in zip(cfgad._FT3_AD_CHANNELS_ATTRIBUTES_NAMES, cfgad._FT3_AD_CHANNELS_ATTRIBUTES_DEFAULT):
            _attrib[a] = pd.Series([p] * cfgad._FT3_AD_CHANNELS_NUM)

        for c in range(cfgad._FT3_AD_CHANNELS_NUM):
            _attrib.at[c, 'sensor_name'] = cfgad._FT3_AD_CHANNEL_NAME(c)

        # Head pressure channel
        _ii = self.data.press_head_channel
        _attrib.at[_ii, 'sensor_name']   = 'press_head'
        _attrib.at[_ii, 'sensor_type']   = cfgad.SensorType.pressure
        _attrib.at[_ii, 'ad_mode']       = cfgad._FT3_AD_PRESSURE_HEAD_AD_MODE_DEFAULT
        _attrib.at[_ii, 'volts_min']     = cfgad._FT3_AD_PRESSURE_HEAD_VOLTS_MIN_DEFAULT
        _attrib.at[_ii, 'volts_max']     = cfgad._FT3_AD_PRESSURE_HEAD_VOLTS_MAX_DEFAULT
        _attrib.at[_ii, 'engr_data_min'] = cfgad._FT3_AD_PRESSURE_HEAD_PSI_MIN_DEFAULT / units._FT3_UNITS_MPA_TO_PSI
        _attrib.at[_ii, 'engr_data_max'] = cfgad._FT3_AD_PRESSURE_HEAD_PSI_MAX_DEFAULT / units._FT3_UNITS_MPA_TO_PSI
        _attrib.at[_ii, 'is_press_head'] = True
        _attrib.at[_ii, 'is_press_rod']  = False

        self.data.press_head = pd.Series(data=_attrib.loc[_ii], name='press_head')

        # Rod pressure channel
        _ii = self.data.press_rod_channel
        _attrib.at[_ii, 'sensor_name']   = 'press_rod'
        _attrib.at[_ii, 'sensor_type']   = cfgad.SensorType.pressure
        _attrib.at[_ii, 'ad_mode']       = cfgad._FT3_AD_PRESSURE_ROD_AD_MODE_DEFAULT
        _attrib.at[_ii, 'volts_min']     = cfgad._FT3_AD_PRESSURE_ROD_VOLTS_MIN_DEFAULT
        _attrib.at[_ii, 'volts_max']     = cfgad._FT3_AD_PRESSURE_ROD_VOLTS_MAX_DEFAULT
        _attrib.at[_ii, 'engr_data_min'] = cfgad._FT3_AD_PRESSURE_ROD_PSI_MIN_DEFAULT / units._FT3_UNITS_MPA_TO_PSI
        _attrib.at[_ii, 'engr_data_max'] = cfgad._FT3_AD_PRESSURE_ROD_PSI_MAX_DEFAULT / units._FT3_UNITS_MPA_TO_PSI
        _attrib.at[_ii, 'is_press_head'] = False
        _attrib.at[_ii, 'is_press_rod']  = True

        self.data.press_rod = pd.Series(data=_attrib.loc[_ii], name='press_rod')

    def calc(self, df, c):
        """Calculate engineering units from A/D data for a channel
        """
        _methodname = self.calc.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("calculate engineering data from A/D channel measurements [{}]".format(c))
            sys.stdout.flush()

        try:
            _name = cfgad._FT3_AD_CHANNEL_NAME(c)
            _attr = pd.Series(data=self.data.attrib.loc[c], name=_name)

            _Eu0 = _attr.engr_data_min
            _Eu1 = _attr.engr_data_max

            if _attr.ad_mode == cfgad.ADMode.unsigned:
                _ad = df[_name].apply(cfgad._FT3_AD_DATA_UNSIGNED)
                _m = (_Eu1 - _Eu0) / cfgad._FT3_AD_DATA_RESOLUTION
                _b = _Eu0
            elif _attr.ad_mode == cfgad.ADMode.signed:
                _ad = df[_name].apply(cfgad._FT3_AD_DATA_SIGNED)
                _m = (_Eu1 - _Eu0) / cfgad._FT3_AD_DATA_RESOLUTION
                _b = 0.50 * (_Eu0 + _Eu1)

            rv = _m * _ad + _b
        except Exception as e:
            rv = None
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("channel A/D to engineering data exception e {}".format(e))
                sys.stdout.flush()

        return rv

    def calc_press_head(self, df):
        """Calculate head-pressure (MPa) from A/D data
        """
        _methodname = self.calc_press_head.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("calculate head-pressure from A/D data")
            sys.stdout.flush()

        try:
            rv = self.calc(df, c=self.data.press_head_channel)
        except Exception as e:
            rv = None
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("head-pressure engineering data exception e {}".format(e))
                sys.stdout.flush()

        return rv

    def calc_press_rod(self, df):
        """Calculate rod-pressure (MPa) from A/D data
        """
        _methodname = self.calc_press_rod.__name__

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("calculate rod-pressure from A/D data")
            sys.stdout.flush()

        try:
            rv = self.calc(df, c=self.data.press_rod_channel)
        except Exception as e:
            rv = None
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("rod-pressure engineering data exception e {}".format(e))
                sys.stdout.flush()

        return rv
