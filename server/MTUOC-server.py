#    MTUOC-server v 2.0   
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

import socket
import os
import _thread
import time
import importlib
import sys
from datetime import datetime
import MTUOC_tags
import re



###YAML IMPORTS
import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

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

###Marian engine

def start_MarianCPU():
    print("Starting Marian CPU")
    startMariancommand="./marian-server-CPU -m "+MarianEngine_model+" -v "+MarianEngine_vocab_sl+" "+MarianEngine_vocab_tl+" --n-best "+"--alignment hard"+" -p "+ str(MarianEngine_port) +" --normalize 1 &"
    os.system(startMariancommand)

    
def start_MarianGPU():
    print("Starting Marian GPU")
    startMariancommand="./marian-server-GPU -m "+MarianEngine_model+" -v "+MarianEngine_vocab_sl+" "+MarianEngine_vocab_tl+" --n-best "+"--alignment hard"+" -p "+ str(MarianEngine_port) +" --normalize 1 &"
    os.system(startMariancommand)

def translate_segment_Marian(segment):
    try:
        #Translate tags with attributes
        tags=re.findall('(<[^>]+>)', segment)
        
        equiltag={}
        cont=0
        for tag in tags:
            if tag.find(" ")>-1:
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
            segmentPre=to_MT(segmentNOTAGS,tokenizerA,tokenizerB)
        elif preprocess_type=="NMT":
            segmentPre=to_MT(segmentNOTAGS, tokenizer, tcmodel, bpeobject, joiner, bos_annotate, eos_annotate)
        if MTUOCServer_verbose:print("Segment Pre: ",segmentPre)
        lseg=len(segmentPre)
        ws.send(segmentPre)
        translations = ws.recv()
        cont=0
        firsttranslationPre=""
        selectedtranslation=""
        selectedalignment=""
        candidates=translations.split("\n")
        #print("CANDIDATES:",candidates)
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
                if ltran>=lseg*MarianEngine_min_len_factor:
                    selectedtranslationPre=translation
                    selectedalignment=alignments
                    break
                cont+=1
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
                selectedtranslation=from_MT(selectedtranslationRestored)
        elif preprocess_type=="NMT":
                selectedtranslation=from_MT(selectedtranslationRestored,detokenizer, joiner, bos_annotate, eos_annotate)
        selectedtranslation=MTUOC_tags.fix_markup_ws(segment,selectedtranslation)
        if MTUOCServer_verbose:print("Translation No Tags: ",selectedtranslationPre)
        if MTUOCServer_verbose:print("Translation Tags: ",selectedtranslationRestored)
        if MTUOCServer_verbose:print("Word Alignment: ",selectedalignment)
        
        
        for clau in equiltag.keys():
            selectedtranslation=selectedtranslation.replace(clau,equiltag[clau])
            
        if toLower:
            selectedtranslation=selectedtranslation.upper()
        if MTUOCServer_verbose:print("Translation: ",selectedtranslation)
    
    except:
        print("ERROR:",sys.exc_info())
    return(selectedtranslation)

###OpenNMT engine

def start_ONMT(config,url_root,ip,port,debug):
    if MTUOCServer_verbose:print("STARTING ONMT SERVER")
    startONMTcommand="onmt_server --ip "+str(ip)+" --port "+str(port)+" --url_root "+str(url_root)+" --config "+config+" &"
    os.system(startONMTcommand)
    
