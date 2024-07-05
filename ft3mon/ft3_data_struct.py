from cffi import FFI

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

bin_hdr = ffi.new("BINARY_HEADER*")
bin_buf = ffi.buffer(bin_hdr)
bin_hdr.bchar = "B".encode()
bin_hdr.data_type = ord('d')
bin_hdr.nof_bytes = 120
    