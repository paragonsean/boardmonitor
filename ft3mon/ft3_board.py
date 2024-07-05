from _thread import *
import threading 
from runlist import *
import queue
from ft3_shot_data import *
from shotsave import *
import time
from log_file import *

FT3_RECV_BUFFER_LEN = 1350
FT3_RESPONSE_TYPE_LEN = 256
FT3_ASYNC_TYPE_HEADER_LEN = 12
FT3_ASYNC_TYPE_BIT = 1 << 7
FT3_ECHO_RESPONSE_INIT = '*'

BINARY_HEADER_LEN = 12
FTII_OSCILLOSCIPE_DATA_LEN = 16000
FTII_OP_STATUS_DATA_LEN = 100

START_OF_BINARY_POS_SAMPLES       = 0
START_OF_BINARY_TIME_SAMPLES      = 1
START_OF_BINARY_PARAMETERS        = 2
START_OF_BINARY_OSCILLOSCOPE_DATA = 3
START_OF_BINARY_OP_STATUS_DATA    = 4
START_OF_BINARY_TEXT_DATA         = 5
START_OF_IO_CHANGE_DATA           = 6  # Version 5 
START_OF_SINGLE_ANALOG_DATA       = 7  # Version 5
START_OF_BLOCK_ANALOG_DATA        = 8  # Version 5 
CONNECTION_LOST                   = 100

NO_INDEX          = -1
ASCII_TYPE        =  0
SAMPLE_TYPE       =  1
PARAMETERS_TYPE   =  2
OP_STATUS_TYPE    =  3
OSCILLOSCOPE_TYPE =  4
SOCKET_ERROR_TYPE =  5

CYCLE_START = "Cycle start"
TIMEOUT     = "timeout"

ANALOG_RESPONSE = "O_CH"
ANALOG_RESPONSE_SLEN = 4

TIMER_FREQ_RESPONSE = "V301_"
TIMER_FREQ_SLEN     = 5
TIMER_FREQ_FLEN     = 4

AT_HOME_RESPONSE    = "R_At home"
POS_AT_IMPACT_RESPONSE = "R_POS1EOS"
POS_AT_IMPACT_RESPONSE_SLEN = 9

VERSION_RESPONSE    = "R:6#emc_"
VERSION_RESPONSE2   = "R:6#cyc_"
VERSION_RESPONSE_SLEN = 8

FATAL_OR_WARNING_RESPONSE = "_Cont."
FATAL_OR_WARNING_RESPONSE_SLEN = 6

INPUT_BITS_RESPONSE      = "O_ISW1="
INPUT_BITS_RESPONSE_SLEN = 7;

FIRST_PACKET_NUMBER = 1
CTRL_PROG_NUMBER_LEN = 4   # Used to compare line numbers like .022
VARIABLE_NUMBER_LEN  = 4   # Used to compare strings that begin V447, etc

NO_WIRE = 0
MonitorWire = NO_WIRE

ConfigSetString          = "V313=H"
ControlFileDateString    = "V447"
ControlStatusString      = "V311"
FlashVariablesString     = "VF\r"
GoString                 = ".G\r"
IsControlSetString       = "V500=H"
DigitalPotGainSetString  = "V431=H"
GetAllAnalogInputs       = "OAA\r"
GetControlFileDateString = "V447\r"
GetControlStatusString   = "V311\r"
GetMonitorStatusString   = "V312\r"
GetMSLString             = "V319\r"
GetTimerFrequencyString  = "V301\r"
GetInputBitsString       = "OI1\r"
GetUploadCopyDateString  = "V448\r"
GetVersionString         = "OV\r"
MonitorStatusString      = "V312"
ConfigWord2SetString     = "V314=H"
TimeoutString            = "Timeout"
UploadCopyDateString     = "V448"

# upload states
NO_UPLOAD_STATE      = 0
WAITING_FOR_INFO     = 1 
UPLOAD_ALL           = 2 
UPLOAD_ALL_VARIABLES = 3
UPLOAD_NEW_VARIABLES = 4
SEND_THREAD_START_FAILURE = 5
SEND_THREAD_WAIT_FAILURE  = 6
NO_FILE_DATE = 0x80000000

# continue_connecting_one_board
POS_AT_IMPACT_DISABLE    = "OC13=0\r"
POS_AT_IMPACT_ENABLE     = "OC13=1\r"
set_input_bitmask_string = "V427=H"

UploadRetractTimeout    = 0
UploadStartShotTimeout  = 0

