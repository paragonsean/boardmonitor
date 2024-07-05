#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 die-cast/injection-molding part interface
"""
import sys

import os
import copy
import dill

import numpy as np

from dataclasses import dataclass

import param.param as param

import part.config as cfgpt
import util.util as util


@dataclass
class Stroke:
    minimum: np.float
    total  : np.float

@dataclass
class Plunger:
    # P1: plunger position @ shot-sleeve full
    # P2: plunger position @ metal-at-gate
    # P3: plunger position @ part-cavity full
    p1_p3: np.float # P3 - P1 
    p2_p3: np.float # P3 - P2

@dataclass
class CSFS:
    min_pos: np.float
    min_vel: np.float

@dataclass
class Intensification:
    p_target: np.float # intensification rise-time target pressure (MPa)
    pk_skip : int      # intensification peak pressure skip counts (---)

@dataclass
class SlowShotVariation:
    start_pos_user: np.float
    end_pos_user  : np.float
    start_pos_init: np.float
    start_pos_bias: np.float
    start_pos_gain: np.float
    end_pos_bias  : np.float


class Part(object):
    def __init__(self, session=None, name=cfgpt._FT3_PART_NAME_DEFAULT, verbose=util.VerboseLevel.info):
        _methodname = self.__init__.__name__

        self.session = session
        self.verbose = verbose

        self._name = name

        self.param = param.Param(session, verbose=verbose) # Monitored parameter alarm limits/wires

        self.stroke = Stroke(minimum=cfgpt._FT3_PART_MINIMUM_STROKE_LENGTH_MM,
                             total=cfgpt._FT3_PART_TOTAL_STROKE_LENGTH_MM)

        self.plunger = Plunger(p1_p3=cfgpt._FT3_PART_P1_P3_DISTANCE_MM,
                               p2_p3=cfgpt._FT3_PART_P2_P3_DISTANCE_MM)

        self.csfs = CSFS(min_pos=cfgpt._FT3_PART_CSFS_MIN_POS_MM,
                         min_vel=cfgpt._FT3_PART_CSFS_MIN_VEL_MM_PER_SEC)

        self.intens = Intensification(p_target=cfgpt._FT3_PART_INTENS_RISE_TIME_TARGET_PRESSURE_MPA,
                                      pk_skip=cfgpt._FT3_PART_INTENS_PEAK_PRESSURE_SKIP_COUNTS)

        self.ss_var = SlowShotVariation(start_pos_user=cfgpt._FT3_PART_SS_VAR_START_POS_USER_MM,
                                        end_pos_user=cfgpt._FT3_PART_SS_VAR_END_POS_USER_MM,
                                        start_pos_init=cfgpt._FT3_PART_SS_VAR_START_POS_INIT_MM,
                                        start_pos_bias=cfgpt._FT3_PART_SS_VAR_START_POS_BIAS_MM,
                                        start_pos_gain=cfgpt._FT3_PART_SS_VAR_START_POS_GAIN,
                                        end_pos_bias=cfgpt._FT3_PART_SS_VAR_END_POS_BIAS_MM)

        if self.verbose >= util.VerboseLevel.info:
            util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
            print("part initialized")
            sys.stdout.flush()

    def bind(self, session):
        """Bind FasTrak3 server session to part
        """
        self.session = self.param.session = session

    def unbind(self):
        """Unbind FasTrak3 server session from part
        """
        self.session = self.param.session = None

    def copy(self):
        """Copy part
        """
        _part = copy.deepcopy(self)
        _part.unbind() # Unbind FasTrak3 server session reference
        return _part 

    def save(self, filename=None):
        """Save part
        """
        _methodname = self.save.__name__

        try:
            if filename is not None:
                _filename = filename
            else:
                _filename = cfgpt._FT3_PART_PARTS_FILENAME_PREFIX + '_' + util._FT3_UTIL_NOW_FID() + '.pkl'

            _f = os.path.join(cfgpt._FT3_PART_PARTS_ABSPATH,_filename)
            _part = self.copy()

            fid = open(file=_f, mode='wb')
            dill.dump(obj=_part, file=fid)
            fid.close()
            
            if self.verbose >= util.VerboseLevel.info:
                util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
                print("part save to {}".format(_f))
                sys.stdout.flush()
        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("part save exception e {}".format(e))
                sys.stdout.flush()

    @staticmethod
    def load(filename):
        """Load part
        """
        _methodname = Part.load.__name__

        try:
            _f = os.path.join(cfgpt._FT3_PART_PARTS_ABSPATH,filename)
            fid = open(file=_f, mode='rb')
            _part = dill.load(file=fid)
            fid.close()

            if _part.verbose >= util.VerboseLevel.info:
                util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
                print("part load from {}".format(_f))
                sys.stdout.flush()

            return _part
        except Exception as e:
            util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
            print("part load exception e {}".format(e))
            sys.stdout.flush()

    @property
    def name(self):
        """Get part name
        """
        return self._name

    @name.setter
    def name(self, val):
        """Set part name
        """
        self._name = val
        # TODO ... part name uniqueness enforcement
