#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABSTRACT: Visi-Trak FasTrak3 data extensions
"""
import pandas as pd

from enum import IntEnum,unique

import data.config as cfgd


# NB: Dataframe and series maximum lengths are one element larger
#     than _maxlen property b/c of how overloaded (+=) assignment
#     operators  drop-then-increment datasets


@unique
class FT3DataType(IntEnum):
    meta   = 0
    shot   = 1
    ref    = 2
    param  = 3
    events = 4
    ad     = 5


@pd.api.extensions.register_dataframe_accessor("ft3meta")
class FT3MetaAccessor(object):
    def __init__(self, pd_obj, maxlen=cfgd._FT3_DATA_MAX_LEN):
        """Initialize FasTrak3 metadata
        """
        self._data = pd.DataFrame(data=None, columns=cfgd._FT3_DATA_META_DATAFRAME_VARIABLES)
        self._type = FT3DataType.meta
        self._maxlen = maxlen
        self._cb = lambda new: None

    def __iadd__(self, new):
        """FasTrak3 metadata overloaded (+=) assignment operator
        """
        self._drop()
        self._data = pd.concat((self._data, new), ignore_index=True)
        self._cb(new)

        return self

    def _drop(self):
        """Drop too-old FasTrak3 metadata
        """
        self._data = cfgd._FT3_DATA_DROP(self)

    @property
    def data(self):
        """Get FasTrak3 metadata
        """
        return self._data
    
    @data.setter
    def data(self, val):
        """Set FasTrak3 metadata
        """
        # TODO ... proposed data assignment validation
        self._data = val

    @property
    def type(self):
        """Get FasTrak3 metadata type
        """
        return self._type
    
    @type.setter
    def type(self, val):
        """Set FasTrak3 metadata type
        """
        # TODO ... proposed data type validation
        self.type = val

    @property
    def cb(self):
        """Get FasTrak3 metadata callback
        """
        return self._cb
    
    @cb.setter
    def cb(self, val):
        """Set FasTrak3 metadata callback
        """
        # TODO ... proposed callback validation
        self._cb = val


@pd.api.extensions.register_series_accessor("ft3shot")
class FT3ShotAccessor(object):
    def __init__(self, pd_obj, maxlen=cfgd._FT3_DATA_MAX_LEN):
        """Initialize FasTrak3 shot data
        """
        self._data = pd.Series(data=None, name='shot_df')
        self._name = self._data.name
        self._type = FT3DataType.shot
        self._maxlen = maxlen
        self._cb = lambda new: None

    def __iadd__(self, new):
        """FasTrak3 shot data overloaded (+=) assignment operator
           to append shot-data dataframe as new element of series
        """
        self._drop()

        # NB: Shot data representation as pandas series with elements
        #     that are per-shot position- and time- sample dataframes
        #     to enable efficient operations to retain / access many
        #     historical shots. (2019-AUG-23)
        wrap_df = pd.Series(data=[new], name=self._name, index=[new.shot[0]])

        self._data = pd.concat((self._data, wrap_df))
        self._cb(new)

        return self

    def _drop(self):
        """Drop too-old FasTrak3 shot data
        """
        self._data = cfgd._FT3_DATA_DROP(self)

    @property
    def data(self):
        """Get FasTrak3 shot data
        """
        return self._data
    
    @data.setter
    def data(self, val):
        """Set FasTrak3 shot data
        """
        # TODO ... proposed data assignment validation
        #          e.g. cfgd._FT3_DATA_SHOT_DATAFRAME_VARIABLES
        self._data = val

    @property
    def type(self):
        """Get FasTrak3 shot data type
        """
        return self._type
    
    @type.setter
    def type(self, val):
        """Set FasTrak3 shot data type
        """
        # TODO ... proposed data type validation
        self.type = val

    @property
    def cb(self):
        """Get FasTrak3 shot data callback
        """
        return self._cb
    
    @cb.setter
    def cb(self, val):
        """Set FasTrak3 shot data callback
        """
        # TODO ... proposed callback validation
        self._cb = val


@pd.api.extensions.register_dataframe_accessor("ft3ref")
class FT3RefAccessor(object):
    def __init__(self, pd_obj, maxlen=cfgd._FT3_DATA_MAX_LEN):
        """Initialize FasTrak3 reference shot data
        """
        self._data = pd.DataFrame(data=None, columns=cfgd._FT3_DATA_REF_DATAFRAME_VARIABLES)
        self._type = FT3DataType.ref
        self._maxlen = maxlen
        self._cb = lambda new: None

    def __iadd__(self, new):
        """FasTrak3 reference shot data overloaded (+=) assignment operator
        """
        self._drop()
        self._data = pd.concat((self._data, new), ignore_index=True)
        self._cb(new)

        return self

    def _drop(self):
        """Drop too-old FasTrak3 reference shot data
        """
        self._data = cfgd._FT3_DATA_DROP(self)

    @property
    def data(self):
        """Get FasTrak3 reference shot data
        """
        return self._data
    
    @data.setter
    def data(self, val):
        """Set FasTrak3 reference shot data
        """
        # TODO ... proposed data assignment validation
        self._data = val

    @property
    def type(self):
        """Get FasTrak3 reference shot data type
        """
        return self._type
    
    @type.setter
    def type(self, val):
        """Set FasTrak3 reference shot data type
        """
        # TODO ... proposed data type validation
        self.type = val

    @property
    def cb(self):
        """Get FasTrak3 reference shot data callback
        """
        return self._cb
    
    @cb.setter
    def cb(self, val):
        """Set FasTrak3 reference shot data callback
        """
        # TODO ... proposed callback validation
        self._cb = val


@pd.api.extensions.register_dataframe_accessor("ft3param")
class FT3ParamAccessor(object):
    def __init__(self, pd_obj, maxlen=cfgd._FT3_DATA_MAX_LEN):
        """Initialize FasTrak3 derived parameters
        """
        self._data = pd.DataFrame(data=None, columns=cfgd._FT3_DATA_PARAM_DATAFRAME_VARIABLES)
        self._type = FT3DataType.param
        self._maxlen = maxlen
        self._cb = lambda new: None

    def __iadd__(self, new):
        """FasTrak3 derived parameters overloaded (+=) assignment operator
        """
        self._drop()
        self._data = pd.concat((self._data, new), ignore_index=True)
        self._cb(new)

        return self

    def _drop(self):
        """Drop too-old FasTrak3 derived parameters
        """
        self._data = cfgd._FT3_DATA_DROP(self)

    @property
    def data(self):
        """Get FasTrak3 derived parameters data
        """
        return self._data
    
    @data.setter
    def data(self, val):
        """Set FasTrak3 derived parameters data
        """
        # TODO ... proposed data assignment validation
        self._data = val

    @property
    def type(self):
        """Get FasTrak3 derived parameters type
        """
        return self._type
    
    @type.setter
    def type(self, val):
        """Set FasTrak3 derived parameters type
        """
        # TODO ... proposed data type validation
        self.type = val

    @property
    def cb(self):
        """Get FasTrak3 derived parameters callback
        """
        return self._cb
    
    @cb.setter
    def cb(self, val):
        """Set FasTrak3 derived parameters callback
        """
        # TODO ... proposed callback validation
        self._cb = val


@pd.api.extensions.register_series_accessor("ft3events")
class FT3EventsAccessor(object):
    def __init__(self, pd_obj, maxlen=cfgd._FT3_DATA_MAX_LEN):
        """Initialize FasTrak3 events
        """
        self._data = pd.Series(data=None, name='events_df')
        self._name = self._data.name
        self._type = FT3DataType.events
        self._maxlen = maxlen
        self._cb = lambda new: None

    def __iadd__(self, new):
        """FasTrak3 events overloaded (+=) assignment operator
        """
        self._drop()

        # NB: Shot events representation as pandas series with elements
        #     that are per-shot events dataframes to enable efficient
        #     operations to retain / access events associated with many
        #     historical shots. (2019-AUG-23)
        wrap_df = pd.Series(data=[new], name=self._name, index=[new.shot[0]])

        self._data = pd.concat((self._data, wrap_df))
        self._cb(new)

        return self

    def _drop(self):
        """Drop too-old FasTrak3 events
        """
        self._data = cfgd._FT3_DATA_DROP(self)

    @property
    def data(self):
        """Get FasTrak3 events data
        """
        return self._data
    
    @data.setter
    def data(self, val):
        """Set FasTrak3 events data
        """
        # TODO ... proposed data assignment validation
        #          e.g. cfgd._FT3_DATA_EVENTS_DATAFRAME_VARIABLES
        self._data = val

    @property
    def type(self):
        """Get FasTrak3 events type
        """
        return self._type
    
    @type.setter
    def type(self, val):
        """Set FasTrak3 events type
        """
        # TODO ... proposed data type validation
        self.type = val

    @property
    def cb(self):
        """Get FasTrak3 events callback
        """
        return self._cb
    
    @cb.setter
    def cb(self, val):
        """Set FasTrak3 events callback
        """
        # TODO ... proposed callback validation
        self._cb = val


@pd.api.extensions.register_series_accessor("ft3ad")
class FT3AdAccessor(object):
    def __init__(self, pd_obj, maxlen=cfgd._FT3_DATA_AD_MAX_LEN):
        """Initialize FasTrak3 shot A/D measurements
        """
        self._data = pd.Series(data=None, name='ad_df')
        self._name = self._data.name
        self._type = FT3DataType.ad
        self._maxlen = maxlen
        self._cb = lambda new: None

    def __iadd__(self, new):
        """FasTrak3 shot data overloaded (+=) assignment operator
           to append shot-data dataframe as new element of series
        """
        self._drop()

        # NB: Shot A/Ds representation as pandas series with elements
        #     that are per-shot position- and time- sample dataframes
        #     to enable efficient operations to retain / access many
        #     historical shots. (2019-AUG-23)
        wrap_df = pd.Series(data=[new], name=self._name, index=[new.shot[0]])

        self._data = pd.concat((self._data, wrap_df))
        self._cb(new)

        return self

    def _drop(self):
        """Drop too-old FasTrak3 shot A/D measurements
        """
        self._data = cfgd._FT3_DATA_DROP(self)

    @property
    def data(self):
        """Get FasTrak3 shot A/D measurements
        """
        return self._data
    
    @data.setter
    def data(self, val):
        """Set FasTrak3 shot A/D measurements
        """
        # TODO ... proposed data assignment validation
        #          e.g. cfgd._FT3_DATA_AD_DATAFRAME_VARIABLES
        self._data = val

    @property
    def type(self):
        """Get FasTrak3 shot A/D measurement type
        """
        return self._type
    
    @type.setter
    def type(self, val):
        """Set FasTrak3 shot A/D measurement type
        """
        # TODO ... proposed data type validation
        self.type = val

    @property
    def cb(self):
        """Get FasTrak3 shot A/D measurement callback
        """
        return self._cb
    
    @cb.setter
    def cb(self, val):
        """Set FasTrak3 shot A/D measurement callback
        """
        # TODO ... proposed callback validation
        self._cb = val
