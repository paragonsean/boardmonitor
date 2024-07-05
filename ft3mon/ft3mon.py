import socket 
from _thread import *
import threading 
import queue
import struct
from cffi import FFI
from ft3_board import *
from shotsave import *
import pandas as pd
import ft3_shot_data
import ft3sim
import time

ffi = FFI()
ffi.cdef("""
    typedef struct {
    char           bchar;
    unsigned char  data_type;
    unsigned short flags;
    unsigned short data_set_num;
    unsigned short packet_num;
    unsigned short nof_packets;
    unsigned short nof_bytes;
    } BINARY_HEADER;
    
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
    short ch_17_20[2000][4];
    } FTII_OSCILLOSCOPE_DATA;
    
    typedef struct {
    int            dac[4];
    unsigned short analog[20];
    int            pos;
    int            vel;
    unsigned       isw1;
    unsigned       isw4;
    unsigned       osw1;
    unsigned       monitor_status;
    unsigned       status_word1;
    unsigned       config_word1;
    int            warning;
    int            fatal_error;
    int            blk_no;
    } FTII_OP_STATUS_DATA;
        """)    

FT3_ECHO_RESPONSE_VERBOSE = False
SET_INPUT_BITMASK_STRING = "V427=H"
ReadThreadRunning = False
ReadSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
NewDataThreadRunning = False
NewData = queue.Queue()
Boards = []
NumBoards = 1
CurrentBoardIndex = 0

def continue_connecting_one_board(i):
    if Boards[i].upload_state != WAITING_FOR_INFO:
        return
        
    if Boards[i].version == 0:
        return
        
    if Boards[i].control_file_date == 0:
        return
        
    if Boards[i].upload_copy_date == 0:
        return

    #tell the Boards[index] which bits are being monitored
    u = 0
    if Boards[i].have_runlist:
        u = Boards[i].runlist.mask
    #elif Boards[i].machine.multipart_runlist_settings.enable:
    #    u = Boards[i].machine.multipart_runlist_settings.mask

    if Boards[i].machine.suretrak_controlled:
        u |= RetractWireMask
    u |= NoUploadWireMask

    for j in range(0,len(Boards[i].extended_analog)):
        u |= Boards[i].extended_analog[j].mask

    #add bits for Al's log file
    if AlsLogIsActive:
        u |= ALS_BITS

    s = SET_INPUT_BITMASK_STRING
    s += hex(u)
    s += '\r'
    Boards[i].send_socket_message(s, True)
    Boards[i].send_socket_message(GetInputBitsString, True)
    
    if Boards[i].needs_impact_position_report:
        Boards[i].send_socket_message(POS_AT_IMPACT_ENABLE, True)
    else:
        Boards[i].send_socket_message(POS_AT_IMPACT_DISABLE, False)
        
    if Boards[i].monitoring_was_stopped == False:
        if Boards[i].upload_control_file() == False:
            update_monitor_status(Boards[i], NO_UPLOAD_FILE_STRING)
            
    Boards[i].monitoring_was_stopped = False
    
    Boards[i].clear_all_alarm_bits()
    if MonitorWire != NO_WIRE and Boards[i].down_timeout_seconds > 0:
        ds = Boards[i].down_state
        if ClearMonitorWireOnDown == False or ds == PROG_UP_STATE or ds == MACH_UP_STATE or ds == NO_DOWN_STATE:
            Boards[i].setwire(MonitorWire)
    
def check_for_cycle_start(index, sorc):
    global Boards
    cp = sorc.find(CYCLE_START)
    if cp >= 0:
        #Cycle Start
        cp = sorc.find(TIMEOUT)
        if cp >= 0:
            #Timeout
            print('FT3 Timeout')
        else:
            print('Cycle Start')
            Boards[index].shot_start_time = datetime.today().isoformat()
        
        return True
    else:
        return False
   

def send_to_terminal(sorc):
    #print('send_to_terminal: ',sorc)
    print('send_to_terminal')

