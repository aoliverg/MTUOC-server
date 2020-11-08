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
import codecs
import xmlrpc.client
import json



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

from MTUOC_BPE import load_codes
from MTUOC_BPE import apply_BPE
from subword_nmt.apply_bpe import BPE

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


def translate(segment):
    #function for Moses server
    print("Translating: ",segment['text'])
    translation=translate_segment(segment['text'])
    print("Translation: ",translation)
    translationdict={}
    translationdict["text"]=translation
    return(translationdict)

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

def translate_segment_OpenNMT(segmentPre):
    params = [{ "src" : segmentPre}]

    response = requests.post(url, json=params, headers=headers)
    target = response.json()
    selectedtranslationPre=target[0][0]["tgt"]
    if "align" in target[0][0]:
        selectedalignment=target[0][0]["align"][0]
    else:
        selectedalignments=""
    
    
    return(selectedtranslationPre, selectedalignment)
    

def translateAliMoses(aliBRUT):
    newali=[]
    for a in aliBRUT:
        at=str(a['source-word'])+"-"+str(a['target-word'])
        newali.append(at)
    newali=" ".join(newali)

    return(newali)

def translate_segment_Moses(segmentPre):
    param = {"text": segmentPre}
    result = proxyMoses.translate(param)
    translationREP=result['text']
    alignmentBRUT=result['word-align']
    alignments=translateAliMoses(alignmentBRUT)
    return(translationREP, alignments)    
    
def translate_segment_ModernMT(segment):
    url = "http://"+MTEngineIP+":"+str(MTEnginePort)+"/translate"
    params={}
    params['q']=segment
    response = requests.get(url,params=params)
    target = response.json()
    translation=target['data']["translation"]
    return(translation) ###ALIGNMENTS?

