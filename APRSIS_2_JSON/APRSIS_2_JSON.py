#
# Python (Bottle)
# APRSIS_2_JSON
# v 0.1, 30.07.2024
# https://github.com/dkxce
# en,ru,1251,utf-8
#

import re
import aprslib
import socket
from datetime import datetime, timedelta
from bottle import route, run, response
import threading


TIME_LIMIT = 1200
BUFFER = None


class TimeBuffer():
    
    def __init__(self):
        self.buffer = []
        
    def __proc__(self, who: str = None):
        buffer = []
        for b in self.buffer:
            if b[0] <= datetime.utcnow(): continue
            if who and who == b[1]: continue            
            buffer.append(b)
        self.buffer = buffer
            
    def add(self, who: str, data: dict):
        self.__proc__(who)
        self.buffer.append( (datetime.utcnow() + timedelta(seconds=TIME_LIMIT), who, data) )
        
    def get(self):
        self.__proc__()
        return {b[2]['who']: b[2] for b in self.buffer}
        

def callback(packet):
    # print(packet)
    try:
        pkt = aprslib.parse(packet)
        if (lat := pkt.get('latitude')) and (lon := pkt.get('longitude')):
            who = pkt.get('object') or pkt.get('from')
            smb = pkt.get('symbol_table') + pkt.get('symbol')
            cmn = pkt.get('comment')
            print(f'{who} {smb} {lat} {lon} {cmn}')
            data = {'who': who, 'symbol': smb, 'lat': lat, 'lon': lon, 'comment': cmn, 'received': str(datetime.utcnow())}
            if BUFFER: BUFFER.add(who, data)
    except:
        pass
    

@route('/')
def index(): 
    response.set_header('Access-Control-Allow-Headers', '*')
    response.set_header('Access-Control-Allow-Origin', '*')
    response.set_header('Access-Control-Allow-Methods', 'GET')
    response.set_header('Access-Control-Max-Age', str(TIME_LIMIT))
    return BUFFER.get() if BUFFER else {}


def server(): run(host='localhost', port=8009)    

if __name__ == "__main__":    
    BUFFER = TimeBuffer()
    (threading.Thread(target=server, args=())).start()
    AIS = aprslib.IS("FAPRS-1", "-1", "rotate.aprs2.ru", 14580)
    AIS.set_filter("p/R/U m/350 r/55.55/37.55/350")
    AIS.connect()
    AIS.consumer(callback, raw=True)