def do_ascii_message(index, sorc):
    global Boards
    
    matched_message = check_for_cycle_start(index, sorc)
    
    print('do_ascii_message: ', sorc)
    
    #write events to database
    ft3events = pd.DataFrame({'shot':[ft3_shot_data.CurrentShot],
                              't':[datetime.today().isoformat()],
                              'event':[sorc]})
    ft3events.to_sql('ft3events', DBEng, if_exists='append', index=False) 
    global EventDataReadyEvent
    EventDataReadyEvent.set()
    
    #timer frequency message
    if matched_message == False:
        cp = sorc.find(TIMER_FREQ_RESPONSE)
        if cp >= 0:
            Boards[index].time_frequency = int(sorc[cp+TIMER_FREQ_SLEN:cp+TIMER_FREQ_SLEN+TIMER_FREQ_FLEN])
            matched_message = True
            print('TIMER_FREQ_RESPONSE')
    
    #input bits response
    if matched_message == False:
        cp = sorc.find(INPUT_BITS_RESPONSE)
        if cp >= 0:
            print('INPUT_BITS_RESPONSE')
            Boards[index].check_inputs(sorc[cp+INPUT_BITS_RESPONSE_SLEN:])
            matched_message = True            
    
    #at home response
    if matched_message == False:
        cp = sorc.find(AT_HOME_RESPONSE)
        if cp >= 0:
            matched_message = True
            print('AT_HOME_RESPONSE')
            if Boards[index].do_not_upload:
                Boards[index].do_not_upoad = False
                Boards[index].do_not_upload_timeout = 0
                #set_text( Dnu[Boards[index]->index], EmptyString );
            #save stop time at at home signal
            Boards[index].shot_stop_time = datetime.today().isoformat()
            #write meta to database
            ft3meta = pd.DataFrame({'shot':[ft3_shot_data.CurrentShot],
                                    't0':[Boards[index].shot_start_time],
                                    't1':[Boards[index].shot_stop_time],
                                    'num_pos_samples':[Boards[index].shotdata.np],
                                    'num_time_samples':[Boards[index].shotdata.nt]})
            ft3meta.to_sql('ft3meta', DBEng, if_exists='append', index=False) 
            Boards[index].shotdata.clear()
            global MetaDataReadyEvent
            MetaDataReadyEvent.set()
    
    #position at impact response
    if matched_message == False:
        cp = sorc.find(POS_AT_IMPACT_RESPONSE)
        if cp >= 0:
            matched_message = True
            cp = sorc[cp:].find('#')
            if cp >= 0:
                position = float(sorc[cp+1:])
                position = Boards[index].dist_from_x4(position)
                #Gibbs wants biscuit size
                position = Boards[index].part.total_stroke_length - position
                #write position param to DB
                print('POS_AT_IMPACT_RESPONSE')
    
    #version response
    if matched_message == False:
        cp = sorc.find(VERSION_RESPONSE)
        if cp < 0:
            cp = sorc.find(VERSION_RESPONSE2)
        if cp >= 0:
            commap = sorc.find(',')
            if commap:
                if Boards[index].version_string != sorc[cp+VERSION_RESPONSE_SLEN:commap]:
                    Boards[index].version_string = sorc[cp+VERSION_RESPONSE_SLEN:commap]
                    Boards[index].put_version_string()
            Boards[index].version = int(sorc[cp+VERSION_RESPONSE_SLEN:cp+VERSION_RESPONSE_SLEN+1])
            Boards[index].sub_version = int(sorc[cp+2+VERSION_RESPONSE_SLEN:cp+4+VERSION_RESPONSE_SLEN])
            matched_message = True
            #wait for the version, V447 and V448 messages before uploading
            if Boards[index].upload_state == WAITING_FOR_INFO:
                continue_connecting_one_board(bindex)
            print('VERSION_RESPONSE')

    #control file upload date
    if matched_message == False:
        if sorc[:VARIABLE_NUMBER_LEN] == ControlFileDateString:
            if sorc[VARIABLE_NUMBER_LEN] == '-':
                Boards[index].control_file_date = NO_FILE_DATE
            else:
                Boards[index].control_file_date = int(sorc[VARIABLE_NUMBER_LEN:])
                if Boards[index].control_file_date == 0:
                    Boards[index].control_file_date = NO_FILE_DATE
            continue_connecting_one_board(bindex)
            matched_message = True
            print('ControlFileDateString')
    
    #upload copy date
    if matched_message == False:
        if sorc[:VARIABLE_NUMBER_LEN] == UploadCopyDateString:
            if sorc[VARIABLE_NUMBER_LEN] == '-':
                Boards[index].upload_copy_date = NO_FILE_DATE
            else:
                Boards[index].upload_copy_date = int(sorc[VARIABLE_NUMBER_LEN:])
                if Boards[index].upload_copy_date == 0:
                    Boards[index].upload_copy_date = NO_FILE_DATE
                continue_connecting_one_board(bindex)
            matched_message = True
            print('UploadCopyDateString')
            
    #analog response        
    if matched_message == False:
        if sorc[:ANALOG_RESPONSE_SLEN] == ANALOG_RESPONSE:
            Boards[index].check_for_extended_channel_value(sorc)
            matched_message = True
            print('ANALOG_RESPONSE')
            
    #fatal or warning response
    if matched_message == False:
        if sorc[1:FATAL_OR_WARNING_RESPONSE_SLEN] == FATAL_OR_WARNING_RESPONSE:
            update_monitor_status(Boards[index], sorc[FATAL_OR_WARNING_RESPONSE_SLEN+2:])
            #if first char is F this is a fatal erro so allow updates
            if sorc[0] == 'F' or sorc[0] == 'f':
                Boards[index].do_not_upload = False
                Boards[index].do_not_upload_timeout = 0
                #set_text(Dnu[bindex], EmptyString);
                if Boards[index].part.st2_program_abort_wire != NO_WIRE:
                    Boards[index].setwire(Boards[index].part.st2_program_abort_wire)
            print('FATAL_OR_WARNING_RESPONSE')
    
    #if this is the Boards[index] that has the current machine then send all ascii data to terminal 
    if index == CurrentBoardIndex:
        send_to_terminal(sorc)
    