def translate_segment_OpenNMT(segment):
    try:
        url = "http://"+OpenNMTEngine_ip+":"+str(OpenNMTEngine_port)+"/translator/translate"

        headers = {'content-type': 'application/json'}
        tags=re.findall('(<[^>]+>)', segment)

        equiltag={}
        cont=0
        for tag in tags:
            if tag.find(" ")>-1:
                tagmod="<tag"+str(cont)+">"
                equiltag[tagmod]=tag
                segment=segment.replace(tag,tagmod)
                t=tag.split(" ")[0].replace("<","")
                ttanc="</"+t+">"
                ttancmod="</tag"+str(cont)+">"
                segment=segment.replace(ttanc,ttancmod)
                equiltag[ttancmod]=ttanc
                cont+=1
        
                        
        if MTUOCServer_verbose:
            now=str(datetime.now())
            print("---------")
            print(now)
            print("Segment: ",segment)
            
        #Dealing with uppercased sentences
        toLower=False
        if segment==segment.upper():
            segment=segment.lower().capitalize()
            toLower=True

        segmentNOTAGS=remove_tags(segment)
        if MTUOCServer_verbose:print("Segment No Tags: ",segmentNOTAGS)
        if preprocess_type=="SentencePiece":
            segmentPre=to_MT(segmentNOTAGS,tokenizerA,tokenizerB)
        elif preprocess_type=="NMT":
            segmentPre=to_MT(segmentNOTAGS, tokenizer, tcmodel, bpeobject, joiner, bos_annotate, eos_annotate)
        if MTUOCServer_verbose:print("Segment Pre: ",segmentPre)
        params = [{ "src" : segmentPre}]

        response = requests.post(url, json=params, headers=headers)
        target = response.json()
        selectedtranslationPre=target[0][0]["tgt"]
        if "align" in target[0][0]:
            selectedalignment=target[0][0]["align"][0]
        else:
            selectedalignments=""
        if MTUOCServer_verbose:print("Translation Pre: ",selectedtranslationPre)
        if MTUOCServer_restore_tags:
            try:
                if preprocess_type=="SentencePiece":
                    SOURCETAGSTOK=tokenizerA.tokenize(segment)
                    SOURCETAGSTOKSP=tokenizerA.unprotect(" ".join(tokenizerB.tokenize(tokenizerA.protect_tags(SOURCETAGSTOK))[0]))
                    SOURCETAGSTOKSP="<s> "+SOURCETAGSTOKSP+" </s>"
                    selectedtranslationRestored=MTUOC_tags.reinsert_wordalign(SOURCETAGSTOKSP,selectedalignment,selectedtranslationPre,splitter="▁")
                elif preprocess_type=="NMT":
                    print
                    SOURCETAGSTOK=tokenizerA.tokenize(segment)
                    glossary=[]
                    tags=re.findall('(<[^>]+>)', SOURCETAGSTOK)
                    for tag in tags:
                        glossary.append(tag)
                    bpe = BPE(open(Preprocess_bpecodes,encoding="utf-8"),separator=joiner,glossaries=glossary)
                    SOURCETAGSTOKBPE=bpe.process_line(SOURCETAGSTOK)
                    selectedtranslationRestored=MTUOC_tags.reinsert_wordalign(SOURCETAGSTOKBPE,selectedalignment,selectedtranslationPre)
                    print("*****************",selectedtranslationRestored)
            except:
                print("ERROR RESTORING:",sys.exc_info())
        else:
            selectedtranslationRestored=selectedtranslationPre  
        
        if preprocess_type=="SentencePiece":
            selectedtranslation=from_MT(selectedtranslationRestored)
        elif preprocess_type=="NMT":
            selectedtranslation=from_MT(selectedtranslationRestored,detokenizer, joiner, bos_annotate, eos_annotate)
        
        selectedtranslation=MTUOC_tags.fix_markup_ws(segment,selectedtranslation)
        
        if MTUOCServer_verbose:print("Translation No Tags: ",selectedtranslationPre)
        if MTUOCServer_verbose:print("Translation Tags: ",selectedtranslationRestored)
        if MTUOCServer_verbose:print("Word Alignment: ",selectedalignment)
        
        for clau in equiltag.keys():
            selectedtranslation=selectedtranslation.replace(clau,equiltag[clau])
        if toLower:
            selectedtranslation=selectedtranslation.upper()
                
        if MTUOCServer_verbose:print("Translation: ",selectedtranslation)
        
        return(selectedtranslation)
    except:
        ("ERROR:",sys.exc_info())
    
#ModernMT engine

