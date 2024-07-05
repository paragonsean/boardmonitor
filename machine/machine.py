#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 die-cast/injection-molding machine interface
"""
import sys

import os
import copy
import dill

import numpy as np

from dataclasses import dataclass

import machine.config as cfgm

import util.util as util
import units.units as units


@dataclass
class Rod:
    name  : str
    _type : cfgm.RodType
    _units: units.UnitSystem
    _pitch: np.float # Rod pitch in native units
    pitch : np.float # Rod pitch in SI units

@dataclass
class MachineGeometry:
    head_area   : np.float
    rod_area    : np.float
    plunger_area: np.float

@dataclass
class MachineTimeouts:
    down : np.float  # Machine down (offline)
    cycle: np.float  # Cycle time


class Machine(object):
    def __init__(self, session=None, name=cfgm._FT3_MACHINE_NAME_DEFAULT, rod_type=cfgm._FT3_MACHINE_ROD_TYPE_DEFAULT, verbose=util.VerboseLevel.info):
        _methodname = self.__init__.__name__

        self.session = session
        self.verbose = verbose

        self._name = name

        # Rod
        if rod_type == cfgm.RodType.tpi_20:
            _r = Rod(name='20 threads/in',
                     _type=rod_type,
                     _units=units.UnitSystem.bg,
                     _pitch=1.0/20.0,
                     pitch=1.0/20.0/units._FT3_UNITS_MM_TO_IN)
        elif rod_type == cfgm.RodType.pmm_2:
            _r = Rod(name='2mm pitch',
                     _type=rod_type,
                     _units=units.UnitSystem.si,
                     _pitch=2.0,
                     pitch=2.0)
        elif rod_type == cfgm.RodType.pmm_4:
            _r = Rod(name='4mm pitch',
                     _type=rod_type,
                     _units=units.UnitSystem.si,
                     _pitch=4.0,
                     pitch=4.0)
        else:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("unknown rod type {}".format(rod_type))
                sys.stdout.flush()
            return

        self.rod = _r

        # Machine geometry
        self.geom = MachineGeometry(head_area=cfgm._FT3_MACHINE_HEAD_AREA_MM_SQ,
                                    rod_area=cfgm._FT3_MACHINE_ROD_AREA_MM_SQ,
                                    plunger_area=cfgm._FT3_MACHINE_PLUNGER_AREA_MM_SQ)

        # Quadrature divisor
        self._qdiv = cfgm._FT3_MACHINE_QUADRATURE_DIVISOR_DEFAULT

        # Machine timeouts
        self.timeouts = MachineTimeouts(down=cfgm._FT3_MACHINE_DOWN_TIMEOUT_DEFAULT_S,
                                        cycle=cfgm._FT3_MACHINE_CYCLE_TIME_DEFAULT_S)

    def bind(self, session):
        """Bind FasTrak3 server session to machine
        """
        self.session = session

    def unbind(self):
        """Unbind FasTrak3 server session from machine
        """
        self.session = None

    def copy(self):
        """Copy machine
        """
        _machine = copy.deepcopy(self)
        _machine.unbind() # Unbind FasTrak3 server session reference
        return _machine

    def save(self, filename=None):
        """Save machine
        """
        _methodname = self.save.__name__

        try:
            if filename is not None:
                _filename = filename
            else:
                _filename = cfgm._FT3_MACHINE_MACHINES_FILENAME_PREFIX + '_' + util._FT3_UTIL_NOW_FID() + '.pkl'

            _f = os.path.join(cfgm._FT3_MACHINE_MACHINES_ABSPATH,_filename)
            _machine = self.copy()

            fid = open(file=_f, mode='wb')
            dill.dump(obj=_machine, file=fid)
            fid.close()
            
            if self.verbose >= util.VerboseLevel.info:
                util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
                print("machine save to {}".format(_f))
                sys.stdout.flush()
        except Exception as e:
            if self.verbose >= util.VerboseLevel.error:
                util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
                print("machine save exception e {}".format(e))
                sys.stdout.flush()

    @staticmethod
    def load(filename):
        """Load machine
        """
        _methodname = Machine.load.__name__

        try:
            _f = os.path.join(cfgm._FT3_MACHINE_MACHINES_ABSPATH,filename)
            fid = open(file=_f, mode='rb')
            _machine = dill.load(file=fid)
            fid.close()

            if _machine.verbose >= util.VerboseLevel.info:
                util._FT3_UTIL_VERBOSE_INFO_WITH_TS(_methodname)
                print("machine load from {}".format(_f))
                sys.stdout.flush()

            return _machine
        except Exception as e:
            util._FT3_UTIL_VERBOSE_ERROR_WITH_TS(_methodname)
            print("machine load exception e {}".format(e))
            sys.stdout.flush()

    @property
    def name(self):
        """Get machine name
        """
        return self._name

    @name.setter
    def name(self, val):
        """Set machine name
        """
        self._name = val
        # TODO ... machine name uniqueness enforcement

    @property
    def qdiv(self):
        """Get quadrature divisor
        """
        return self._qdiv

    @qdiv.setter
    def qdiv(self, val):
        self._qdiv = min(max(np.uint8(val), cfgm._FT3_MACHINE_QUADRATURE_DIVISOR_MIN), cfgm._FT3_MACHINE_QUADRATURE_DIVISOR_MAX)
        # TODO ... Transmit quadrature divisor to FasTrak3 board via CONFIG WORD 2
