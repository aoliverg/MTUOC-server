#    MTUOC-server v 5
#    Description: an MTUOC server using Sentence Piece as preprocessing step
#    Copyright (C) 2022  Antoni Oliver
#    v. 4/10/2022
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
import importlib.util
import codecs
import xmlrpc.client
import json
import pickle
import sentencepiece as spm
from subword_nmt import apply_bpe
import collections

import lxml

import html

import csv

import argparse

import re
import regex as rx

import string as stringmodule


###YAML IMPORTS
import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def is_first_letter_upper(segment):
    for character in segment:
        if character.isalpha() and character.isupper():
            return(True)
        elif character.isalpha() and character.islower():
            return(False)
    return(False)

def upper_case_first_letter(segment):
    pos=0
    for character in segment:
        if character.isalpha() and character.islower():
            llista=list(segment)
            llista[pos]=llista[pos].upper()
            segment="".join(llista)
            return(segment)
        elif character.isalpha() and character.isupper():
            return(segment)
        pos+=1
    return(segment)    

def printLOG(vlevel,m1,m2=""):
    cadena=str(datetime.now())+"\t"+str(m1)+"\t"+str(m2)
    if vlevel<=verbosity_level:
        print(cadena)
        if log_file:
            sortidalog.write(cadena+"\n")


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

###BPE subword-nmt
def processBPE(bpeobject,segment):
    segmentBPE=bpeobject.process_line(segment)
    return(segmentBPE)
    
def deprocessBPE(segment, joiner="@@"):
    regex = r"(" + re.escape(joiner) + " )|("+ re.escape(joiner) +" ?$)"
    segment=re.sub(regex, '', segment)
    regex = r"( " + re.escape(joiner) + ")|(^ $"+ re.escape(joiner) +")"
    segment=re.sub(regex, '', segment)
    return(segment)

###URLs EMAILs

def findEMAILs(string): 
    email=re.findall('\S+@\S+', string)
    email2=[]
    for em in email: 
        if em[-1] in stringmodule.punctuation: em=em[0:-1]
        email2.append(em)
    return email2
    
def findURLs(string): 
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)       
    return [x[0] for x in url] 

def replace_EMAILs(string,code="@EMAIL@"):
    EMAILs=findEMAILs(string)
    cont=0
    for EMAIL in EMAILs:
        string=string.replace(EMAIL,code)
    return(string)

def replace_URLs(string,code="@URL@"):
    URLs=findURLs(string)
    cont=0
    for URL in URLs:
        string=string.replace(URL,code)
    return(string)
    
re_num = re.compile(r'[\d,\.]+')

def replace_NUMs(segment,code="@NUM@"):
    trobatsEXPRNUM=re.finditer(re_num,segment)
    for trobat in trobatsEXPRNUM:
        if not trobat.group(0) in [".",","]:
            segment=segment.replace(trobat.group(0),code,1)
    return(segment)
    
def restore_EMAILs(stringA,stringB,code="@EMAIL@"):
    EMAILs=findEMAILs(stringA)
    for email in EMAILs:
        stringB=stringB.replace(code,email,1)
    return(stringB)
    
def restore_URLs(stringA,stringB,code="@URL@"):
    URLs=findURLs(stringA)
    for url in URLs:
        stringB=stringB.replace(code,url,1)
    return(stringB)
    
def restore_NUMs(segmentSL,segmentTL,code="@NUM@"):
    trobatsEXPRNUM=re.finditer(re_num,segmentSL)
    position=0
    for trobat in trobatsEXPRNUM:
        if not trobat.group(0) in [".",","]:
            segmentTL=segmentTL.replace(code,trobat.group(0),1)
    return(segmentTL)


def startMTEngine():
    printLOG(1,"Starting MT engine...")
    os.system(startMTEngineCommand)

def stopMTEngine():
    try:
        stopcommand2="fuser -k "+str(MTEnginePort)+"/tcp"
        os.system(stopcommand2)
        printLOG(1,"MT Engine stopped.")
    except:
        printLOG(1,"Unable to stop MT Engine",sys.exc_info())
    