def translate_segment_ModernMT(segment):
    url = "http://"+ModernMTEngine_ip+":"+str(ModernMTEngine_port)+"/translate"
    params={}
    params['q']=preprocessMMT(segment)
    response = requests.get(url,params=params)
    target = response.json()
    translation=postprocessMMT(target['data']["translation"])
    return(translation)



#Moses engine

def start_Moses(ip,port,ini):
    if MTUOCServer_verbose:print("STARTING MOSES SERVER")
    startMosescommand="./moses -f "+ini+" --server --server-port "+str(port)+" --print-alignment-info "
    os.system(startMosescommand)

def translateAliMoses(aliBRUT):
    newali=[]
    for a in aliBRUT:
        at=str(a['source-word'])+"-"+str(a['target-word'])
        newali.append(at)
    newali=" ".join(newali)

    return(newali)

def translate_segment_Moses(segment):
    try:
        print("SEGMENT:",segment)
        equiltag={}
        cont=0
        tags=re.findall('(<[^>]+>)', segment)
        #Dealing with uppercased sentences
        toLower=False
        if segment==segment.upper():
            segment=segment.lower().capitalize()
            toLower=True
        for tag in tags:
            if tag.find(" ")>-1:
                tagmod="<tag"+str(cont)+">"
                equiltag[tagmod]=tag
                segment=segment.replace(tag,tagmod)
                t=tag.split(" ")[0].replace("<","")
                ttanc="</"+t+">"
                ttancmod="</tag"+str(cont)+">"
                segment=segment.replace(ttanc,ttancmod)
                equiltag[ttancmod]=ttanc
                cont+=1
        print("EQUILTRADS:",equiltag)
                        
        if MTUOCServer_verbose:
            now=str(datetime.now())
            print("---------")
            print(now)
            print("Segment: ",segment)
        SOURCETAGSTOK=tokenizerA.tokenize(segment)
        print("SOURCETAGSTOK",SOURCETAGSTOK)
        segmentNOTAGS=remove_tags(segment)
        segmentreplacenum=to_MT(segmentNOTAGS, tokenizer, tcmodel)
        print("segmentreplacenum",segmentreplacenum)
        param = {"text": segmentreplacenum}
        result = proxyMoses.translate(param)
        translationREP=result['text']
        alignmentBRUT=result['word-align']
        alignments=translateAliMoses(alignmentBRUT)
        selectedtranslationPre=from_MT(translationREP,segmentNOTAGS,detokenizer)
        print("alignments",alignments)
        print("selectedtranslationPre",selectedtranslationPre)
        if MTUOCServer_restore_tags:
            #selectedtranslationRestored=restore_tags(SOURCETAGSTOK,selectedtranslationPre,alignments)
            selectedtranslationRestored=MTUOC_tags.reinsert_wordalign(SOURCETAGSTOK,alignments,selectedtranslationPre)
            print("selectedtranslationRestored",selectedtranslationRestored)
            
            
        else:
            selectedtranslationRestored=selectedtranslationPre 
        print("selectedtranslationRestored",selectedtranslationRestored)
        if MTUOCServer_verbose:print("Translation No Tags: ",selectedtranslationPre)
        
        
        
        if MTUOCServer_verbose:print("Translation Tags: ",selectedtranslationRestored)
        if MTUOCServer_verbose:print("Word Alignment: ",alignments)
        selectedtranslation=MTUOC_tags.fix_markup_ws(segment,selectedtranslationRestored)
        for clau in equiltag.keys():
            selectedtranslation=selectedtranslation.replace(clau,equiltag[clau])
        
        if MTUOCServer_verbose:print("Translation: ",selectedtranslation)
        if toLower:
            selectedtranslation=selectedtranslation.upper()
        return(selectedtranslation)
    except:
        print("ERROR",sys.exc_info())


####MAIN

if len(sys.argv)==1:
    configfile="config-server.yaml"
else:
    configfile=sys.argv[1]

stream = open(configfile, 'r',encoding="utf-8")
config=yaml.load(stream, Loader=yaml.FullLoader)


