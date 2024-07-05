from cffi import FFI
from struct import *
import pandas as pd
from pandas import DataFrame
from log_file import *
import time

ffi = FFI()
ffi.cdef("""    
    typedef struct {
    unsigned short analog[8];
    unsigned       velcount[4];
    unsigned       isw1;
    unsigned       isw4;
    unsigned       osw1;
    unsigned       one_ms_timer;
    int            position;
    int            sample_num;
    } FTII_SAMPLE;
    
    typedef struct {
    unsigned       cycle_time;
    unsigned short biscuit_size;
    short          eos_pos;
    unsigned short static_analog[8];
    } FTII_PARAMETERS;
    
    typedef struct {
    unsigned       cycle_time;
    unsigned short biscuit_size;
    short          eos_pos;
    } VERSION_1_FTII_PARAMETERS;
    
    typedef struct {
    int curve_type;
    union { int imin; unsigned int umin; };
    union { int imax; unsigned int umax; };
    } FTII_MIN_MAX_DATA;
        """)

ASCII_TYPE        =  0
SAMPLE_TYPE       =  1
PARAMETERS_TYPE   =  2
OP_STATUS_TYPE    =  3
OSCILLOSCOPE_TYPE =  4
SOCKET_ERROR_TYPE =  5

NOF_STATIC_ANALOGS       = 8
NOF_FTII_FILE_PARAMETERS = 11
NOF_FTII_FILE_CURVES     = 10  # This is the number of curves that have max and min data in curvedata

FIRST_ANALOG_CURVE_INDEX = 2  # FTII_FILE_DATA

FTII_SAMPLE_LEN = 56
FTII_PARAMETERS_LEN = 24

CHANNEL_MODE_1  =  1
CHANNEL_MODE_2  =  2
CHANNEL_MODE_3  =  3
CHANNEL_MODE_4  =  4
CHANNEL_MODE_5  =  5

NOF_FILE_COUNTS =  7
NOF_CURVES      = NOF_FTII_FILE_CURVES

MAX_12_BIT_VALUE = 4095
CHANNEL_MASK     = 0xF000
VALUE_MASK       = 0x0FFF
TIMER_MASK       = 0x3FFFFFFF
ERROR_MASK       = 0x40000000
DIRECTION_MASK   = 0x80000000

# curve types
FTII_NO_CURVE_TYPE        = 0
FTII_POSITION_TYPE        = 1
FTII_TIME_TYPE            = 2
FTII_TIMER_COUNT_TYPE     = 3
FTII_VELOCITY_TYPE        = 4
FTII_ISW1_TYPE            = 5
FTII_ISW2_TYPE            = 6
FTII_ISW3_TYPE            = 7
FTII_ISW4_TYPE            = 8
FTII_OSW1_TYPE            = 9
FTII_OSW2_TYPE            = 10
FTII_OSW3_TYPE            = 11
FTII_ANALOG1_TYPE         = 12  # Keep these sequential
FTII_ANALOG2_TYPE         = 13
FTII_ANALOG3_TYPE         = 14
FTII_ANALOG4_TYPE         = 15
FTII_ANALOG5_TYPE         = 16
FTII_ANALOG6_TYPE         = 17
FTII_ANALOG7_TYPE         = 18
FTII_ANALOG8_TYPE         = 19
FTII_ANALOG9_TYPE         = 20
FTII_ANALOG10_TYPE        = 21
FTII_ANALOG11_TYPE        = 22
FTII_ANALOG12_TYPE        = 23
FTII_ANALOG13_TYPE        = 24
FTII_ANALOG14_TYPE        = 25
FTII_ANALOG15_TYPE        = 26
FTII_ANALOG16_TYPE        = 27
FTII_ANALOG17_TYPE        = 28
FTII_ANALOG18_TYPE        = 29
FTII_ANALOG19_TYPE        = 30
FTII_ANALOG20_TYPE        = 31

NOF_FTII_FILE_CURVES = 10

# from VISIPARM.H
X4_COUNTS_PER_MARK = 4
NOF_FTII_ANALOGS = 8     # Number of continuous analog channels on ftii board
NO_PARAMETER_NUMBER = 0

CurrentShot = 0

class FTII_MIN_MAX_DATA:
    def __init__(self):
        self.curve_type = FTII_NO_CURVE_TYPE
        self.imin = 0
        self.imax = 0
        self.umin = 0
        self.umax = 0

class EXTENDED_ANALOG_ENTRY:
    def __init__(self):
        self.parameter_number = NO_PARAMETER_NUMBER
        self.value = str()
        
    #def read:
        #read from DB
    #def write:
        #write to DB