def convert_io_change_to_ascii(i, msg):
    response = INPUT_BITS_RESPONSE    
    hex = msg.data[0:4].hex()
    response += hex
    #print('convert_io_change_to_ascii: ', response)
    do_ascii_message(i, response)     
  
def board_index(term):
    #search by object
    if type(term).__name__ == 'Ft3Board':
        for i in range(NumBoards):
            if Boards[i].addr == term.sockaddr.addr:
                return i
    
    #search by machine name
    elif type(term).__name__ == 'str':
        for i in range(NumBoards):
            if Boards[i].machine.name == term:
                return i
                
    #search by address
    elif type(term).__name__ == 'Sockaddr':
        for i in range(NumBoards):
            if Boards[i].sockaddr.addr == term.addr:
                return i
    
    return -1

def start_of_binary_data( i, bh ):
    Boards[i].binarybuf = bytes()
    Boards[i].current_len = 0
    Boards[i].chars_left_in_buffer = 0
    
    if bh.data_type == START_OF_BINARY_POS_SAMPLES or bh.data_type == START_OF_BINARY_TIME_SAMPLES:
        Boards[i].chars_left_in_buffer = bh.nof_bytes * bh.nof_packets
        Boards[i].current_type = SAMPLE_TYPE
        Boards[i].sample_type  = 'P'
        
        if bh.data_type == START_OF_BINARY_TIME_SAMPLES:
            Boards[i].sample_type = 'T'

    elif bh.data_type == START_OF_BINARY_PARAMETERS:
        Boards[i].chars_left_in_buffer = bh.nof_bytes * bh.nof_packets
        Boards[i].current_type = PARAMETERS_TYPE          

    elif bh.data_type == START_OF_BINARY_OP_STATUS_DATA:
        Boards[i].current_type = OP_STATUS_TYPE
        #Boards[i].chars_left_in_buffer = sizeof(FTII_OP_STATUS_DATA)
        op_status_def = ffi.new("FTII_OP_STATUS_DATA*")
        op_status_buf = ffi.buffer(op_status_def)
        Boards[i].chars_left_in_buffer = len(op_status_buf)
        print('START_OF_BINARY_OP_STATUS_DATA len(FTII_OP_STATUS_DATA) = ', len(op_status_buf))

    elif bh.data_type == START_OF_BINARY_OSCILLOSCOPE_DATA:
        Boards[i].current_type = OSCILLOSCOPE_TYPE
        #Boards[i].chars_left_in_buffer = sizeof(FTII_OSCILLOSCOPE_DATA)
        oscope_def = ffi.new("FTII_SAMPLE*")
        oscope_buf = ffi.buffer(oscope_def)
        Boards[i].chars_left_in_buffer = FTII_OSCILLOSCIPE_DATA_LEN
        print('START_OF_BINARY_OP_STATUS_DATA len(FTII_SAMPLE) = ', len(oscope_buf))
            
    if Boards[i].chars_left_in_buffer > 0:
        Boards[i].binarybuf             = bytes()
        Boards[i].bp                    = 0  # pointer to position in binarybuf
        Boards[i].current_packet_number = 0