def connect_to_Marian():
    from websocket import create_connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        conn=s.connect_ex((MTEngineIP, MTEnginePort))
        if conn == 0:marianstarted=True
    service="ws://"+MTEngineIP+":"+str(MTEnginePort)+"/translate"
    error=True
    while error:
        try:
            ws = create_connection(service)
            printLOG(1,"Connection with Marian Server created","")
            error=False
        except:
            printLOG(1,"Error: waiting for Marian server to start. Retrying in 2 seconds.","")
            time.sleep(2)
            error=True
    return(ws)

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

    printLOG(3,"Selected translation from Marian:",selectedtranslationPre)
    printLOG(3,"Selected alignment from Marian:",selectedalignment)
    return(selectedtranslationPre, selectedalignment)
    
def translate_segment_OpenNMT(segmentPre):
    params = [{ "src" : segmentPre}]

    response = requests.post(url, json=params, headers=headers)
    target = response.json()
    selectedtranslationPre=target[0][0]["tgt"]
    if "align" in target[0][0]:
        selectedalignments=target[0][0]["align"][0]
    else:
        selectedalignments=""
    return(selectedtranslationPre, selectedalignments)

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

def translate(segment):
    #function for Moses server
    translation=translate_segment(segment['text'])
    translationdict={}
    translationdict["text"]=translation
    return(translationdict)    

def pseudotokenizetags(segment):
    tags = re.findall(r'</?.+?/?>', segment)
    segmentmod=segment
    for tag in tags:        
        tagmod=" "+tag+" "
        segmentmod=segmentmod.replace(tag,tagmod)
    segmentmod=" ".join(segmentmod.split())    
    return(segmentmod)
    
def remove_control_characters(cadena):
    return rx.sub(r'\p{C}', '', cadena)

re_num = re.compile(r'[\d,.\-/]+')

def splitnumbers(segment,joiner=""):
    joiner=joiner+" "
    xifres = re.findall(re_num,segment)
    for xifra in xifres:
        xifrastr=str(xifra)
        xifrasplit=xifra.split()
        xifra2=joiner.join(xifra)
        segment=segment.replace(xifra,xifra2)
    return(segment)

def verify_length(llista,maxlength):
    correct=True
    for s in llista:
        if len(s)>maxlength:
            correct=False
            break
    return(correct)

def translate_segment(segment):
    #leading and trailing spaces
    leading_spaces=len(segment)-len(segment.lstrip())
    trailing_spaces=len(segment)-len(segment.rstrip())-1
    segmentOrig=segment
    if len(segment)>max_chars_segment:
        segmentL=[segment]
        for sp in segment_splitters:
            newsegmentL=[]
            for element in segmentL:
                if len(element)>max_chars_segment and element.find(sp)>-1:
                    elementSplitted=element.split(sp)
                    numelem=len(elementSplitted)
                    contelem=1
                    for eS in elementSplitted:
                        if contelem<numelem:
                            newsegmentL.append(eS+sp)
                        else:
                            newsegmentL.append(eS)
                        contelem+=1
                else:
                    newsegmentL.append(element)
            
            segmentL=newsegmentL
            correctparts=verify_length(segmentL,max_chars_segment)
            if correctparts:
                break
        translationL=[]
        for segment in segmentL:
            translation=translate_segment_part(segment,ucfirst=False)
            translationL.append(translation)
        translation=" ".join(translationL)
    elif len(tagrestorer.remove_tags(segment).strip())==0:
        translation=segment
    else:
        translation=translate_segment_part(segment)
    if fix_xml:
        translation=tagrestorer.fix_xml_tags(translation)
    #change translation
    for ct in changes_translation:
        if segmentOrig.find(ct[0])>-1 and translation.find(ct[1])>-1:
            #regexp="\\b"+ct[1]+"\\b"
            translation=translation.replace(ct[1],ct[2])
            #translation=re.sub(regexp, ct[2], translation)
            
    translation=translation.strip()
    translation=leading_spaces*" "+translation+" "*trailing_spaces
        
    return(translation)

