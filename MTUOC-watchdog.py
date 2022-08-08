# -*- coding: utf-8 -*-
#    MTUOC-watchdog.py
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

import argparse
import codecs
import sys
import time
import os
import subprocess

#IMPORTS FOR MTUOC CLIENT
from websocket import create_connection
import socket

#IMPORTS FOR MOSES CLIENT
import xmlrpc.client

#IMPORTS FOR OPENNMT / MODERNMT CLIENT
import requests

###YAML IMPORTS
import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def print_info(message1,message2=""):
    print(message1,message2)

def disconnect(type):
    if type=="MTUOC":
        try:
            ws.close()
        except:
            pass

def connect(ip,port,server_type):
    if server_type=="MTUOC":
        try:
            service="ws://"+ip+":"+str(port)+"/translate"
            global ws
            ws = create_connection(service)
        except:
            errormessage="Error connecting to MTUOC: \n"+ str(sys.exc_info()[1])
            print_info("Error", errormessage)
            
    elif server_type=="Moses":
        try:
            global proxyMoses
            proxyMoses = xmlrpc.client.ServerProxy("http://"+ip+":"+str(port)+"/RPC2")
        except:
            errormessage="Error connecting to Moses: \n"+ str(sys.exc_info()[1])
            print_info("Error", errormessage)      
            
    elif server_type=="OpenNMT":
        try:
            global urlOpenNMT
            urlOpenNMT = "http://"+ip+":"+str(port)+"/translator/translate"
        except:
            errormessage="Error connecting to OpenNMT: \n"+ str(sys.exc_info()[1])
            print_info("Error", errormessage)   
    elif server_type=="NMTWizard":
        try:
            global urlNMTWizard
            urlNMTWizard = "http://"+ip+":"+str(port)+"/translate"
        except:
            errormessage="Error connecting to NMTWizard: \n"+ str(sys.exc_info()[1])
            print_info("Error", errormessage)           
    elif server_type=="ModernMT":
        try:
            global urlModernMT
            urlModernMT = "http://"+ip+":"+str(port)+"/translate"
        except:
            errormessage="Error connecting to ModernMT: \n"+ str(sys.exc_info()[1])
            print_info("Error", errormessage)
    
def translate_segment_MTUOC(segment):
    translation=""
    try:
        ws.send(segment)
        translation = ws.recv()
    except:
        errormessage="Error retrieving translation from MTUOC: \n"+ str(sys.exc_info()[1])
        print_info("Error", errormessage)
    return(translation)

    
def translate_segment_OpenNMT(segment):
    global urlOpenNMT
    translation=""
    try:
        headers = {'content-type': 'application/json'}
        params = [{ "src" : segment}]
        response = requests.post(urlOpenNMT, json=params, headers=headers)
        target = response.json()
        translation=target[0][0]["tgt"]
    except:
        errormessage="Error retrieving translation from OpenNMT: \n"+ str(sys.exc_info()[1])
        print_info("Error", errormessage)
    return(translation)

    
def translate_segment_NMTWizard(segment):
    global urlNMTWizard
    translation=""
    try:
        headers = {'content-type': 'application/json'}
        params={ "src": [  {"text": segment}]}
        response = requests.post(urlNMTWizard, json=params, headers=headers)
        target = response.json()
        translation=target["tgt"][0][0]["text"]
    except:
        print(sys.exc_info())
        errormessage="Error retrieving translation from NMTWizard: \n"+ str(sys.exc_info()[1])
        print_info("Error", errormessage)
    return(translation)
    
def translate_segment_ModernMT(segment):
    global urlModernMT
    params={}
    params['q']=segment
    response = requests.get(urlModernMT,params=params)
    target = response.json()
    translation=target['data']["translation"]
    return(translation)
        
def translate_segment_Moses(segment):
    translation=""
    try:
        param = {"text": segment}
        result = proxyMoses.translate(param)
        translation=result['text']
    except:
        errormessage="Error retrieving translation from Moses: \n"+ str(sys.exc_info()[1])
        print_info("Error", errormessage)
    return(translation)
    
def translate_segment(segment):
    MTEngine=type
    if MTEngine=="MTUOC":
        translation=translate_segment_MTUOC(segment)
    elif MTEngine=="OpenNMT":
        translation=translate_segment_OpenNMT(segment)
    elif MTEngine=="NMTWizard":
        translation=translate_segment_NMTWizard(segment)
    elif MTEngine=="ModernMT":
        translation=translate_segment_ModernMT(segment)
    elif MTEngine=="Moses":
        translation=translate_segment_Moses(segment)
    translation=translation.replace("\n"," ")
    return(translation)



parser = argparse.ArgumentParser(description='MTUOC-watchdog: command line MTUOC program to check if a MTUOC server is up an running. Otherwise it restarts the server')
parser.add_argument('-c','--config', dest='configfile', help='The config file for the server to start.', action='store',default="config-server.yaml")
parser.add_argument('-s','--segment', dest='segment', help='The test segment to translate.', action='store',required=True)
parser.add_argument('-t','--time', dest='time', type=int, help='The time in seconds between tests.', action='store',required=True)

args = parser.parse_args()


stream = open(args.configfile, 'r',encoding="utf-8")
config=yaml.load(stream, Loader=yaml.FullLoader)


ip="localhost"
port=config["MTUOCServer"]["port"]
type=config["MTUOCServer"]["type"]

#commandStart=config["MTEngine"]["startCommand"]
commandStart="./start -c "+args.configfile+" &"
commandStop="./stop -c "+args.configfile

os.system(commandStop)
os.system(commandStart)

time.sleep(args.time)
try:
    disconnect(type)  
    connect(ip,port,type)
except:
    print("ERROR: server not started. Starting.")
    os.system(commandStop)
    os.system(commandStart)



while 1:
    try:
        print("Waiting to test.")
        time.sleep(args.time)
        print("Translating the test sentence: ",args.segment)
        traduccio=translate_segment(args.segment)
        print("Test translation: ",traduccio)
        if traduccio=="":
            print("ERROR: restarting server")
            disconnect(type)
            os.system(commandStop)
            os.system(commandStart)
            connect(ip,port,type)
    except:
        print("ERROR: restarting server",sys.exc_info()[0])
        os.system(commandStop)
        os.system(commandStart)
        disconnect(type)   
        connect(ip,port,type)       