class SocketMessage:
    def __init__(self):
        self.bin_hdr = ffi.new('BINARY_HEADER*')
        self.bin_buf = ffi.buffer(self.bin_hdr)
        self.addr = Sockaddr()
        self.data = bytes()

class NewDataThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        
    def run(self):
        while NewDataThreadRunning:
            while not NewData.empty():
                print('NewDataThread: ')
                msg = NewData.get()
                NewData.task_done() 
                
                #if msg.data[:8].decode('ascii').find('shutdown') >= 0:
                    #do shutdown
                #    print('shutdown msg found...')

                #elif msg.data[:16].decode('ascii').find('ShotSaveComplete') >= 0:
                    #do shot save complete
                #    print('ShotSaveComplete msg found...')
                    
                i = board_index(msg.addr)
                print('Boards[index] index: ', i)
                
                if i != NO_INDEX:
                    print('Boards[index]: ', i)
                    
                    if msg.bin_hdr.bchar.decode('ascii') == 'B':
                        print('new_data msg.bin_hdr.bchar: ', msg.bin_hdr.bchar) 
                        print('new_data msg.bin_hdr.data_type: ', msg.bin_hdr.data_type) 
                        print('new_data msg.bin_buf size: ', len(msg.bin_buf))
                        print('new_data msg.data size: ', len(msg.data))
                        
                        if msg.bin_hdr.data_type == START_OF_BINARY_TEXT_DATA:
                            print('data_type: START_OF_BINARY_TEXT_DATA')
                            do_ascii_message(i, msg.data.decode('ascii'))
                        
                        elif msg.bin_hdr.data_type == START_OF_IO_CHANGE_DATA:
                            #print('data_type: START_OF_IO_CHANGE_DATA')
                            convert_io_change_to_ascii(i, msg)
                        
                        elif msg.bin_hdr.data_type == START_OF_SINGLE_ANALOG_DATA or msg.bin_hdr.data_type == START_OF_BLOCK_ANALOG_DATA:
                            print('START_OF_BLOCK_ANALOG_DATA')
                        
                        elif msg.bin_hdr.data_type == CONNECTION_LOST:
                            #do Boards[index] connection lost
                            print('CONNECTION_LOST')
                        
                        else:
                            if msg.bin_hdr.packet_num == FIRST_PACKET_NUMBER:
                                start_of_binary_data(i, msg.bin_hdr)
                                print('FIRST_PACKET_NUMBER')
                            
                            if msg.bin_hdr.packet_num == Boards[i].current_packet_number:
                                send_to_terminal('Packet ' + str(Boards[i].current_packet_number) + ' repeated from machine ' + Boards[i].machine.name)                                
                                msg.bin_hdr.packet_num = 0 #already did this one so mark as invalid                                
                            
                            elif msg.bin_hdr.packet_num == (Boards[i].current_packet_number + 1):
                                n = msg.bin_hdr.nof_bytes
                                if n > 0 and Boards[i].chars_left_in_buffer > 0:
                                    if n > Boards[i].chars_left_in_buffer:
                                        n = Boards[i].chars_left_in_buffer
                                    #cp += sizeof( BINARY_HEADER )
                                    #memcpy( Boards[i].bp, cp, n );
                                    Boards[i].binarybuf += msg.data
                                    Boards[i].chars_left_in_buffer -= n
                                    Boards[i].current_len += n
                                    # may not need Boards[i].bp anymore with python
                                    #if ( Boards[i].chars_left_in_buffer > 0 )
                                    #    Boards[i].bp += n
                                    
                                Boards[i].current_packet_number = msg.bin_hdr.packet_num                        
                            
                            elif msg.bin_hdr.packet_num > Boards[i].current_packet_number + 1:
                                if ( TerminalIsVisible ):
                                    s = '**** Packet '
                                    s += str(Boards[i].current_packet_number+1)
                                    s += ' missing from machine '
                                    s += Boards[i].m.name
                                    s += ' ***'
                                    #log_network_error_string( s )
                                    send_to_terminal(s)

                                #update_monitor_status(Boards[i], resource_string(PACKET_ERROR_STRING) )
                                
                                #Make the packet number invalid so I don't do something stupid                                
                                msg.bin_hdr.packet_num = 0
                            
                            if msg.bin_hdr.packet_num == msg.bin_hdr.nof_packets:
                                if Boards[i].current_type == SAMPLE_TYPE or Boards[i].current_type == PARAMETERS_TYPE:
                                    Boards[i].add_binary_to_shotdata()
                                elif Boards[i].current_type == OP_STATUS_TYPE or Boards[i].current_type == OSCILLOSCOPE_TYPE:
                                    if i == CurrentBoardIndex:
                                        #do_new_rt_data()
                                        print('do_new_rt_data()')
                                Boards[i].current_type = ASCII_TYPE
                    
                    else:
                        do_ascii_message(i, msg.data.decode('ascii'))

                else:
                    print('no Boards[index] found for addr: ', msg.addr.addr)
  