def translate_segment_part(segment,ucfirst=True):
    try:
        if escape_html_input:
            segment=html.escape(segment)
        if unescape_html_input:
            segment=html.unescape(segment)
        #clean unicode control characters
        segment=remove_control_characters(segment)
        segmentORI=segment
        if not change_input_files[0]=="None":
            for change in changes_input:
                tofind=change[0]
                tochange=change[1]
                if segment.find(tofind)>-1:
                    regexp="\\b"+tofind+"\\b"
                    segment=re.sub(regexp, tochange, segment)
        printLOG(2,"------------------------------------------")        
        printLOG(2,"Segment:",segment)
        hastags=tagrestorer.has_tags(segment)
        originaltags=tagrestorer.get_tags(segment)
        printLOG(3,"HAS TAGS",hastags)
        #leading and trailing spaces
        leading_spaces=len(segment)-len(segment.lstrip())
        trailing_spaces=len(segment)-len(segment.rstrip())-1
        segment=segment.lstrip().rstrip()
        ###Pretractament dels tags
        if MTUOCServer_NUMs:
            segment=replace_NUMs(segment)
        if MTUOCServer_splitNUMs:
            segment=splitnumbers(segment)
        if hastags:
            segmentTAGS=segment
            equilG={}
            (segmentTAGS,equil)=tagrestorer.replace_tags(segmentTAGS)
            
            (segmentTAGS,tagInici,tagFinal)=tagrestorer.remove_start_end_tag(segmentTAGS)
            segmentNOTAGS=tagrestorer.remove_tags(segment)
        else:
            segmentTAGS=segment
            segmentNOTAGS=segment
            equilG={}
            equil={}
            tagInici=""
            tagFinal=""
        segmentTAGSrepair=segmentTAGS
        if len(segmentNOTAGS)<min_chars_segment:
            return(segment)
        toreturn=True 
        if checkisalpha:
            if not tokenizerSL==None:
                tokens=tokenizerSL.tokenize(segmentNOTAGS)
            else:
                tokens=segmentNOTAGS.split(" ")
            for token in tokens:
                if token.isalpha():
                    toreturn=False
                    break
            if toreturn:
                return(segment)
            
        
        if MTUOCServer_EMAILs:
            segmentTAGS=replace_EMAILs(segmentTAGS)
            segmentNOTAGS=replace_EMAILs(segmentNOTAGS)
        if MTUOCServer_URLs:
            segmentTAGS=replace_URLs(segmentTAGS)
            segmentNOTAGS=replace_URLs(segmentNOTAGS)
        

        for tag in equil:
            segmentTAGS=segmentTAGS.replace(tag," "+tag+" ")
        totruecase=False
        toupperfinal=False
        if not truecase==None and truecase=="all": totruecase=True
        if not truecase==None and truecase=="upper" and segmentNOTAGS.isupper(): 
            totruecase=True
            toupperfinal=True
                
        if totruecase:        
            segmentTAGS=truecaser.truecase(segmentTAGS)
            segmentNOTAGS=truecaser.truecase(segmentNOTAGS)
        
        if not tokenizerSL==None:
            segmentNOTAGSTOK=tokenizerSL.tokenize(segmentNOTAGS)
            segmentTAGSTOK=tokenizerSL.tokenize(segmentTAGS)
        
        if sentencepiece:
            segmentNOTAGSTOK=" ".join(sp.encode(segmentNOTAGS))
            segmentTAGSTOK=" ".join(sp.encode(segmentTAGS))
        if MTUOCServer_splitNUMs:
            segmentNOTAGSTOK=splitnumbers(segmentNOTAGSTOK)
            segmentTAGSTOK=splitnumbers(segmentTAGSTOK)
        printLOG(3,"segmentTAGS:",segmentTAGS)
        printLOG(3,"segmentNOTAGS:",segmentNOTAGS)
        printLOG(3,"equilG:",equilG)
        printLOG(3,"equil:",equil)
        printLOG(3,"segmentNOTAGSTOK:",segmentNOTAGSTOK)
        printLOG(3,"segmentTAGSTOK:",segmentTAGSTOK)
        
        if MTUOCServer_MTengine=="Marian":
            (translationNOTAGSTOK, alignment)=translate_segment_Marian(segmentNOTAGSTOK)
                
        
        elif MTUOCServer_MTengine=="Moses":
            (translationNOTAGSTOK, alignment)=translate_segment_Moses(segmentNOTAGSTOK)
        
        printLOG(3,"translationNOTAGSTOK:",translationNOTAGSTOK)
        printLOG(3,"alignment:",alignment)
        
        #####L'ERROR ESTÀ A PARTIR D'AQUI
        
        if hastags and MTUOCServer_restore_tags:
            translationTAGS=tagrestorer.restore_tags(segmentNOTAGSTOK, segmentTAGSTOK, alignment, translationNOTAGSTOK)
        else:
            translationTAGS=translationNOTAGSTOK
        printLOG(3,"translationTAGS:",translationTAGS)
        
        if not bos_annotate=="" and translationTAGS.startswith(bos_annotate+" "):translationTAGS=translationTAGS.replace(bos_annotate+" ","").strip()
        if not eos_annotate=="" and translationTAGS.endswith(" "+eos_annotate):translationTAGS=translationTAGS.replace(" "+eos_annotate,"").strip()
        printLOG(3,"SELECTED TRANSLATION SIMPLE TAGS",translationTAGS)
        if hastags:
            
            if sentencepiece:
                translationTAGS=sp.decode(translationTAGS.split())
            if not tokenizerTL==None and not tokenizerSL==None:
                translationTAGS=tokenizerSL.detokenize(translationTAGS)
            #Leading and trailing tags
            if tagInici:
                translationTAGS=tagInici+translationTAGS
            if tagFinal:
                translationTAGS=translationTAGS+tagFinal
            printLOG(3,"SELECTED TRANSLATION SIMPLE TAGS",translationTAGS)
            for t in equil:
                translationTAGS=translationTAGS.replace(t,equil[t],1)
            for t in equilG:
                translationTAGS=translationTAGS.replace(t,equilG[t],1)
            printLOG(3,"Translation Restored Real Tags:",translationTAGS)
            translation=tagrestorer.repairSpacesTags(segment,translationTAGS)
        else:
            if sentencepiece:
                translation=sp.decode(translationTAGS.split())
            if not tokenizerTL==None:
                translation=tokenizerTL.detokenize(translation)
            elif not tokenizerSL==None:
                translation=tokenizerSL.detokenize(translation)
        if MTUOCServer_NUMs:
            translation=restore_NUMs(segmentORI,translation)
        if MTUOCServer_EMAILs:
            translation=restore_EMAILs(segment,translation)
        if MTUOCServer_URLs:
            translation=restore_URLs(segment,translation)
        if not truecaser==None and is_first_letter_upper(segment):    
            translation=upper_case_first_letter(translation)
        if toupperfinal: 
            translation=translation.upper()
            ###LOWERCASE UPPERCASED TAGS
            hastagstranslation=tagrestorer.has_tags(translation)
            if hastagstranslation:
                translationtags=tagrestorer.get_tags(translation)
                for tt in translationtags:
                    if not tt in originaltags and tt.lower() in originaltags:
                        translation=translation.replace(tt,tt.lower())
        
    except:
        printLOG(1,"ERROR 001:",sys.exc_info())
        translation="#!#TRANSLATION ERROR#!#:"+str(sys.exc_info()[0])
    if not change_output_files[0]=="None":
        for change in changes_output:
            tofind=change[0]
            tochange=change[1]
            if translation.find(tofind)>-1:
                regexp="\\b"+tofind+"\\b"
                translation=re.sub(regexp, tochange, translation)
    translation=translation.strip()
    translation=leading_spaces*" "+translation+" "*trailing_spaces
    printLOG(2,"Translation:",translation)
    printLOG(2,"------------------------------------------")
    return(translation)  


