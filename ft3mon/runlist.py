EmptyPartName = 'Default Part'

class RunListEntry:
    def __init__(self):
        bits = bytes([0])
        partname = str()
    
class RunList:
    def __init__(self):
        list = []
        mask = bytes([0])
        
    def find_part(self, bits):
        if len(self.list) == 0:
            return EmptyPartName

        x = bits
        x &= self.mask

        for i in range(0, len(list)):
            if list[i].bits == x:
                return list[i].partname
                
        return list[0].partname
        
    def current_part_name(self):
        if len(self.list) > 0:
            return list[0].partname
        else:
            return EmptyPartName