class Ft3SendThread(threading.Thread):
    def __init__(self, threadID, name, counter, index):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.myboard = Boards[index]
    
    def run(self):
        self.myboard = Boards[index]
        self.myboard.ft3_send_event = threading.Event()
        
        if self.myboard.ft3_is_connected == False:
            self.myboard.set_connect_state(CONNECTING_STATE)
            status = self.myboard.ft3_connect()
            if status == FT3_SOCKET_CONNECT_ERROR:
                print('ft3 Boards[index] socket connect error')
            if self.myboard.ft3_is_connected:
                self.myboard.ms_at_last_contact = GetTickCount()
                self.set_connect_state(CONNECTED_STATE)
                #begin ft3_read_thread(Boards[index])
        else:
            self.myboard.set_connect_state(NOT_CONNECTED_STATE)
        
        print('Ft3SendThread running...')
        
        while True:
            self.ft3_send_event.wait(CONNECT_TIMEOUT_SEC)
            self.ft3_send_event.clear()
            
            if self.myboard.ft3_is_connected and ShuttingDown == False:
                t = GetTickCount()
                dt = t = self.myboard.ms_at_last_contact
                
                #try to reconnect
                if dt > CONNECT_TIMEOUT_MS:
                    self.myboard.set_connect_state(CONNECTING_STATE)
                    self.myboard.ft3_connect()
                    if self.myboard.ft3_is_connected:
                        self.myboard.ms_at_last_contact = GetTickCount()
                        #begin ft3_read_thread(Boards[index])
                    else:
                        self.myboard.set_connect_state(NOT_CONNECTED_STATE)
            
            if self.myboard.ft3_is_connected:
                # can't upload while a shot is in progress
                # see if it is time to cancel the do_not_upload
                # this should be done by the AT_HOME signal 
                if self.myboard.do_not_upload:
                    t = GetTickCount()
                    if self.myboard.do_not_upload_timeout > 0 and t > self.myboard.do_not_upload_timeout:
                        self.myboard.do_not_upload = False
                        self.myboard.do_not_upload_timeout = 0
                        #set_text( Dnu[myboard->index], EmptyString );
                        print('Dnu[' + str(self.myboard.index) + ']')
                        
                if self.myboard.f.qsize() == 0:
                    t = GetTickCount()
                    dt = t = self.myboard.ms_at_last_contact
                    
                    if dt > PING_TIMEOUT_MS:                        
                        # Send periodic echo-request to FT3 Boards[index] as heartbeat.
                        # Uses a dedicated echo-request/echo-response mechanism
                        # to interact with SOM Linux layer, i.e. command is not
                        # passed to FPGA performing A/D acquisition and control.
                        self.myboard.ms_at_last_contact = t
                        self.myboard.send_socket_message(FT3_ECHO_REQUEST, True)
                        
                while self.myboard.f.qsize() > 0:
                    mp = self.myboard.f.get()
                    
                    if mp.s.find(START_OF_UPLOAD) == 0:
                        # Don't start an upload if the do_not_upload is on
                        if self.myboard.do_not_upload == True:
                            break
                        self.myboard.do_not_upload = True
                        self.myboard.bytes_uploaded = 0
                        #update_monitor_status( myboard, resource_string(BEGIN_UPLOAD_STRING) );
                        print(BEGIN_UPLOAD_STRING)    
                    elif mp.s.find(END_OF_UPLOAD) == 0:
                        self.myboard.uploading = False
                        self.myboard.bytes_uploaded = 0
                        mp = self.myboard.f.get()
                        #update_monitor_status( myboard, resource_string(UPLOAD_COMPLETE_STRING) );
                        print(UPLOAD_COMPLETE_STRING)
                        # I turn off realtime updates during upload so I
                        # need to turn them back on now
                        if self.myboard.start_op_data_after_upload:
                            self.myboard.send_socket_message(SEND_OP_DATA_PACKETS, False)
                            self.myboard.start_op_data_after_upload = False
                    else:
                        sent = self.myboard.mysock.send(mp.s)
                        if sent == 0:
                            self.myboard.ft3_disconnect()
                            break
            
                if ShuttingDown:
                    self.myboard.ft3_disconnect()
                    self.myboard.set_connect_stat(NOT_CONNECTED_STATE)  
           
            if ShuttingDown:
                break
  