#YAML

parser = argparse.ArgumentParser(description='MTUOC-server. With no arguments the config-server.yaml file will be used.')
parser.add_argument('-c','--config', action="store", dest="config", help='The server configuration file to be used.',required=False)
parser.add_argument('-p','--port', action="store", dest="port", type=int, help='The MTUOC server port.',required=False)
parser.add_argument('-t','--type', action="store", dest="type", help='The MTUOC server type.',required=False)


args = parser.parse_args()
if args.config:
    configfile=args.config
else:
    configfile="config-server.yaml"

stream = open(configfile, 'r',encoding="utf-8")
config=yaml.load(stream, Loader=yaml.FullLoader)

MTUOCServer_MTengine=config["MTEngine"]["MTengine"]
startMTEngineV=config["MTEngine"]["startMTEngine"]
startMTEngineCommand=config["MTEngine"]["startCommand"]
MTEngineIP=config["MTEngine"]["IP"]
MTEnginePort=config["MTEngine"]["port"]
min_len_factor=config["MTEngine"]["min_len_factor"]



    
MTUOCServer_port=config["MTUOCServer"]["port"]
MTUOCServer_type=config["MTUOCServer"]["type"]
verbosity_level=int(config["MTUOCServer"]["verbosity_level"])
log_file=config["MTUOCServer"]["log_file"]
if log_file=="None":
    log_file=False