def translate_segment(segment):
    try:
        if not pre_script=="None":
            stemp=codecs.open("segment.tmp","w",encoding="utf-8")
            stemp.write(segment+"\n")
            stemp.close()
            os.system(pre_script)
            stemp=codecs.open("segmentpre.tmp","r",encoding="utf-8")
            segment=stemp.readline().rstrip()
            stemp.close()
            
        if MTUOCServer_MTengine=="ModernMT":
            selectedtranslation=translate_segment_ModernMT(segment)
        else:
            #leading and trailing spaces
            leading_spaces=len(segment)-len(segment.lstrip())
            trailing_spaces=len(segment)-len(segment.rstrip())-1
            
            #URLs and EMAILs
            if MTUOCServer_URLs:
                segment,equilURLs=replace_URLs(segment)
            if MTUOCServer_EMAILs:
                segment,equilEMAILs=replace_EMAILs(segment)
            
            #html/xml tags
            if MTUOCServer_restore_tags:
                existingtags=[]
                tags=re.findall('(<[^>]+>)', segment)
                existingtags.extend(tags)
                equiltag={}
                cont=0
                for tag in tags:
                    tagmod="<tag"+str(cont)+">"
                    equiltag[tagmod]=tag
                    segment=segment.replace(tag,tagmod,1)
                    if tag.find(" ")>-1: ttanc=tag.split(" ")[0].replace("<","</")+">"
                    else: ttanc=tag.replace("<","</")
                    ttancmod="</tag"+str(cont)+">"
                    if ttanc in tags: tags.remove(ttanc)
                    segment=segment.replace(ttanc,ttancmod)
                    equiltag[ttancmod]=ttanc
                    cont+=1
                #special tags {1} {2} ...
                tags=re.findall('(\{[0-9]+\})', segment)
                existingtags.extend(tags)
                for tag in tags:
                    tagmod="<tag"+str(cont)+"/>"
                    equiltag[tagmod]=tag
                    segment=segment.replace(tag,tagmod)
                    t=tag.split(" ")[0].replace("<","")
                    cont+=1
            else:
                segment=remove_tags(segment)
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
            elif preprocess_type=="SMT":
                segmentPre=MTUOC_process_segment_SMT.to_MT(segmentNOTAGS, tokenizer, tcmodel)
            elif preprocess_type=="Custom":
                stemp=codecs.open("segment.tmp","w",encoding="utf-8")
                stemp.write(segmentNOTAGS+"\n")
                stemp.close()
                os.system(preprocess_command)
                stemp=codecs.open("segmentpre.tmp","r",encoding="utf-8")
                segmentPre=stemp.readline().rstrip()
                stemp.close()
            
            if MTUOCServer_verbose:print("Segment Pre: ",segmentPre)
            
            if MTUOCServer_MTengine=="Marian":
                (selectedtranslationPre, selectedalignment)=translate_segment_Marian(segmentPre)
            elif MTUOCServer_MTengine=="OpenNMT":
                (selectedtranslationPre, selectedalignment)=translate_segment_OpenNMT(segmentPre)
            elif MTUOCServer_MTengine=="Moses":
                (selectedtranslationPre, selectedalignment)=translate_segment_Moses(segmentPre)
            
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
                    elif preprocess_type=="SMT":
                        SOURCETAGSTOK=tokenizerA.tokenize(segment)
                        selectedtranslationRestored=MTUOC_tags.reinsert_wordalign(SOURCETAGSTOK,selectedalignment,selectedtranslationPre)
                    elif preprocess_type=="Custom":
                        #no tag restoration for custom preprocessing
                        selectedtranslationRestored=selectedtranslationPre
                    else:
                        selectedtranslationRestored=selectedtranslationPre
                        
                except:
                    print("ERROR RESTORING:",sys.exc_info())
            else:
                selectedtranslationRestored=selectedtranslationPre
            
            
            if preprocess_type=="SentencePiece":
                selectedtranslation=MTUOC_process_segment_SP.from_MT(selectedtranslationRestored,sp_joiner,bos_annotate,eos_annotate)
            elif preprocess_type=="NMT":
                    selectedtranslation=MTUOC_process_segment_NMT.from_MT(selectedtranslationRestored,detokenizer, joiner, bos_annotate, eos_annotate)
            elif preprocess_type=="SMT":
                segmentnotags=remove_tags(segment)
                selectedtranslation=MTUOC_process_segment_SMT.from_MT(selectedtranslationRestored,segmentnotags,tokenizer)
            elif preprocess_type=="Custom":
                stemp=codecs.open("segmentpost.tmp","w",encoding="utf-8")
                stemp.write(selectedtranslationRestored+"\n")
                stemp.close()
                os.system(postprocess_command)
                stemp=codecs.open("segmenttrad.tmp","r",encoding="utf-8")
                selectedtranslation=stemp.readline().rstrip()
                stemp.close()
            selectedtranslation=MTUOC_tags.fix_markup_ws(segment,selectedtranslation)
            
            if MTUOCServer_verbose:print("Translation No Tags: ",selectedtranslationPre)
            if MTUOCServer_verbose:print("Translation Tags: ",selectedtranslationRestored)
            if MTUOCServer_verbose:print("Word Alignment: ",selectedalignment)
            
            if MTUOCServer_restore_tags:
                for clau in equiltag.keys():
                    if equiltag[clau] in existingtags:
                        selectedtranslation=selectedtranslation.replace(clau,equiltag[clau])
                    else:
                        selectedtranslation=selectedtranslation.replace(clau,"")
            elif preprocess_type=="SMT":
                    selectedtranslation=MTUOC_process_segment_SMT.from_MT(selectedtranslation,segment,tokenizer)
            if toLower:
                selectedtranslation=selectedtranslation.upper()
                
            #restoring leading and trailing spaces
            lSP=leading_spaces*" "
            tSP=trailing_spaces*" "
            #restoring URLs and EMAILs
            if MTUOCServer_URLs:
                selectedtranslation=restore_URLs(selectedtranslation,equilURLs)
            if MTUOCServer_EMAILs:
                selectedtranslation=restore_EMAILs(selectedtranslation,equilEMAILs)
            selectedtranslation=lSP+selectedtranslation.strip()+tSP
            if MTUOCServer_verbose:print("Translation: ",selectedtranslation)
            if not post_script=="None":
                stemp=codecs.open("segmentpost.tmp","w",encoding="utf-8")
                stemp.write(selectedtranslation+"\n")
                stemp.close()
                os.system(post_script)
                stemp=codecs.open("segmenttrad.tmp","r",encoding="utf-8")
                selectedtranslation=stemp.readline().rstrip()
                stemp.close()
                
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
MTUOCServer_URLs=config["MTUOCServer"]["URLs"]
MTUOCServer_EMAILs=config["MTUOCServer"]["EMAILs"]
MTUOCServer_port=config["MTUOCServer"]["port"]
MTUOCServer_type=config["MTUOCServer"]["type"]
MTUOCServer_MTengine=config["MTUOCServer"]["MTengine"]

pre_script=config["Preprocess"]["pre_script"]
post_script=config["Preprocess"]["post_script"]
preprocess_type=config["Preprocess"]["type"]
preprocess_command=config["Preprocess"]["preprocess_command"]
postprocess_command=config["Preprocess"]["postprocess_command"]