class Ft3ReadThread(threading.Thread):
    def __init__(self, threadID, name, counter, i):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.myboard = Boards[i]
    
    def run(self):
        print('read_thread started...')
        while ReadThreadRunning:            
            # message received from server 
            rvdata = bytearray()
            rvdata += ReadSocket.recv(1)

            # print the received message 
            print('bytearray received: ',len(rvdata))
            print('data: ',str(rvdata[0]))
            #print('Received from the server :',str(rvdata)) 
            
            # check for async bit
            if rvdata[0] & FT3_ASYNC_TYPE_BIT:
                is_async = True                
                rvdata[0] &= ~FT3_ASYNC_TYPE_BIT # unset message framing bit
            else:
                is_async = False
      
            if is_async:
                # ASYNCHRONOUS
                rvlen = 1 #first character is message framing byte
                while rvlen < FT3_ASYNC_TYPE_HEADER_LEN:
                    rvdata += ReadSocket.recv(FT3_ASYNC_TYPE_HEADER_LEN - rvlen)
                    if len(rvdata) > 0:
                        rvlen += len(rvdata)
                        print('rvlen: ', rvlen)
                    else:
                        print('socket error')
                
                print('Async Header: ', rvdata)
                print('Async Header len: ', len(rvdata))
               
                #datalen = rvdata[10] | rvdata[11] << 8
                datalen = ft3sim.uint8s_to_uint16(int(rvdata[10]), int(rvdata[11]))
                
                print('rvdata[10]: ', int(rvdata[10]))
                print('rvdata[11]: ', int(rvdata[11]))
                print('datalen: ', datalen)
                if (datalen + FT3_ASYNC_TYPE_HEADER_LEN > FT3_RECV_BUFFER_LEN):
                    # WARNING Rx buffer insufficient size for async header and data.
                    datalen = FT3_RECV_BUFFER_LEN - FT3_ASYNC_TYPE_HEADER_LEN
                
                #convert binary header to python struct
                bin_hdr = ffi.new('BINARY_HEADER*')
                bin_buf = ffi.buffer(bin_hdr)
                bin_buf[:] = rvdata
                msg = SocketMessage()
                msg.bin_buf[:] = rvdata
                msg.addr = Boards[CurrentBoardIndex].sockaddr
                
                print('bin_hdr.bchar: ', bin_hdr.bchar)
                print('bin_hdr.data_type: ', chr(bin_hdr.data_type))
                print('bin_hdr.nof_bytes: ', bin_hdr.nof_bytes)

                #read binary data
                rvlen = 0
                rvdata = bytes()
                while rvlen < datalen:
                    # Binary data.
                    print('rvlen: ', rvlen)
                    print('datalen: ', datalen)
                    rvdata += ReadSocket.recv(datalen - rvlen)
                    if (len(rvdata) > 0):
                        rvlen += len(rvdata)                    
                    else:
                        # TODO: Handle connection-closed (rv = 0) state.
                        print('socket error')
                
                #print('Async Message: ', rvdata)  
                print('Queue is empty: ', NewData.empty())
                
                msg.data = rvdata
                sa = Sockaddr()
                sa.addr = '192.168.130.45'
                msg.sockaddr = sa
                NewData.put(msg)
                NewData.join()
                
                #rvlen += FT3_ASYNC_TYPE_HEADER_LEN
            else:
                # synchronous
                rvlen = 1
                #rvdata = bytearray(0)
                while rvlen < FT3_RESPONSE_TYPE_LEN:
                    rvdata += ReadSocket.recv(FT3_RESPONSE_TYPE_LEN - rvlen)
                    if len(rvdata) > 0:
                        rvlen += len(rvdata)
                        print('sync rvlen: ', rvlen)
                    else:
                        print('socket error')
                
                if (rvdata.decode('ascii').find(FT3_ECHO_RESPONSE_INIT) == 0):
                # FT3 echo-request / echo-response.
                    if (not (self.myboard.connect_state & CONNECTED_STATE) and not (self.myboard.connect_state & NOT_MONITORED_STATE)):
                        # Periodic connection state consistency enforcement.
                        self.myboard.set_connect_state(CONNECTED_STATE)
                        print('set_connect_state(CONNECTED_STATE)')

                    if not FT3_ECHO_RESPONSE_VERBOSE:
                        # Zero length to discard FT3 echo-request / echo-response
                        # if verbose Boolean is false.
                        rvlen = 0
                
                msg = SocketMessage()                
                msg.addr = Boards[CurrentBoardIndex].sockaddr
                msg.data = rvdata
                sa = Sockaddr()
                sa.addr = '192.168.130.45'
                msg.sockaddr = sa
                
                print('Sync msg len: ', len(rvdata))
                #print('Sync Message: ', rvdata)
                NewData.put(msg)
                NewData.join()