else:
    sortidalog=codecs.open(log_file,"a",encoding="utf-8")
    log_file=True
MTUOCServer_restore_tags=config["MTUOCServer"]["restore_tags"]
fix_xml=config["MTUOCServer"]["fix_xml"]
strictTagRestoration=config["MTUOCServer"]["strictTagRestoration"]
MTUOCServer_restore_case=config["MTUOCServer"]["restore_case"]

MTUOCServer_URLs=config["MTUOCServer"]["URLs"]
MTUOCServer_EMAILs=config["MTUOCServer"]["EMAILs"]
MTUOCServer_NUMs=config["MTUOCServer"]["replaceNUMs"]
MTUOCServer_splitNUMs=config["MTUOCServer"]["splitNUMs"]

min_chars_segment=config["MTUOCServer"]["min_chars_segment"]
max_chars_segment=config["MTUOCServer"]["max_chars_segment"]
checkisalpha=config["MTUOCServer"]["checkisalpha"]
segment_splitters=config["MTUOCServer"]["segment_splitters"]
add_trailing_space=config["MTUOCServer"]["add_trailing_space"]

MTUOCServer_ONMT_url_root=config["MTUOCServer"]["ONMT_url_root"]

sllang=config["Preprocess"]["sl_lang"]
tllang=config["Preprocess"]["tl_lang"]
MTUOCtokenizerSL=config["Preprocess"]["sl_tokenizer"]
MTUOCtokenizerTL=config["Preprocess"]["tl_tokenizer"]
if MTUOCtokenizerSL=="None": MTUOCtokenizerSL=None
if MTUOCtokenizerTL=="None": MTUOCtokenizerTL=None
tcmodel=config["Preprocess"]["tcmodel"]
truecase=config["Preprocess"]["truecase"]
#sentencepiece
sentencepiece=config["Preprocess"]["sentencepiece"]
spmodel=config["Preprocess"]["sp_model_SL"]
sp_splitter=config["Preprocess"]["sp_splitter"]

#BPE subword-nmt
BPE=config["Preprocess"]["BPE"]
bpecodes=config["Preprocess"]["bpecodes"]
bpe_joiner=config["Preprocess"]["bpe_joiner"]

#bos and eos annotate
bos_annotate=config["Preprocess"]["bos_annotate"]
if bos_annotate=="None": bos_annotate=""
eos_annotate=config["Preprocess"]["eos_annotate"]
if eos_annotate=="None": eos_annotate=""

unescape_html_input=config["unescape_html_input"]
escape_html_input=config["escape_html_input"]

unescape_html_output=config["unescape_html_output"]
escape_html_output=config["escape_html_output"]

finaldetokenization=config["Preprocess"]["finaldetokenization"]

#Lucy server specific options
TRANSLATION_DIRECTION=config["Lucy"]["TRANSLATION_DIRECTION"]
USER=config["Lucy"]["USER"]
if tcmodel=="None": tcmodel=None
if tcmodel:
    from MTUOC_truecaser import Truecaser
    truecaser=Truecaser(tokenizer=MTUOCtokenizerSL,tc_model=tcmodel)
else:
    truecaser=None

change_input_files=config["change_input_files"].split(";")
changes_input=[]
if not change_input_files[0]=="None":
    for ci in change_input_files:
        with open(ci) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for row in csvreader:
                changes_input.append(row)
                