preprocess_type=config["Preprocess"]["type"]

sllang=config["Preprocess"]["sl_lang"]
tllang=config["Preprocess"]["tl_lang"]
MTUOCtokenizer=config["Preprocess"]["sl_tokenizer"]

if preprocess_type=="SentencePiece":
    sp_model_SL=config["Preprocess"]["sp_model_SL"]

elif preprocess_type=="SMT":
    Preprocess_tcmodel=config["Preprocess"]["tcmodel"]
    MTUOCdetokenizer=config["Preprocess"]["tl_tokenizer"]

elif preprocess_type=="NMT":
    Preprocess_tcmodel=config["Preprocess"]["tcmodel"]
    Preprocess_bpecodes=config["Preprocess"]["bpecodes"]
    MTUOCdetokenizer=config["Preprocess"]["tl_tokenizer"]
    joiner=config["Preprocess"]["joiner"]
    bos_annotate=config["Preprocess"]["bos_annotate"]
    eos_annotate=config["Preprocess"]["eos_annotate"]

MTUOCServer_verbose=config["MTUOCServer"]["verbose"]
MTUOCServer_verbose=config["MTUOCServer"]["verbose"]
MTUOCServer_restore_tags=config["MTUOCServer"]["restore_tags"]
MTUOCServer_port=config["MTUOCServer"]["port"]
MTUOCServer_type=config["MTUOCServer"]["type"]
MTUOCServer_MTengine=config["MTUOCServer"]["MTengine"]
MTUOCServer_verbose=config["MTUOCServer"]["verbose"]
startMTEngine=config["MTUOCServer"]["startMTEngine"]

if not MTUOCServer_MTengine=="ModernMT" and preprocess_type=="SentencePiece":
    from MTUOC_process_segment_SP import to_MT
    from MTUOC_process_segment_SP import from_MT
    import pyonmttok
    TOKENIZERA=MTUOCtokenizer
    SPMODEL=sp_model_SL
    tokenizerA=importlib.import_module(TOKENIZERA)
    tokenizerB=pyonmttok.Tokenizer("space", spacer_annotate=True, segment_numbers=True, sp_model_path=SPMODEL)

if not MTUOCServer_MTengine=="ModernMT" and preprocess_type=="NMT":
    from MTUOC_process_segment_NMT import to_MT
    from MTUOC_process_segment_NMT import from_MT
    from MTUOC_truecaser import load_model
    from MTUOC_BPE import load_codes
    from MTUOC_BPE import apply_BPE
    from subword_nmt.apply_bpe import BPE
    tokenizer = importlib.import_module(MTUOCtokenizer,"tokenize")
    TOKENIZERA=MTUOCtokenizer
    tokenizerA=importlib.import_module(TOKENIZERA)
    detokenizer = importlib.import_module(MTUOCdetokenizer,"detokenize")
    if MTUOCServer_verbose:print("Loading TC Model.")    
    tcmodel=load_model(Preprocess_tcmodel)
    if MTUOCServer_verbose:print("Loading BPE")
    bpeobject=load_codes(Preprocess_bpecodes)

if not MTUOCServer_MTengine=="ModernMT" and preprocess_type=="SMT":
    from MTUOC_process_segment_SMT import to_MT
    from MTUOC_process_segment_SMT import from_MT
    from MTUOC_truecaser import load_model
    tokenizer = importlib.import_module(MTUOCtokenizer,"tokenize")
    TOKENIZERA=MTUOCtokenizer
    tokenizerA=importlib.import_module(TOKENIZERA)
    detokenizer = importlib.import_module(MTUOCdetokenizer,"detokenize")
    if MTUOCServer_verbose:print("Loading TC Model.")    
    tcmodel=load_model(Preprocess_tcmodel)