class TEXT_PARAMETER_ENTRY:
    def __init__(self):
        self.parameter_number = NO_PARAMETER_NUMBER
        self.value = str()

class FTII_FILE_DATA:
    def __init__(self):
        self.channel_mode            = CHANNEL_MODE_1
        self.timer_frequency         = 16666666
        self.np                      = 0
        self.nt                      = 0
        self.cs_to_point_1_ms        = 0
        self.us_per_time_sample      = 1000
        self.internal_shot_number    = 0
        self.position_df             = pd.DataFrame()
        self.time_df                 = pd.DataFrame()
        
        self.parameter = []
        for i in range(0,11):
            self.parameter.append(0)
        
        self.nof_extended_analogs    = 0
        self.extended_analog         = 0
        self.nof_text_parameters     = 0
        self.text_parameter          = 0
        
        self.curvedata = ffi.new('FTII_MIN_MAX_DATA[]', NOF_FTII_FILE_CURVES)
        self.curvedata_buf = ffi.buffer(self.curvedata)

    def clear(self):
        self.position_df = pd.DataFrame()
        self.time_df = pd.DataFrame()
        self.nof_extended_analogs = 0
        self.extended_analog = 0
        self.text_parameter = 0
        
    def from_FTII_NET_DATA(self, sorc):
        #debug
        debug_log = LogFile('debug.log')
        debug_log.add_entry('from_FTII_NET_DATA enter')
        debug_log.add_entry('np = ' + str(sorc.np) + ', nt = ' + str(sorc.nt))
        
        self.clear()
        self.timer_frequency = sorc.timer_frequency
        self.np = sorc.np
        self.nt = sorc.nt
        self.cs_to_point_1_ms = sorc.position_sample[1].one_ms_timer
        self.us_per_time_sample = sorc.us_per_time_sample
        self.internal_shot_number = sorc.internal_shot_number
        self.shot_time = sorc.shot_time
        
        if self.np > 0:
            debug_log.add_entry('from_FTII_NET_DATA sorc.position_sample len=' + str(len(sorc.position_sample)))
            
            for i in range(0, self.np):
                try:
                    self.position_df = self.position_df.append(pd.DataFrame({'shot':[CurrentShot],
                                        'type':['P'],
                                        'ana_ch1':[sorc.position_sample[i].analog[0]],
                                        'ana_ch2':[sorc.position_sample[i].analog[1]],
                                        'ana_ch3':[sorc.position_sample[i].analog[2]],
                                        'ana_ch4':[sorc.position_sample[i].analog[3]],
                                        'ana_ch5':[sorc.position_sample[i].analog[4]],
                                        'ana_ch6':[sorc.position_sample[i].analog[5]],
                                        'ana_ch7':[sorc.position_sample[i].analog[6]],
                                        'ana_ch8':[sorc.position_sample[i].analog[7]],
                                        'vel_count_q1':[sorc.position_sample[i].velcount[0]],
                                        'vel_count_q2':[sorc.position_sample[i].velcount[1]],
                                        'vel_count_q3':[sorc.position_sample[i].velcount[2]],
                                        'vel_count_q4':[sorc.position_sample[i].velcount[3]],
                                        'isw1':[sorc.position_sample[i].isw1],
                                        'isw4':[sorc.position_sample[i].isw4],
                                        'osw1':[sorc.position_sample[i].osw1],
                                        'one_ms_timer':[sorc.position_sample[i].one_ms_timer],
                                        'position':[sorc.position_sample[i].position],
                                        'sample_num':[sorc.position_sample[i].sample_num]} ))
                except Exception as e:
                    debug_log.add_entry(str(e))
            
            debug_log.add_entry('position_df len=' + str(len(self.position_df)))
        
        self.curvedata[0].curve_type = FTII_POSITION_TYPE
        self.curvedata[0].imin = 0
        self.curvedata[0].imax = self.np - 1
        
        if self.nt > 0:
            debug_log.add_entry('from_FTII_NET_DATA sorc.time_sample len=' + str(len(sorc.time_sample)))
            
            for i in range(0, self.nt):
                try:
                    self.time_df = self.time_df.append(pd.DataFrame({'shot':[CurrentShot],
                                        'type':['T'],
                                        'ana_ch1':[sorc.time_sample[i].analog[0]],
                                        'ana_ch2':[sorc.time_sample[i].analog[1]],
                                        'ana_ch3':[sorc.time_sample[i].analog[2]],
                                        'ana_ch4':[sorc.time_sample[i].analog[3]],
                                        'ana_ch5':[sorc.time_sample[i].analog[4]],
                                        'ana_ch6':[sorc.time_sample[i].analog[5]],
                                        'ana_ch7':[sorc.time_sample[i].analog[6]],
                                        'ana_ch8':[sorc.time_sample[i].analog[7]],
                                        'isw1':[sorc.time_sample[i].isw1],
                                        'isw4':[sorc.time_sample[i].isw4],
                                        'osw1':[sorc.time_sample[i].osw1],
                                        'one_ms_timer':[sorc.time_sample[i].one_ms_timer],
                                        'position':[sorc.time_sample[i].position],
                                        'sample_num':[sorc.time_sample[i].sample_num]} ))
                except Exception as e:
                    debug_log.add_entry(str(e))
            
            debug_log.add_entry('time_df len=' + str(len(self.time_df)))
        
        self.parameter[0] = int(sorc.parameter.cycle_time)
        self.parameter[1] = int(sorc.parameter.biscuit_size)
        self.parameter[2] = int(sorc.parameter.eos_pos)

        ai = 0
        for i in range(3, NOF_FTII_FILE_PARAMETERS):
            u = sorc.parameter.static_analog[ai]
            self.parameter[i] = int(u)
            ai += 1

        self.nof_text_parameters = 0
        if self.text_parameter != 0:
            self.text_parameter = 0
            
    # change this to insert into db
    def put(self, db_conn):
        debug_log = LogFile('debug.log')
        global CurrentShot 
        debug_log.add_entry('ft3_shot_data.py(340): CurrentShot = ' + str(CurrentShot))      
        # write shot data to database        
        t0 = time.time() 
        self.position_df.to_sql('ft3shot', db_conn, if_exists='append', index=False)
        self.time_df.to_sql('ft3shot', db_conn, if_exists='append', index=False)        
        t1 = time.time()
        np = len(self.position_df)
        nt = len(self.time_df)
        debug_log.add_entry('ft3_shot_data.py(356): write shot data complete, nof position samples=' + str(np) + ', nof time samples=' + str(nt) + ', dt=' + str(t1-t0))
        CurrentShot += 1

