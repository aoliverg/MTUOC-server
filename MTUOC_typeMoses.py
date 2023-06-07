#    MTUOC_typeMoses
#    Copyright (C) 2023  Antoni Oliver
#    v. 07/06/2023
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

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