def connect_one_board(i):
    not_connected = True
    if Boards[i].connect_state & CONNECTED_STATE:
        not_connected = False
        
    if Boards[i].is_monitoring:
        if Boards[i].is_ft3:
            if not Boards[i].ft3_send_thread_is_running:
                new_thread = Ft3SendThread(1, 'Ft3SendThread'+str(i), 1, i)
                new_thread.start()
        
    # I use the following to decide which error message to display if I don't talk
    Boards[i].have_response     = False
    Boards[i].upload_state      = WAITING_FOR_INFO
    Boards[i].version           = 0
    Boards[i].control_file_date = 0 # V447
    Boards[i].upload_copy_date  = 0 # V448
    Boards[i].set_connect_state( CONNECTING_STATE )
    
    if not_connected:
        Boards[i].send_socket_message( GetTimerFrequencyString, false )
        Boards[i].send_socket_message( GetVersionString, true )
        Boards[i].send_socket_message( GetControlFileDateString, true )
        Boards[i].send_socket_message( GetUploadCopyDateString, true )

    else:
        u = NOT_MONITORED_STATE
        if is_float_zero(Boards[i].part.min_stroke_length) or is_float_zero(Boards[i].part.total_stroke_length):
            u |= ZERO_STROKE_LENGTH_STATE
        Boards[i].set_connect_state( u )

def Main(): 
    # Define an ft3 Boards[index] 
    Boards.append(Ft3Board())
    sa = Sockaddr()
    #sa.sin_port = 12345
    #sa.addr = '127.0.0.1'
    sa.sin_port = 31000
    sa.addr = '192.168.130.45'
    Boards[0].sockaddr = sa
    machine = Machine()
    machine.name = 'Test Machine 001'
    Boards[0].machine = machine

    global ReadSocket
    # connect to server on local computer 
    ReadSocket.connect((Boards[CurrentBoardIndex].sockaddr.addr, Boards[CurrentBoardIndex].sockaddr.sin_port))
    #WriteSocket.connect((host,port+1))
        
    # start read thread
    global ReadThreadRunning
    ReadThreadRunning = True
    read_thread = Ft3ReadThread(1, 'Ft3ReadThread', 1, CurrentBoardIndex)
    read_thread.start()
    
    # start NewData thread
    global NewDataThreadRunning
    NewDataThreadRunning = True
    new_thread = NewDataThread(1, 'NewDataThread', 1)
    new_thread.start()
    
    # start shot_save thread
    global ShotSaveThreadRunning
    ShotSaveThreadRunning = True
    shot_save_thread = ShotSaveThread(1, 'ShotSaveThread', 1)
    shot_save_thread.start()
    
    print('Main thread continuing...')
    
    while True:
        time.sleep(.1)
        # ask the client whether he wants to continue 
        #cmd = input('\nSend command to server :')
        #if cmd == 'exit':
        #    ReadThreadRunning = False  
        #    NewDataThreadRunning = False
        #    ReadSocket.close()               
        #    read_thread.join()
        #    new_thread.join()
        #    shot_save_thread.join()
        #    break
        #elif cmd != 'async' and cmd != 'sync':
        #    print('invalid command')
        #    continue                   
        # message sent to server 
        #ReadSocket.send(cmd.encode('ascii')) 
 
if __name__ == '__main__': 
    Main() 
