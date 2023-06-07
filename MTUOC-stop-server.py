#    MTUOC_stop_server
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
import os
import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import argparse

#YAML

parser = argparse.ArgumentParser(description='MTUOC-server. With no arguments the config-server.yaml file will be used.')
parser.add_argument('-c','--config', action="store", dest="config", help='The tokenizer to be used.',required=False)
parser.add_argument('-p','--port', action="store", dest="port", type=int, help='The MTUOC server port.',required=False)

args = parser.parse_args()
if args.config:
    configfile=args.config
else:
    configfile="config-server.yaml"

stream = open(configfile, 'r',encoding="utf-8")
config=yaml.load(stream, Loader=yaml.FullLoader)

MTEnginePort=config["MTEngine"]["port"]
MTUOCServer_port=config["MTUOCServer"]["port"]

if args.port:
    MTUOCServer_port=args.port

try:
    stopcommand2="fuser -k "+str(MTEnginePort)+"/tcp"
    os.system(stopcommand2)
    print("MT Engine stopped.")
except:
    print("Unable to stop MT Engine",sys.exc_info())
    
try:
    stopcommand2="fuser -k "+str(MTUOCServer_port)+"/tcp"
    os.system(stopcommand2)
    print("MTUOC server stopped.")
except:
    print("Unable to stop MTUOC server",sys.exc_info())