change_output_files=config["change_output_files"].split(";")
changes_output=[]
if not change_output_files[0]=="None":
    for co in change_output_files:
        with open(co) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for row in csvreader:
                changes_output.append(row)

change_translation_files=config["change_translation_files"].split(";")
changes_translation=[]
if not change_translation_files[0]=="None":
    for change_list in change_translation_files:
        with open(change_list) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for row in csvreader:
                changes_translation.append(row)

if startMTEngineV:
    startMTEngine()

if args.port:
    MTUOCServer_port=args.port
if args.type:
    MTUOCServer_type=args.type
if not MTUOCtokenizerSL==None:
    if not MTUOCtokenizerSL.endswith(".py"): MTUOCtokenizerSL=MTUOCtokenizerSL+".py"
    spec = importlib.util.spec_from_file_location('', MTUOCtokenizerSL)
    tokenizerSLmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tokenizerSLmod)
    tokenizerSL=tokenizerSLmod.Tokenizer()
else:
    tokenizerSL=None

if not MTUOCtokenizerTL==None:
    if not MTUOCtokenizerTL.endswith(".py"): MTUOCtokenizerTL=MTUOCtokenizerTL+".py"
    spec = importlib.util.spec_from_file_location('', MTUOCtokenizerTL)
    tokenizerTLmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tokenizerTLmod)
    tokenizerTL=tokenizerTLmod.Tokenizer()
else:
    tokenizerTL=None
    
from MTUOC_tags import TagRestorer
tagrestorer=TagRestorer()


###sentencepiece
if sentencepiece:
    sp= spm.SentencePieceProcessor(model_file=spmodel, out_type=str, add_bos=bos_annotate, add_eos=eos_annotate)
    sp2= spm.SentencePieceProcessor(model_file=spmodel, out_type=str)

elif BPE:
    bpeobject=apply_bpe.BPE(open(bpecodes,encoding="utf-8"),separator=bpe_joiner)
        

if MTUOCServer_MTengine=="Marian":
    ws=connect_to_Marian()
            
           
elif MTUOCServer_MTengine=="OpenNMT":
    import requests
    url = "http://"+MTEngineIP+":"+str(MTEnginePort)+"/translator/translate"
    headers = {'content-type': 'application/json'}

    
elif MTUOCServer_MTengine=="Moses":
    proxyMoses = xmlrpc.client.ServerProxy("http://"+MTEngineIP+":"+str(MTEnginePort)+"/RPC2")


    

if MTUOCServer_type=="MTUOC":
    from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
    class MTUOC_server(WebSocket):
        def handleMessage(self):
            self.translation=translate_segment(self.data)
            self.sendMessage(self.translation)

        def handleConnected(self):
            printLOG(1,'Connected to: ',self.address[0].split(":")[-1])

        def handleClose(self):
            printLOG(1,'Disconnected from: ',self.address[0].split(":")[-1])
    server = SimpleWebSocketServer('', MTUOCServer_port, MTUOC_server)
    ip=get_IP_info()
    cadena="MTUOC server IP: "+str(ip)+" port: "+str(MTUOCServer_port)
    printLOG(1,cadena)
    server.serveforever()
    
elif MTUOCServer_type=="MTUOC2":
    from flask import Flask, jsonify, request, make_response
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    printLOG(1,"MTUOC server started as MTUOC2 server")
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
        def translateMTUOC2():
            try:
                body = request.get_json()
                ts=translate_segment(body["src"])
                jsonObject = {
                    "id": body["id"],
                    "src": body["src"],
                    
                    "tgt": ts # Call MTUOC
                }
                return jsonify(jsonObject)
            except:
                return make_response("Server Error", 500)
            
        app.run(debug=debug, host=host, port=port, use_reloader=False,
            threaded=True)
    url_root="/"
    ip="0.0.0.0"
    ip=get_IP_info()
    debug="store_true"
    start(url_root=url_root, host=ip, port=MTUOCServer_port,debug=debug)

