#    MTUOC-server v 3.0   
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

###GENERIC IMPORTS
import sys
import threading
import os
import socket
import time
import re
from datetime import datetime
import importlib
import pyonmttok



###YAML IMPORTS
import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

#MTUOC imports

from MTUOC_URLs import replace_URLs as replace_URLs
from MTUOC_URLs import restore_URLs as restore_URLs
from MTUOC_EMAILs import replace_EMAILs as replace_EMAILs
from MTUOC_EMAILs import restore_EMAILs as restore_EMAILs
from MTUOC_tags import remove_tags

from MTUOC_truecaser import load_model
from MTUOC_truecaser import truecase    

import MTUOC_process_segment_NMT
import MTUOC_process_segment_SMT
import MTUOC_process_segment_SP

from MTUOC_restorenumbers import restore
from MTUOC_tags import remove_tags

import MTUOC_tags

def startMTEngineThread(startMTEngineCommand):
    if not startMTEngineCommand.endswith("&"):
        command=startMTEngineCommand +" &"
    else:
        command=startMTEngineCommand
    os.system(command)

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

def translate_segment_Marian(segmentPre):
    lseg=len(segmentPre)
    ws.send(segmentPre)
    translations = ws.recv()
    cont=0
    firsttranslationPre=""
    selectedtranslation=""
    selectedalignment=""
    candidates=translations.split("\n")
    translation=""
    alignments=""
    
    for candidate in candidates:
        camps=candidate.split(" ||| ")
        if len(camps)>2:
            translation=camps[1]
            alignments=camps[2]
            if cont==0:
                if not len(translation.strip())==0:
                    selectedtranslationPre=translation
                    selectedalignment=alignments
                else:
                    cont-=1
            ltran=len(translation)
            if ltran>=lseg*min_len_factor:
                selectedtranslationPre=translation
                selectedalignment=alignments
                break
            cont+=1
    return(selectedtranslationPre, selectedalignment)
    
