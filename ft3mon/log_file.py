from datetime import datetime

class LogFile:
    def __init__(self, filename):
        self.f = filename
        
    def add_entry(self, msg):
        t = datetime.today()
        s = t.isoformat() + ' ' + msg + '\n'
        h = open(self.f, 'a')
        h.write(s)
        h.close()