class FTII_NET_DATA:
    def __init__(self):
        self.timer_frequency = 16666666
        self.np = 0
        self.nt = 0
        self.us_per_time_sample = 1000
        self.internal_shot_number = 0
        self.shot_time = int()                                  # C++ FILETIME
        self.position_sample = ffi.new('FTII_SAMPLE[]', 0)      # FTII_SAMPLE[]
        self.position_sample_buf = 0
        self.time_sample = ffi.new('FTII_SAMPLE[]', 0)          # FTII_SAMPLE[]
        self.time_sample_buf = 0
        self.parameter = ffi.new('FTII_PARAMETERS[]', 0)
        self.parameter_buf = 0

    def clear(self):
        self.np = 0
        self.nt = 0
        self.position_sample = ffi.new('FTII_SAMPLE[]', 0)
        self.time_sample = ffi.new('FTII_SAMPLE[]', 0)
        debug_log = LogFile('debug.log')
        debug_log.add_entry('FTII_NET_DATA.clear() was called')

    def set_shot_time(self, t):
        self.shot_time = t
        
    def set_time_based_points(self, time_based_points, nof_samples):
        nof_samples = int(nof_samples)
        if nof_samples > 0:
            self.time_sample = ffi.new('FTII_SAMPLE[]', nof_samples)
            self.time_sample_buf = ffi.buffer(self.time_sample)
            self.time_sample_buf[:] = time_based_points
            self.nt = nof_samples

    def set_position_based_points(self, position_based_points, nof_samples):
        nof_samples = int(nof_samples)
        if nof_samples > 0:
            self.position_sample = ffi.new('FTII_SAMPLE[]', nof_samples)
            self.position_sample_buf = ffi.buffer(self.position_sample)
            self.position_sample_buf[:] = position_based_points
            self.np = nof_samples

    def set_parameters(self, parameters):
        n = len(parameters)
        if n <= 0:
            return
        if n > int(ffi.sizeof('VERSION_1_FTII_PARAMETERS')):
            self.parameter = ffi.new('FTII_PARAMETERS*')
        else:
            self.parameter = ffi.new('VERSION_1_FTII_PARAMETERS*')

        self.parameter_buf = ffi.buffer(self.parameter)
        self.parameter_buf[:] = parameters

    def set_timer_frequency(self, new_timer_frequency):
        self.timer_frequency = new_timer_frequency

    def set_us_per_time_sample(self, new_us):
        self.us_per_time_sample = new_us

    # The following methods are not used ???
    #void set_time_based_points( NEW_FTII_DATA & nd ) 
    #void set_position_based_points( NEW_FTII_DATA & nd );
    #void set_parameters( NEW_FTII_DATA & nd ); 
    #BOOLEAN write_csv( STRING_CLASS & dest_file_path );
