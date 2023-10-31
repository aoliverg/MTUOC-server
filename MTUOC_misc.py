import socket
from datetime import datetime
import sys

import config

def printLOG(vlevel,m1,m2=""):
    cadena=str(datetime.now())+"\t"+str(m1)+"\t"+str(m2)
    if vlevel<=config.verbosity_level:
        print(cadena)
        if config.log_file:
            config.sortidalog.write(cadena+"\n") 

def get_IP_info(): 
    try: 
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
        return(IP)
    except: 
        IP = '127.0.0.1'
        return(IP)
    finally:
        s.close()
        
def capitalizeMTUOC(cadena):
    resultat=cadena
    try:
        resultat=cadena[0].upper()+cadena[1:]
    except:  
        pass      
    return(resultat)
