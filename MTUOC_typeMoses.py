import sys
from xmlrpc.server import SimpleXMLRPCServer

from MTUOC_misc import get_IP_info
from MTUOC_misc import printLOG
import config

from MTUOC_translate import translate_para

def translate(segment):
    #function for Moses server
    translation=translate_para(segment['text'])
    translationdict={}
    translationdict["text"]=translation
    return(translationdict) 

def start_Moses_server():
    server = SimpleXMLRPCServer(("", config.MTUOCServer_port),logRequests=True,)
    server.register_function(translate)
    server.register_introspection_functions()
    # Start the server
    try:
        ip=get_IP_info()
        printLOG(1,"MTUOC server IP:   ", ip)
        printLOG(1,"MTUOC server port: ", config.MTUOCServer_port)
        printLOG(1,"MTUOC server type:  Moses")
        server.serve_forever()
    except KeyboardInterrupt:
        printLOG(1,'Exiting')