elif MTUOCServer_type=="OpenNMT":
    from flask import Flask, jsonify, request
    MTUOCServer_ONMT_url_root=config["MTUOCServer"]["ONMT_url_root"]
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    printLOG(1,"MTUOC server started as OpenNMT server")
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
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    printLOG(1,"MTUOC server started as NMTWizard server")
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
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    printLOG(1,"MTUOC server started as ModernMT server")
    def start(
              url_root="",
              host="",
              port=MTUOCServer_port,
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
        cadena="MTUOC server started as Moses server IP: "+str(ip)+" port: "+str(MTUOCServer_port)
        printLOG(1,cadena)
        print('\t\t\t\tUse Control-C to exit')
        server.serve_forever()
    except KeyboardInterrupt:
        printLOG(1,'Exiting')
        
elif MTUOCServer_type=="Lucy":
    from flask import Flask, jsonify, request
    from dicttoxml import dicttoxml
    MTUOCServer_ONMT_url_root=config["MTUOCServer"]["ONMT_url_root"]
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    printLOG(1,"MTUOC server started as Lucy server")
    STATUS_ERROR = "error"
    out={}
    def start(url_root="./AutoTranslateRS/V1.3",
              host="0.0.0.0",
              port=5000,
              debug=True):
        def prefix_route(route_function, prefix='', mask='{0}{1}'):
            def newroute(route, *args, **kwargs):
                return route_function(mask.format(prefix, route), *args, **kwargs)
            return newroute

        app = Flask(__name__)
        app.route = prefix_route(app.route, url_root)
        @app.route('/mtrans/exec/', methods=['POST'])
        def translateLucy():
            inputs = request.get_json(force=True)
            inputs0=inputs['inputParams']
            
            out = {}
            try:
                out = [[]]
                ss=inputs0['param'][4]['@value'].replace("[*áéíóúñ*] ","").lstrip()
                ts=translate_segment(ss)

                WORDS=len(ts.split())
                CHARACTERS=len(ts)
                INPUT=ss
                response_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><task><inputParams><param name="TRANSLATION_DIRECTION" value="'+TRANSLATION_DIRECTION+'"/><param name="MARK_UNKNOWNS" value="0"/><param name="MARK_ALTERNATIVES" value="0"/><param name="MARK_COMPOUNDS" value="0"/><param name="INPUT" value="'+str(INPUT)+'"/><param name="USER" value="'+USER+'"/></inputParams><outputParams><param name="OUTPUT" value="'+str(ts)+'"/><param name="MARK_UNKNOWNS" value="0"/><param name="MARK_ALTERNATIVES" value="0"/><param name="SENTENCES" value="1"/><param name="WORDS" value="'+str(WORDS)+'"/><param name="CHARACTERS" value="'+str(CHARACTERS)+'"/><param name="FORMAT" value="ASCII"/><param name="CHARSET" value="UTF"/><param name="SOURCE_ENCODING" value="UTF-8"/><param name="TARGET_ENCODING" value="UTF-8"/><param name="ERROR_MESSAGE" value=""/></outputParams></task>'
                out=response_xml
            except:
                out['error'] = "Error"
                out['status'] = STATUS_ERROR

            return out
            
        
        app.run(debug=debug, host=host, port=port, use_reloader=False,
            threaded=True)
    url_root=MTUOCServer_ONMT_url_root
    ip="0.0.0.0"
    ip=get_IP_info()
    debug="store_true"
    start(url_root="/AutoTranslateRS/V1.3", host=ip, port=MTUOCServer_port,debug=debug)

if MTUOCServer_type=="OpusMT":
    from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
    
    class OpusMT_server(WebSocket):
        def handleMessage(self):
            self.input=eval(self.data)
            self.translation=translate_segment(self.input['text'])
            self.data2 = {'result':  self.translation}
            self.jsondata=json.dumps(self.data2)
            self.sendMessage(self.jsondata)

        def handleConnected(self):
            printLOG(0,'Connected to: ',self.address[0].split(":")[-1])

        def handleClose(self):
            printLOG(0,'Disconnected from: ',self.address[0].split(":")[-1])
    server = SimpleWebSocketServer('', MTUOCServer_port, OpusMT_server)
    ip=get_IP_info()
    printLOG(1,"OpusMT server IP:",ip," port:",MTUOCServer_port)
    server.serveforever()