#Marian
if MTUOCServer_MTengine=="Marian":
    from websocket import create_connection
    
    from MTUOC_tags import remove_tags



    MarianEngine_ip=config["MarianEngine"]["ip"]
    MarianEngine_port=config["MarianEngine"]["port"]
    MarianEngine_type=config["MarianEngine"]["type"]
    MarianEngine_model=config["MarianEngine"]["model"]
    MarianEngine_vocab_sl=config["MarianEngine"]["vocab_sl"]
    MarianEngine_vocab_tl=config["MarianEngine"]["vocab_tl"]
    MarianEngine_min_len_factor=float(config["MarianEngine"]["min_len_factor"])
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        conn=s.connect_ex((MarianEngine_ip, MarianEngine_port))
        if conn == 0:marianstarted=True
    if startMTEngine:
        if MarianEngine_type=="CPU":
            _thread.start_new_thread(start_MarianCPU,())
        elif MarianEngine_type=="GPU":
            _thread.start_new_thread(start_MarianGPU,())
            
    service="ws://"+MarianEngine_ip+":"+str(MarianEngine_port)+"/translate"
    error=True
    while error:
        try:
            ws = create_connection(service)
            error=False
        except:
            print("Error: waiting for Marian server to start. Retrying in 5 seconds.")
            time.sleep(5)
            error=True
    
            
#OpenNMT
if MTUOCServer_MTengine=="OpenNMT":
    import requests
    #from onmt.bin.server import start as onmt_server_start
   
    from MTUOC_tags import remove_tags


    OpenNMTEngine_ip=config["OpenNMTEngine"]["ip"]
    OpenNMTEngine_port=config["OpenNMTEngine"]["port"]
    OpenNMTEngine_confjson=config["OpenNMTEngine"]["confjson"]
    #OpenNMTEngine_model=config["OpenNMTEngine"]["model"] THE MODEL IS GIVEN IN THE configONMT.json file
    OpenNMTEngine_url_root=config["OpenNMTEngine"]["url_root"]
    OpenNMTEngine_debug=True
    if startMTEngine:
        _thread.start_new_thread(start_ONMT,(OpenNMTEngine_confjson,OpenNMTEngine_url_root,OpenNMTEngine_ip,OpenNMTEngine_port,OpenNMTEngine_debug))
    
    url = "http://"+OpenNMTEngine_ip+":"+str(OpenNMTEngine_port)+OpenNMTEngine_url_root+"/translate"

    headers = {'content-type': 'application/json'}
    
    
    

#ModernMT

def startModernMT(ModernMTEnginte_path,ModernMTEngine_engine,ModernMTEngine_port):
    if MTUOCServer_verbose:print("Starting ModernMT")
    startModernMTcommand=ModernMTEnginte_path+"/mmt start -e "+ModernMTEngine_engine+" -p "+str(ModernMTEngine_port)+" &"
    os.system(startModernMTcommand)

if MTUOCServer_MTengine=="ModernMT":
    import requests
if MTUOCServer_MTengine=="ModernMT" and startMTEngine:
    if MTUOCServer_verbose:print("REMEMBER: ModernMT engine should be started manually")
    ModernMTEngine_ip=config["ModernMTEngine"]["ip"]
    ModernMTEngine_port=config["ModernMTEngine"]["port"]
    ModernMTEngine_path=config["ModernMTEngine"]["path_to_mmt"]
    ModernMTEngine_engine=config["ModernMTEngine"]["engine"]
    ModernMTEngine_sl=config["ModernMTEngine"]["sl"]
    ModernMTEngine_tl=config["ModernMTEngine"]["tl"]
    ModernMTEngine_preprocess=config["ModernMTEngine"]["preprocess"]
    ModernMTEngine_postprocess=config["ModernMTEngine"]["postprocess"]
    if MTUOCServer_verbose:print("IP:",ModernMTEngine_ip)
    if MTUOCServer_verbose:print("PORT:",ModernMTEngine_port)
    if MTUOCServer_verbose:print("PATH:",ModernMTEngine_path)
    if MTUOCServer_verbose:print("ENGINE",ModernMTEngine_engine)
    if MTUOCServer_verbose:print("SL",ModernMTEngine_sl)
    if MTUOCServer_verbose:print("TL",ModernMTEngine_tl)
    if not ModernMTEngine_path=="None":
        _thread.start_new_thread(startModernMT,(ModernMTEngine_path,ModernMTEngine_engine,ModernMTEngine_port))
    if not ModernMTEngine_preprocess=="None":
        from ModernMTEngine_preprocess import preprocessMMT
    else:
        def preprocessMMT(segment):
            return(segment)
    if not ModernMTEngine_postprocess=="None":
        from ModernMTEngine_postprocess import postprocessMMT
    else:
        def postprocessMMT(segment):
            return(segment)