sllang=config["Preprocess"]["sl_lang"]
tllang=config["Preprocess"]["tl_lang"]
MTUOCtokenizer=config["Preprocess"]["sl_tokenizer"]
MTUOCdetokenizer=config["Preprocess"]["tl_tokenizer"]

sp_model_SL=config["Preprocess"]["sp_model_SL"]
sp_vocabulary_SL=config["Preprocess"]["sp_vocabulary_SL"]
sp_vocabulary_threshold=config["Preprocess"]["sp_vocabulary_threshold"]
Preprocess_tcmodel=config["Preprocess"]["tcmodel"]
Preprocess_bpecodes=config["Preprocess"]["bpecodes"]
joiner=config["Preprocess"]["joiner"]
bos_annotate=config["Preprocess"]["bos_annotate"]
eos_annotate=config["Preprocess"]["eos_annotate"]
sp_joiner=config["Preprocess"]["sp_joiner"]


if not MTUOCServer_MTengine=="ModernMT" and preprocess_type=="SentencePiece":
    TOKENIZERA=MTUOCtokenizer
    SPMODEL=sp_model_SL
    SPVOCABULARY=sp_vocabulary_SL
    VOCTHR=sp_vocabulary_threshold
    tokenizerA=importlib.import_module(TOKENIZERA)
    if SPVOCABULARY=="None" or VOCTHR=="None":
        tokenizerB=pyonmttok.Tokenizer("space", spacer_annotate=True, segment_numbers=True, sp_model_path=SPMODEL)
    else:
        tokenizerB=pyonmttok.Tokenizer("none", spacer_annotate=True, segment_numbers=True, sp_model_path=SPMODEL, vocabulary_path=SPVOCABULARY, vocabulary_threshold=VOCTHR)
    if not Preprocess_tcmodel==None:
        tcmodel=load_model(Preprocess_tcmodel)
    else:
        tcmodel=None
        
elif not MTUOCServer_MTengine=="ModernMT" and reprocess_type=="NMT":
    tokenizer = importlib.import_module(MTUOCtokenizer,"tokenize")
    TOKENIZERA=MTUOCtokenizer
    tokenizerA=importlib.import_module(TOKENIZERA)
    detokenizer = importlib.import_module(MTUOCdetokenizer,"detokenize")
    if MTUOCServer_verbose:print("Loading TC Model.")    
    tcmodel=load_model(Preprocess_tcmodel)
    if MTUOCServer_verbose:print("Loading BPE")
    bpeobject=load_codes(Preprocess_bpecodes)
    
elif not MTUOCServer_MTengine=="ModernMT" and preprocess_type=="SMT":
    tokenizer = importlib.import_module(MTUOCtokenizer,"tokenize")
    TOKENIZERA=MTUOCtokenizer
    tokenizerA=importlib.import_module(TOKENIZERA)
    detokenizer = importlib.import_module(MTUOCdetokenizer,"detokenize")
    if MTUOCServer_verbose:print("Loading TC Model.")    
    tcmodel=load_model(Preprocess_tcmodel)

    

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
            
elif MTUOCServer_MTengine=="OpenNMT":
    import requests
    url = "http://"+MTEngineIP+":"+str(MTEnginePort)+"/translator/translate"
    headers = {'content-type': 'application/json'}

elif MTUOCServer_MTengine=="Moses":
    proxyMoses = xmlrpc.client.ServerProxy("http://"+MTEngineIP+":"+str(MTEnginePort)+"/RPC2")
    
elif MTUOCServer_MTengine=="ModernMT":
    import requests
    
    


#STARTING MTUOC SERVER

if MTUOCServer_type=="MTUOC":
    from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
    
    class MTUOC_server(WebSocket):
        def handleMessage(self):
            if MTUOCServer_verbose:print("Translating: ",self.data)
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

elif MTUOCServer_type=="OpenNMT":
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
                ts=translate_segment(ss)
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

elif MTUOCServer_type=="NMTWizard":
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
                targettext=translate_segment(sourcetext)
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
    
elif MTUOCServer_type=="ModernMT":
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
                translation=translate_segment(segment)
                out['data']['translation']=translation
            except:
                out['status'] = STATUS_ERROR
            return jsonify(out)
        ip=get_IP_info()
        app.run(debug=True, host=ip, port=MTUOCServer_port, use_reloader=False,
                threaded=True)
    start()
    
elif MTUOCServer_type=="Moses":
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
        

