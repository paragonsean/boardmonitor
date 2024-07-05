
#1. convert int to bytes
#   int(123).to_bytes(1,'big')

#2. convert bytes to int
#	int.from_bytes(b,'big')

# import socket programming library 
import socket 
from _thread import *
import threading 
import numpy as np
from cffi import FFI
from ft3_board import *

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
    """)    

# sizeof(sockaddr_in) = 16
# sizeof(in_addr) = 4
# sizeof(SOCKET_MESSAGE) = 1371
# sizeof(BINARY_HEADER) = 12
    
print_lock = threading.Lock() 

#this class implements a circular list iterator
class LoopIter:
    def __init__(self, data):
        self.data = data
        self.index = 0
        
    def get_next_item(self):
        if self.index >= len(self.data):
            self.index = 0
        item = self.data[self.index]
        self.index += 1
        return item

class TestMan:
    data_types = ([START_OF_BINARY_TEXT_DATA,
                   START_OF_IO_CHANGE_DATA,
                   START_OF_BINARY_POS_SAMPLES,
                   START_OF_BINARY_TIME_SAMPLES,
                   START_OF_BINARY_PARAMETERS,
                   START_OF_BINARY_OP_STATUS_DATA,
                   START_OF_BINARY_OSCILLOSCOPE_DATA,
                   START_OF_SINGLE_ANALOG_DATA,
                   START_OF_BLOCK_ANALOG_DATA,
                   CONNECTION_LOST])
                   
    messages = ([CYCLE_START,
                 TIMEOUT,
                 ANALOG_RESPONSE,
                 TIMER_FREQ_RESPONSE+'1234',
                 AT_HOME_RESPONSE,
                 POS_AT_IMPACT_RESPONSE,
                 VERSION_RESPONSE+'7.53',
                 VERSION_RESPONSE2+'7.53',
                 FATAL_OR_WARNING_RESPONSE,
                 ControlFileDateString+'0',
                 UploadCopyDateString+'0',
                 '1234'])
                 
    test_cases = LoopIter([[0,0],
                           [0,1],
                           [0,2],
                           [0,3],
                           [0,4],
                           [0,5],
                           [0,6],
                           [0,7],
                           [0,8],
                           [0,9],
                           [0,10],
                           [1,11],
                           [2,11],
                           [3,11],
                           [4,11],
                           [5,11],
                           [6,11]])
    
    def get_next_test_case(self):
        ix = self.test_cases.get_next_item()
        id = ix[0]
        im = ix[1]        
        return self.data_types[id], self.messages[im]
 
# thread function 
def threaded(c):
    
    test_man = TestMan()
   
    while True: 
  
        # data received from client 
        data = c.recv(1024) 
        
        if not data: 
            print('Bye') 
              
            # lock released on exit 
            print_lock.release() 
            break  
       
        if str(data.decode('ascii')) == 'async':
            print('async')            
            
            # get a test case from TestMan
            test_case = test_man.get_next_test_case()
            test_data_type = test_case[0]
            test_msg = test_case[1]
            
            bin_hdr = ffi.new("BINARY_HEADER*")
            bin_buf = ffi.buffer(bin_hdr)
            bin_hdr.bchar = bytes([ord('B') | FT3_ASYNC_TYPE_BIT])            
            bin_hdr.data_type = test_data_type
            bin_hdr.nof_bytes = len(test_msg)
            bin_hdr.packet_num = 1
            c.send(bin_buf)
            
            msg = test_msg
            #slen = len(msg)            
            #blen = 120 - slen
            blen = len(msg)
            print('sending: ', msg)
            #msg += bytes(blen).decode('ascii')
            c.send(msg.encode('ascii'))

        else:
            print('received: ', str(data.decode('ascii')))
            data += bytes(FT3_RESPONSE_TYPE_LEN - len(data))
            print('sending: ', str(len(data)) + ' bytes')
            c.send(data)
            
    # connection closed 
    c.close() 

# function to break the UINT16 num into two UINT8s
def uint16_to_uint8s(num):
    himask = np.uint16(65280)
    lomask = np.uint16(255)
    
    hibyte = np.uint8((num & himask) >> 8)
    lobyte = np.uint8(num & lomask)
    
    return (lobyte, hibyte)

# function to combine two UINT8s into one UINT16
def uint8s_to_uint16(lobyte, hibyte):
    return (np.uint16(lobyte | (hibyte << 8)))
 
  
def Main(): 
    host = "" 
  
    # reserve a port on your computer 
    # in our case it is 12345 but it 
    # can be anything 
    port = 12345
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.bind((host, port)) 
    print("socket binded to post", port) 
  
    # put the socket into listening mode 
    s.listen(5) 
    print("socket is listening") 
  
    # a forever loop until client wants to exit 
    while True: 
  
        # establish connection with client 
        c, addr = s.accept() 
  
        # lock acquired by client 
        print_lock.acquire() 
        print('Connected to :', addr[0], ':', addr[1]) 
  
        # Start a new thread and return its identifier 
        start_new_thread(threaded, (c,)) 
    s.close() 
  
  
if __name__ == '__main__': 
    Main() 