#MOSES

if MTUOCServer_MTengine=="Moses":
    import xmlrpc.client
    from MTUOC_truecaser import load_model
    from MTUOC_truecaser import truecase
    from MTUOC_detruecaser import detruecase
    from MTUOC_replacenumbers import replace
    from MTUOC_restorenumbers import restore

    
    from MTUOC_tags import remove_tags

    MosesEngine_ini=config['MosesEngine']['ini']
    MosesEngine_ip=config['MosesEngine']['ip']
    MosesEngine_port=config['MosesEngine']['port']
    if startMTEngine:
        _thread.start_new_thread(start_Moses, (MosesEngine_ip,MosesEngine_port,MosesEngine_ini))
    proxyMoses = xmlrpc.client.ServerProxy("http://"+MosesEngine_ip+":"+str(MosesEngine_port)+"/RPC2")
    
   

#STARTING MTUOC SERVER

if MTUOCServer_type=="MTUOC":
    from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
    
    class MTUOC_server(WebSocket):
        def handleMessage(self):
            if MTUOCServer_verbose:print("Translating: ",self.data)
            if MTUOCServer_MTengine=="Marian":
                self.translation=translate_segment_Marian(self.data)
            elif MTUOCServer_MTengine=="OpenNMT":
                self.translation=translate_segment_OpenNMT(self.data)
            elif MTUOCServer_MTengine=="ModernMT":
                self.translation=translate_segment_ModernMT(self.data)
            elif MTUOCServer_MTengine=="Moses":
                self.translation=translate_segment_Moses(self.data)
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

      

def translateforONMT(segment):
    if MTUOCServer_verbose:print("Translating: ",segment)
    if MTUOCServer_MTengine=="Marian":
        translation=translate_segment_Marian(segment)
    elif MTUOCServer_MTengine=="OpenNMT":
        translation=translate_segment_OpenNMT(segment)
    elif MTUOCServer_MTengine=="ModernMT":
        translation=translate_segment_ModernMT(segment)
    elif MTUOCServer_MTengine=="Moses":
        translation=translate_segment_Moses(segment)
    if MTUOCServer_verbose:print("Translation: ",translation)
    return(translation)

if MTUOCServer_type=="OpenNMT":
    from flask import Flask, jsonify, request
    MTUOCServer_ONMT_url_root=config["MTUOCServer"]["ONMT_url_root"]
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    out={}
    def start(url_root="./translator",
              host="0.0.0.0",
              port=5000,
              debug=True):
        def prefix_route(route_function, prefix='', mask='{0}{1}'):
            def newroute(route, *args, **kwargs):
                return route_function(mask.format(prefix, route), *args, **kwargs)
            return newroute

        app = Flask(__name__)
        app.route = prefix_route(app.route, url_root)

        @app.route('/translate', methods=['POST'])
        def translateONMT():
            inputs = request.get_json(force=True)
            inputs0=inputs[0]
            out = {}
            try:
                out = [[]]
                ss=inputs0['src']
                ts=translateforONMT(ss)
                response = {"src": ss, "tgt": ts,
                                "n_best": 0, "pred_score": 0}
                    
                out[0].append(response)
            except:
                out['error'] = "Error"
                out['status'] = STATUS_ERROR

            return jsonify(out)
            
        
        app.run(debug=debug, host=host, port=port, use_reloader=False,
            threaded=True)
    url_root=MTUOCServer_ONMT_url_root
    ip="0.0.0.0"
    ip=get_IP_info()
    debug="store_true"
    start(url_root=MTUOCServer_ONMT_url_root, host=ip, port=MTUOCServer_port,debug=debug)
    
    
    