NoUploadWire       = NO_WIRE
NoUploadWireMask   = 0
RetractWire        = NO_WIRE
RetractWireMask    = 0x080000

# connection states
NO_FT2_CONNECT_STATE = 0
NOT_CONNECTED_STATE  = 1
NOT_MONITORED_STATE  = 2
CONNECTING_STATE     = 4
CONNECTED_STATE      = 8
ZERO_STROKE_LENGTH_STATE = 16
UPLOAD_WAS_ABORTED_STATE = 32

DONT_SEND_OP_DATA_PACKETS   = "OC3=0"
SEND_OP_DATA_PACKETS        = "OC3=2"
CLEAR_CONTROL_FILE_DATE_CMD = "V447=0"

ALS_BITS = 0x600E0000

class PartNameEntry:
    def __init__(self):
        self.computer = str()
        self.machine = str()
        self.part = str()
        
    def set(self, cn, mn, pn):
        self.computer = cn
        self.machine = mn
        self.part = pn

class ExtendedAnalogEntry:    
    def __init__(self):
        self.parameter_number = NO_PARAMETER_NUMBER
        self.value = 0
    
class BoardExtendedAnalogEntry:
    def __init__(self):
        self.mask = 0
        self.channel = NO_FT_CHANNEL
        self.trigger_type = TRIGGER_WHEN_GREATER
        self.waiting_for_value = FALSE
        ae = ExtendedAnalogEntry()        

class Sockaddr:
    def __init__(self):
        sin_family = int()
        sin_port = int()
        addr = str()
        sin_zero = str()

class Machine:
    def __init__(self):
        self.computer = str()
        self.current_part = str()
        self.name = str()
        self.suretrak_controlled = bool()
        self.monitoring_was_stopped = bool()
    