def translate_segment(segment):
    try:
        #leading and trailing spaces
        leading_spaces=len(segment)-len(segment.lstrip())
        trailing_spaces=len(segment)-len(segment.rstrip())-1
        
        #html/xml tags
        existingtags=[]
        segment,equilURLs=replace_URLs(segment)
        segment,equilEMAILs=replace_EMAILs(segment)
        tags=re.findall('(<[^>]+>)', segment)
        existingtags.extend(tags)
        equiltag={}
        cont=0
        for tag in tags:
            tagmod="<tag"+str(cont)+">"
            equiltag[tagmod]=tag
            segment=segment.replace(tag,tagmod)
            t=tag.split(" ")[0].replace("<","")
            ttanc="</"+t+">"
            ttancmod="</tag"+str(cont)+">"
            segment=segment.replace(ttanc,ttancmod)
            equiltag[ttancmod]=ttanc
            cont+=1
        #special tags {1} {2} ...
        tags=re.findall('(\{[[0-9]+\})', segment)
        existingtags.extend(tags)
        for tag in tags:
            tagmod="<tag"+str(cont)+">"
            equiltag[tagmod]=tag
            segment=segment.replace(tag,tagmod)
            t=tag.split(" ")[0].replace("<","")
            ttanc="</"+t+">"
            ttancmod="</tag"+str(cont)+">"
            segment=segment.replace(ttanc,ttancmod)
            equiltag[ttancmod]=ttanc
            cont+=1
            
        #Dealing with uppercased sentences
        toLower=False
        if segment==segment.upper():
            segment=segment.lower().capitalize()
            toLower=True
                        
        if MTUOCServer_verbose:
            now=str(datetime.now())
            print("---------")
            print(now)
            print("Segment: ",segment)
        segmentNOTAGS=remove_tags(segment)
        
        if MTUOCServer_verbose:print("Segment No Tags: ",segmentNOTAGS)
        
        if preprocess_type=="SentencePiece":
            segmentPre=MTUOC_process_segment_SP.to_MT(segmentNOTAGS,tokenizerA,tokenizerB,tcmodel,bos_annotate,eos_annotate)
        elif preprocess_type=="NMT":
            segmentPre=MTUOC_process_segment_NMT.to_MT(segmentNOTAGS, tokenizer, tcmodel, bpeobject, joiner, bos_annotate, eos_annotate)
        if MTUOCServer_verbose:print("Segment Pre: ",segmentPre)
        
        (selectedtranslationPre, selectedalignment)=translate_segment_Marian(segmentPre)
        
        if MTUOCServer_verbose:print("Translation Pre: ",selectedtranslationPre)
        if MTUOCServer_restore_tags:
            try:
                if preprocess_type=="SentencePiece":
                    SOURCETAGSTOK=tokenizerA.tokenize(segment)
                    SOURCETAGSTOKSP=tokenizerA.unprotect(" ".join(tokenizerB.tokenize(tokenizerA.protect_tags(SOURCETAGSTOK))[0]))
                    SOURCETAGSTOKSP="<s> "+SOURCETAGSTOKSP+" </s>"
                    selectedtranslationRestored=MTUOC_tags.reinsert_wordalign(SOURCETAGSTOKSP,selectedalignment,selectedtranslationPre,splitter="▁")
                elif preprocess_type=="NMT":
                    SOURCETAGSTOK=tokenizerA.tokenize(segment)
                    glossary=[]
                    tags=re.findall('(<[^>]+>)', SOURCETAGSTOK)
                    for tag in tags:
                        glossary.append(tag)
                    bpe = BPE(open(Preprocess_bpecodes,encoding="utf-8"),separator=joiner,glossaries=glossary)
                    SOURCETAGSTOKBPE=bpe.process_line(SOURCETAGSTOK)
                    selectedtranslationRestored=MTUOC_tags.reinsert_wordalign(SOURCETAGSTOKBPE,selectedalignment,selectedtranslationPre)
                    
            except:
                print("ERROR RESTORING:",sys.exc_info())
        else:
            selectedtranslationRestored=selectedtranslationPre
        
        
        if preprocess_type=="SentencePiece":
            selectedtranslation=MTUOC_process_segment_SP.from_MT(selectedtranslationRestored,sp_joiner,bos_annotate,eos_annotate)
        elif preprocess_type=="NMT":
                selectedtranslation=MTUOC_process_segment_NMT.from_MT(selectedtranslationRestored,detokenizer, joiner, bos_annotate, eos_annotate)
        
        selectedtranslation=MTUOC_tags.fix_markup_ws(segment,selectedtranslation)
        
        if MTUOCServer_verbose:print("Translation No Tags: ",selectedtranslationPre)
        if MTUOCServer_verbose:print("Translation Tags: ",selectedtranslationRestored)
        if MTUOCServer_verbose:print("Word Alignment: ",selectedalignment)
        
        for clau in equiltag.keys():
            print(clau,equiltag[clau])
            if equiltag[clau] in existingtags:
                selectedtranslation=selectedtranslation.replace(clau,equiltag[clau])
            else:
                selectedtranslation=selectedtranslation.replace(clau,"")
            print(selectedtranslation)
        if toLower:
            selectedtranslation=selectedtranslation.upper()
            
        #restoring leading and trailing spaces
        lSP=leading_spaces*" "
        tSP=trailing_spaces*" "
        selectedtranslation=restore_URLs(selectedtranslation,equilURLs)
        selectedtranslation=restore_EMAILs(selectedtranslation,equilEMAILs)
        selectedtranslation=lSP+selectedtranslation.strip()+tSP
        if MTUOCServer_verbose:print("Translation: ",selectedtranslation)
    except:
        print("ERROR:",sys.exc_info())
    return(selectedtranslation)

if len(sys.argv)==1:
    configfile="config-server.yaml"
else:
    configfile=sys.argv[1]