if MTUOCServer_type=="NMTWizard":
    from flask import Flask, jsonify, request
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    out={}
    def start(url_root="",
              host="0.0.0.0",
              port=5000,
              debug=True):
        def prefix_route(route_function, prefix='', mask='{0}{1}'):
            def newroute(route, *args, **kwargs):
                return route_function(mask.format(prefix, route), *args, **kwargs)
            return newroute

        app = Flask(__name__)
        app.route = prefix_route(app.route, url_root)

        @app.route('/translate', methods=['POST'])
        def translateONMT():
            inputs = request.get_json(force=True)
            sourcetext=inputs["src"][0]["text"]
            if MTUOCServer_verbose:print("SOURCE TEXT",sourcetext)
            try:
                targettext=translateforONMT(sourcetext)
                out={"tgt": [[{"text": targettext}]]}
            except:
                out['error'] = "Error"
                out['status'] = STATUS_ERROR
            return jsonify(out)
        app.run(debug=debug, host=host, port=port, use_reloader=False,
                threaded=True)
    url_root=""
    ip="0.0.0.0"
    ip=get_IP_info()
    debug="store_true"
    start(url_root=url_root, host=ip, port=MTUOCServer_port,debug=debug)


def translateforModernMT(segment):
    if MTUOCServer_verbose:print("Translating: ",segment)
    if MTUOCServer_MTengine=="Marian":
        translation=translate_segment_Marian(segment)
    elif MTUOCServer_MTengine=="OpenNMT":
        translation=translate_segment_OpenNMT(segment)
    elif MTUOCServer_MTengine=="ModernMT":
        translation=translate_segment_ModernMT(segment)
    elif MTUOCServer_MTengine=="Moses":
        translation=translate_segment_Moses(segment)
    if MTUOCServer_verbose:print("Translation: ",translation)
    return(translation)

if MTUOCServer_type=="ModernMT":
    from flask import Flask, jsonify, request
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    def start(
              url_root="",
              host="",
              port=8000,
              debug=True):
        def prefix_route(route_function, prefix='', mask='{0}{1}'):
            def newroute(route, *args, **kwargs):
                return route_function(mask.format(prefix, route), *args, **kwargs)
            return newroute
        app = Flask(__name__)
        app.route = prefix_route(app.route, url_root)
        @app.route('/translate', methods=['GET'])
        def translateModernMT():
            out = {}
            try:
                out['data']={}
                segment=request.args['q']
                translation=translateforModernMT(segment)
                out['data']['translation']=translation
            except:
                out['status'] = STATUS_ERROR
            return jsonify(out)
        ip=get_IP_info()
        app.run(debug=True, host=ip, port=MTUOCServer_port, use_reloader=False,
                threaded=True)
    start()

def translate(segment):
    print("Translating: ",segment['text'])
    if MTUOCServer_MTengine=="Marian":
        translation=translate_segment_Marian(segment['text'])
    elif MTUOCServer_MTengine=="OpenNMT":
        translation=translate_segment_OpenNMT(segment['text'])
    elif MTUOCServer_MTengine=="ModernMT":
        translation=translate_segment_ModernMT(segment['text'])
    elif MTUOCServer_MTengine=="Moses":
        translation=translate_segment_Moses(segment['text'])
    print("Translation: ",translation)
    translationdict={}
    translationdict["text"]=translation
    return(translationdict)

if MTUOCServer_type=="Moses":
    from xmlrpc.server import SimpleXMLRPCServer
    server = SimpleXMLRPCServer(
    ("", MTUOCServer_port),
    logRequests=True,)
    server.register_function(translate)
    server.register_introspection_functions()
    # Start the server
    try:
        ip=get_IP_info()
        print("Moses server IP:",ip," port:",MTUOCServer_port)
        print('Use Control-C to exit')
        server.serve_forever()
    except KeyboardInterrupt:
        print('Exiting')
