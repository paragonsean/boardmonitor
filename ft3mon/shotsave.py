import threading
from ft3_shot_data import *
from sqlalchemy import create_engine, event
from log_file import *
import ft3_shot_data
import socket

DBEng = create_engine('postgresql+psycopg2://postgres:admin@localhost:5432/ft3shot', echo=False)

#get the greatest shot number in the database and use it to set CurrentShot
ft3_shot_data.CurrentShot = DBEng.execute("SELECT MAX(shot) FROM ft3meta").fetchone()[0]
if ft3_shot_data.CurrentShot is None:
    ft3_shot_data.CurrentShot = 0
else:
    ft3_shot_data.CurrentShot += 1

MetaDataReadyEvent = threading.Event()
EventDataReadyEvent = threading.Event()
ShotSaveEvent = threading.Event()
ShotSaveThreadRunning = False
SHOTSAVE_WAIT_TIMEOUT = 1.005
NO_INDEX = -1

INFINITE = 0xFFFFFFFF

MAX_SHOTSAVE_BUFFERS = 20
ShotSaveBuf = []  # this is BufPtr in C++ code
for i in range(0,MAX_SHOTSAVE_BUFFERS):
    ShotSaveBuf.append(0)

class SHOT_BUFFER_ENTRY:
    def __init__(self):
        self.save_failed = bool()
        self.has_alarm = bool()
        self.has_warning = bool()
        self.pn = PROFILE_NAME_ENTRY()
        self.f = FTII_FILE_DATA()
        self.param = DOUBLE_ARRAY_CLASS()

class PROFILE_NAME_ENTRY:
    def __init__(self):
        self.computer = str()
        self.machine = str()
        self.part = str()
        self.shot = str()

class DOUBLE_ARRAY_CLASS:
    def __init__(self):
        self.p = float()
        self.n = int()

class ShotSaveEntry:
    def __init__(self):
        self.save_failed = bool()
        self.has_alarm = bool()
        self.has_warning = bool()
        self.pn = PROFILE_NAME_ENTRY()
        self.f = FTII_FILE_DATA()
        self.param = DOUBLE_ARRAY_CLASS()
        self.debug_log = LogFile('debug.log')

# bool has_new_alarm
# bool new_has_warning
# PART_NAME_ENTRY partname
# FTII_FILE_DATA fsorc
# DOUBLE_ARRAY_CLASS psorc
def add_to_shotsave(new_has_alarm, new_has_warning, partname, fsorc, psorc):
    global ShotSaveBuf
    for i in range(0, MAX_SHOTSAVE_BUFFERS):
        if ShotSaveBuf[i] == 0:
            b = ShotSaveEntry()
            b.save_failed = False
            b.has_alarm   = new_has_alarm
            b.has_warning = new_has_warning
            b.pn          = partname
            b.f = fsorc #b.f.move(fsorc)
            #b.param.move(psorc)
            ShotSaveBuf[i] = b
            return True

    return False

def save_this_machine(machine_to_save):
    global ShotSaveBuf
    debug_log = LogFile('debug.log')
    #debug_log.add_entry('save_this_machine: enter')
    #debug_log.add_entry('save_this_machine: MAX_SHOTSAVE_BUFFERS = ' + str(MAX_SHOTSAVE_BUFFERS))
    i_to_save = NO_INDEX
    for i in range(0, MAX_SHOTSAVE_BUFFERS):
        #debug_log.add_entry('save_this_machine: ' + str(i))
        if ShotSaveBuf[i] != 0:
            #debug_log.add_entry('save_this_machine: step 001')
            if ShotSaveBuf[i].pn.machine == machine_to_save:
                #debug_log.add_entry('save_this_machine: ' + machine_to_save + ' found')
                new_time = ShotSaveBuf[i].f.shot_time
                if i_to_save == NO_INDEX:
                    i_to_save = i
                    time_to_save = new_time
                elif (new_time - time_to_save) < 0:
                    i_to_save = i
                    time_to_save = new_time

    if i_to_save != NO_INDEX:
        #save_shot(ShotSaveBuf[i])
        debug_log.add_entry('save_this_machine: i_to_save = ' + str(i_to_save))
        ShotSaveBuf[i_to_save].f.put(DBEng)
        ShotSaveBuf[i_to_save] = 0
    else:
        debug_log.add_entry('save_this_machine: no index to save')
        # Mark all shots for this machine as save failed
        for i in range(0, MAX_SHOTSAVE_BUFFERS):
            if ShotSaveBuf[i] != 0:
                if ShotSaveBuf[i].pn.machine == machine_to_save:
                    ShotSaveBuf[i].save_failed = True

def save_all_shots():
    global ShotSaveBuf
    debug_log = LogFile('debug.log')
    first_index = save_all_shots.current_index # static variable in C++ code

    while True:
        if ShotSaveBuf[save_all_shots.current_index] != 0:
            debug_log.add_entry('found a shot in ShotSaveBuf')
            b = ShotSaveBuf[save_all_shots.current_index]
            if not b.save_failed:
                debug_log.add_entry('save_this_machine(' + b.pn.machine + ')')
                save_this_machine(b.pn.machine)

        save_all_shots.current_index += 1
        #debug_log.add_entry('save_all_shots: ' + str(save_all_shots.current_index))
        
        if save_all_shots.current_index >= MAX_SHOTSAVE_BUFFERS:
            save_all_shots.current_index = 0
        if save_all_shots.current_index == first_index:
            break
save_all_shots.current_index = 0 # static variable initialization

class ShotSaveThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.debug_log = LogFile('debug.log')

    def startup(self):
        print('shot_save_thread startup')
        global ShotSaveThreadRunning
        ShotSaveThreadRunning = True
        self.debug_log.add_entry('startup')
        
    def shutdown(self):
        print('shot_save_thread shutdown')
        self.debug_log.add_entry('shutdown')

    def run(self):
        self.debug_log.add_entry('shot_save_thread started...')
        self.startup()
        global ShotSaveBuf
        global ShotSaveThreadRunning
        while ShotSaveThreadRunning:
            ms_to_wait = None
            for i in range(0, MAX_SHOTSAVE_BUFFERS):
                if ShotSaveBuf[i] != 0:
                    ms_to_wait = SHOTSAVE_WAIT_TIMEOUT
                    ShotSaveBuf[i].save_failed = False
                    
            ShotSaveEvent.wait(ms_to_wait)
            ShotSaveEvent.clear()
            self.debug_log.add_entry('!!! ShotSaveEvent !!!')
            save_all_shots()
            self.debug_log.add_entry('save_all_shots() called')
                    #if ShutdownState == SHUTTING_DOWN_SHOTSAVE:
                    #    ShotSaveThreadRunning = False
            
            #meta and event data are written else where so wait for those to finish
            global MetaDataReadyEvent
            global EventDataReadyEvent
            MetaDataReadyEvent.wait()
            EventDataReadyEvent.wait()
            
            #send new shot message to server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            try:
                server_socket.connect(('127.0.0.1', 12345))
                server_socket.send(('NewShot: ' + str(ft3_shot_data.CurrentShot-1) + ',').encode('ascii'))
                server_socket.close()
            except Exception as e:
                print('ERROR: ' + str(e))
            
            print('server_socket msg sent')
            
            MetaDataReadyEvent.clear()
            EventDataReadyEvent.clear()

        self.shutdown()