class Ft3Board:    
    def __init__(self): 
        self.binarybuf = bytes()
        self.connect_state = 0
        self.control_file_date = 0
        self.current_packet_number = int()
        self.current_type = int()
        self.do_not_upload = False
        self.extended_analog = []
        self.f = queue.Queue()
        self.ft3_send_event = threading.Event()
        self.have_response = False
        self.have_runlist = False
        self.input_bits = 0
        self.is_sending_op_data_packets = False
        self.machine = Machine() 
        self.runlist = RunList()
        self.s = str()
        self.shotdata = FTII_NET_DATA()
        self.shot_number = int()
        self.shot_start_time = str()
        self.shot_stop_time = str()
        self.sockaddr = Sockaddr()
        self.start_op_data_after_upload = False
        self.sub_version = 0 
        self.time_of_last_shot = 0
        self.upload_file_date = 0
        self.upload_state = NO_UPLOAD_STATE
        self.version_string = '0.00'
        self.version = 0
    
    def add_binary_to_shotdata(self):
        if self.current_type == SAMPLE_TYPE:
            #The length is in bytes but I need number of samples
            nof_samples = self.current_len / FTII_SAMPLE_LEN
            if self.sample_type == 'P':
                self.time_of_last_shot = time.time()
                self.shotdata.set_shot_time(self.time_of_last_shot)
                self.shotdata.set_position_based_points(self.binarybuf, nof_samples)
            else:
                self.shotdata.set_time_based_points(self.binarybuf, nof_samples)
                self.binarybuf = 0

        elif self.current_type == PARAMETERS_TYPE:
            self.shotdata.set_parameters(self.binarybuf)
            self.binarybuf = 0
            self.save_shot()
    
    def check_for_extended_channel_value(self, sorc):
        print('check_for_extended_channel_value')
    
    def put_version_string(self):
        print('Board Version: ', self.version_string)
        
    def check_inputs(self, sorc):
        getanalog = "OA"
        u = int(sorc, 16) # convert hex string to int
        s = str()

        if (s != '') and (s != part.name):
            if part_exists( part.computer, part.machine, s):
                set_current_part_name( part.computer, part.machine, s )
                s = part.machine
                if not s.isempty():
                    #MainWindow.post( WM_POKEMON, (WPARAM) MONITOR_SETUP_INDEX, (LPARAM) s.release() )
                    print('MainWindow.post( WM_POKEMON, (WPARAM) MONITOR_SETUP_INDEX, (LPARAM) s.release() )')
                else:
                    print('MessageBox( 0, not_found_string.text(), s.text(), MB_OK | MB_SYSTEMMODAL )')
                    #MessageBox( 0, not_found_string.text(), s.text(), MB_OK | MB_SYSTEMMODAL )

        #If the NoUploadMask is set then I am using an input instead of the cycle start message
        #The bit must be clear in the saved input_bits before I disable uploads.    
        if self.machine.suretrak_controlled and NoUploadWireMask and not self.do_not_upload:
            if (u & NoUploadWireMask) and not (u & self.input_bits):
                self.do_not_upload_timeout = 0
                self.do_not_upload         = True
                if self.UploadStartShotTimeout:
                    self.do_not_upload_timeout = GetTickCount()
                    additional_ms = UploadStartShotTimeout
                    additional_ms *= 1000
                    self.do_not_upload_timeout += additional_ms
                    
                set_text( Dnu[index], '*' )

        if self.do_not_upload and UploadRetractTimeout:
            if u & RetractWireMask:          
                #Wait 2 more seconds for the rod to retract
                #before beginning an upload.            
                self.do_not_upload_timeout = GetTickCount()
                self.do_not_upload_timeout += UploadRetractTimeout*1000        

        #See if any of the extended analog inputs have changed. If so, send a
        #OAy command to get the analog value for that channel..    
        for i in range(0, len(self.extended_analog)):        
            need_message = False
            if self.extended_analog[i].waiting_for_value == False:
                mask = self.extended_analog[i].mask
                if self.extended_analog[i].trigger_type == TRIGGER_WHEN_GREATER:
                    if (mask & u) == True and (mask & input_bits ) == False:
                        need_message = True
                else:          
                    if (mask & u) == False and (mask & input_bits ) == True:
                        need_message = True

            if need_message:
                self.extended_analog[i].waiting_for_value = True
                getanalog += str(self.extended_analog[i].channel) + '\r'
                self.send_socket_message( getanalog, True )

        self.input_bits = u
     
    def save_shot(self):
        filedata = FTII_FILE_DATA()
        
        # If either the position data or time data are missing I must have lost some packets and
        # can't save the file.
        if ffi.sizeof(self.shotdata.position_sample) == 0 or ffi.sizeof(self.shotdata.time_sample) == 0:
            return
        
        pn = PartNameEntry()
        pn.set(self.machine.computer, self.machine.name, self.machine.current_part)  
        filedata.from_FTII_NET_DATA(self.shotdata)        
        add_to_shotsave(False, False, pn, filedata, 0)
        global ShotSaveEvent
        ShotSaveEvent.set()
        debug_log = LogFile('debug.log')
        debug_log.add_entry('ft3_board.py(355): ShotSaveEvent.set()')
        #self.shotdata.clear()            

    def send_socket_message(self, sorc, need_to_set_event):
        mp = SocketMessage()
        mp.addr.sin_family = AF_INET
        mp.sin_port = self.sockaddr.sin_port
        mp.addr.addr = self.sockaddr.addr
        
        if len(sorc) > 0:
            # Keep track of whether I'm sending the op data packets or not. If I'm uploading
            #skip it because I will turn the packets back on when the upload is done.
            if sorc.find(OpDataPacketString) == 0:
                if sorc[4] == '0':
                    self.is_sending_op_data_packets = False
                elif sorc[4] == '2':
                    self.is_sending_op_data_packets = True

            #copy the message to the buffer
            mp.s = sorc
        else:
            mp.s = ''
            
        self.f.put(mp)
        
        if need_to_set_event == True:
            self.ft3_send_event.set()
            
    def set_connect_state(self, new_state):
        b = 0
        if self.connect_state != new_state:
            old_state = self.connect_state
            b = self.connect_state & UPLOAD_WAS_ABORTED_STATE
            self.connect_state = new_state
            if new_state & CONNECTING_STATE or new_state & NOT_CONNECTED_STATE:
                self.connect_state |= b
            #i = board_index()             
            #If the last upload was aborted, tell the main proc so he can ask a human to reupload   
            if new_state & CONNECTED_STATE:
                new_state |= b
                if not (old_state & CONNECTED_STATE):
                    #If the board is reconnecting after an absense I need to restart the op data
                    #packets. If start_op_data_after_upload then I am resetting and don't need
                    #to do this.                    
                    if self.is_sending_op_data_packets and not self.start_op_data_after_upload:
                        self.send_socket_message( SEND_OP_DATA_PACKETS, true )                   
            #MainWindow.post( WM_NEW_FT2_STATE, (WPARAM) i, (LPARAM) new_state )
   
            
            
            
            
            
            
    
    