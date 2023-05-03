import websocket
import socket
import time
import sys
import config

from MTUOC_misc import printLOG


def connect_to_Marian():
    print("CONNECT TO MARIAN.")
    from websocket import create_connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        conn=s.connect_ex((config.MTEngineIP, config.MTEnginePort))
        if conn == 0:marianstarted=True
    service="ws://"+config.MTEngineIP+":"+str(config.MTEnginePort)+"/translate"
    error=True
    while error:
        try:
            config.ws = create_connection(service)
            printLOG(1,"Connection with Marian Server created","")
            error=False
        except:
            printLOG(1,"Error: waiting for Marian server to start. Retrying in 2 seconds.",sys.exc_info())
            time.sleep(2)
            error=True
    
def translate_segment_Marian(segmentPre):
    translation_candidates={}
    translation_candidates["segmentNOTAGSPre"]=segmentPre
    lseg=len(segmentPre)
    try:
        config.ws.send(segmentPre)
    except:
        printLOG(1,"Error sending segment to Marian.",sys.exc_info())
    translations = config.ws.recv()
    tc_aux=translations.split("\n")
    translation_candidates["translationNOTAGSPre"]=[]
    translation_candidates["alignments"]=[]
    for tca in tc_aux:
        try:
            segmentaux=tca.split(" ||| ")[1].strip()
            alignmentaux=tca.split(" ||| ")[2].strip()
            translation_candidates["translationNOTAGSPre"].append(segmentaux)
            translation_candidates["alignments"].append(alignmentaux)
        except:
            pass
    return(translation_candidates)