stream = open(configfile, 'r',encoding="utf-8")
config=yaml.load(stream, Loader=yaml.FullLoader)


startMTEngine=config["MTEngine"]["startMTEngine"]
startMTEngineCommand=config["MTEngine"]["startCommand"]
MTEnginePort=config["MTEngine"]["port"]
MTEngineIP=config["MTEngine"]["IP"]
min_len_factor=config["MTEngine"]["min_len_factor"]

if startMTEngine:
    x = threading.Thread(target=startMTEngineThread, args=(startMTEngineCommand,))
    x.start()
    
MTUOCServer_verbose=config["MTUOCServer"]["verbose"]
MTUOCServer_restore_tags=config["MTUOCServer"]["restore_tags"]
MTUOCServer_port=config["MTUOCServer"]["port"]
MTUOCServer_type=config["MTUOCServer"]["type"]
MTUOCServer_MTengine=config["MTUOCServer"]["MTengine"]

preprocess_type=config["Preprocess"]["type"]

sllang=config["Preprocess"]["sl_lang"]
tllang=config["Preprocess"]["tl_lang"]
MTUOCtokenizer=config["Preprocess"]["sl_tokenizer"]
MTUOCdetokenizer=config["Preprocess"]["tl_tokenizer"]

sp_model_SL=config["Preprocess"]["sp_model_SL"]
sp_vocabulary_SL=config["Preprocess"]["sp_vocabulary_SL"]
Preprocess_tcmodel=config["Preprocess"]["tcmodel"]
Preprocess_bpecodes=config["Preprocess"]["bpecodes"]
joiner=config["Preprocess"]["joiner"]
bos_annotate=config["Preprocess"]["bos_annotate"]
eos_annotate=config["Preprocess"]["eos_annotate"]
sp_joiner=config["Preprocess"]["sp_joiner"]


if preprocess_type=="SentencePiece":
    TOKENIZERA=MTUOCtokenizer
    SPMODEL=sp_model_SL
    SPVOCABULARY=sp_vocabulary_SL
    print("SP",SPMODEL,SPVOCABULARY)
    tokenizerA=importlib.import_module(TOKENIZERA)
    tokenizerB=pyonmttok.Tokenizer("space", spacer_annotate=True, segment_numbers=True, sp_model_path=SPMODEL)#, vocabulary_path=SPVOCABULARY, vocabulary_threshold=50)
    if not Preprocess_tcmodel==None:
        tcmodel=load_model(Preprocess_tcmodel)
    else:
        tcmodel=None
    

if MTUOCServer_MTengine=="Marian":
    from websocket import create_connection
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        conn=s.connect_ex((MTEngineIP, MTEnginePort))
        if conn == 0:marianstarted=True
    service="ws://"+MTEngineIP+":"+str(MTEnginePort)+"/translate"
    error=True
    while error:
        try:
            ws = create_connection(service)
            print("Connection with Marian Server created")
            error=False
        except:
            print("Error: waiting for Marian server to start. Retrying in 5 seconds.")
            time.sleep(5)
            error=True


#STARTING MTUOC SERVER

if MTUOCServer_type=="MTUOC":
    from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
    
    class MTUOC_server(WebSocket):
        def handleMessage(self):
            if MTUOCServer_verbose:print("Translating: ",self.data)
            if MTUOCServer_MTengine=="Marian":
                self.translation=translate_segment(self.data)
                
            self.sendMessage(self.translation)

        def handleConnected(self):
            if MTUOCServer_verbose:
                print('Connected to: ',self.address[0].split(":")[-1])
            else:
                pass

        def handleClose(self):
            if MTUOCServer_verbose:
                print('Disconnected from:',self.address[0].split(":")[-1])
            else:
                pass
    
    server = SimpleWebSocketServer('', MTUOCServer_port, MTUOC_server)
    ip=get_IP_info()
    print("MTUOC server IP:",ip," port:",MTUOCServer_port)
    server.serveforever()
