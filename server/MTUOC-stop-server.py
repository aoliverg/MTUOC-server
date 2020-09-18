#!/usr/bin/env python3

#    MTUOC_stop_server
#    Copyright (C) 2020  Antoni Oliver
#
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
import os
import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

stream = open('config-server.yaml', 'r',encoding="utf-8")
config=yaml.load(stream, Loader=yaml.FullLoader)

MTUOCServer_port=config["MTUOCServer"]["port"]
MTUOCServer_MTengine=config["MTUOCServer"]["MTengine"]


stopcommand1="fuser -k "+str(MTUOCServer_port)+"/tcp &"
os.system(stopcommand1)
print("MTUOC Server stopped.")

if MTUOCServer_MTengine=="Marian":
    try:
        MarianServer_port=config["MarianEngine"]["port"]
        stopcommand2="fuser -k "+str(MarianServer_port)+"/tcp &"
        os.system(stopcommand2)
        print("Marian Server stopped.")
    except:
        print("Unable to stop Marian server",sys.exc_info())
        

elif MTUOCServer_MTengine=="OpenNMT":

    try:
        OpenNMTServer_port=config["MarianEngine"]["port"]
        stopcommand2="fuser -k "+str(OpenNMTServer_port)+"/tcp &"
        os.system(stopcommand2)
        print("OpenNMT Server stopped.")
    except:
        print("Unable to stop OpenNMT server",sys.exc_info())

elif MTUOCServer_MTengine=="ModernMT":
    try:
        ModernMTServer_port=config["ModernMTEngine"]["port"]
        ModernMTEngine_path=config["ModernMTEngine"]["path_to_mmt"]
        ModernMTEngine_engine=config["ModernMTEngine"]["engine"]
        if not ModernMTEngine_path=="None":
            stopcommand3=ModernMTEngine_path+"/mmt stop -e "+ModernMTEngine_engine+" &"
            os.system(stopcommand3)
        #stopcommand2="fuser -k "+str(ModernMTServer_port)+"/tcp &"
        #os.system(stopcommand2)
        print("ModernMT Server stopped.")
    except:
        print("Unable to stop ModernMT server",sys.exc_info())

elif MTUOCServer_MTengine=="Moses":
    try:
        MosesServer_port=config["MosesEngine"]["port"]
        stopcommand2="fuser -k "+str(MosesServer_port)+"/tcp &"
        os.system(stopcommand2)
        print("Moses Server stopped.")
    except:
        print("Unable to stop Moses server",sys.exc_info())
    




