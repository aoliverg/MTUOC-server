#    MTUOC-server v 6
#    Description: an MTUOC server using Sentence Piece as preprocessing step
#    Copyright (C) 2023  Antoni Oliver
#    v. 11/09/2023
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

import os
import sys
import asyncio
import websockets
import argparse
import codecs
import csv

import srx_segmenter


from websocket import create_connection
import socket
import time
import asyncio
import websockets

import config

from MTUOC_misc import printLOG
from MTUOC_misc import get_IP_info

from MTUOC_Marian import connect_to_Marian
from MTUOC_Marian import translate_segment_Marian

from MTUOC_OpenNMT import connect_to_OpenNMT
from MTUOC_OpenNMT import translate_segment_OpenNMT

from MTUOC_Moses import connect_to_Moses
from MTUOC_Moses import translate_segment_Moses

from MTUOC_typeMTUOC import start_MTUOC_server
from MTUOC_typeMoses import start_Moses_server
from MTUOC_typeOpenNMT import start_OpenNMT_server
from MTUOC_typeNMTWizard import start_NMTWizard_server
from MTUOC_typeModernMT import start_ModernMT_server




from MTUOC_tags import TagRestorer


###YAML IMPORTS
import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def startMTEngine():
    printLOG(3,"START MT ENGINE:", config.startMTEngineCommand)
    os.system(config.startMTEngineCommand)   


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
configYAML=yaml.load(stream, Loader=yaml.FullLoader)

config.MTUOCServer_MTengine=configYAML["MTEngine"]["MTengine"]
config.MTUOCServer_type=configYAML["MTUOCServer"]["type"]
config.MTUOCServer_port=configYAML["MTUOCServer"]["port"]
config.tag_restoration=configYAML["MTUOCServer"]["restore_tags"]
config.fix_xml=configYAML["MTUOCServer"]["fix_xml"]

config.MTUOCServer_URLs=configYAML["MTUOCServer"]["URLs"]
config.MTUOCServer_EMAILs=configYAML["MTUOCServer"]["EMAILs"]

config.code_URLs=configYAML["MTUOCServer"]["code_URLs"]
config.code_EMAILs=configYAML["MTUOCServer"]["code_EMAILs"]

config.min_chars_segment=configYAML["MTUOCServer"]["min_chars_segment"]
translation_selection_strategy=configYAML["MTUOCServer"]["translation_selection_strategy"]

config.segment_input=configYAML["Preprocess"]["segment_input"]
config.SRXfile=configYAML["Preprocess"]["SRXfile"]
config.SRXlang=configYAML["Preprocess"]["SRXlang"]

config.rules = srx_segmenter.parse(config.SRXfile)

config.sllang=configYAML["Preprocess"]["sl_lang"]
config.tllang=configYAML["Preprocess"]["tl_lang"]
config.tokenize_SL=configYAML["Preprocess"]["tokenize_SL"]
config.tokenizerSL=configYAML["Preprocess"]["sl_tokenizer"]
tokenizerSLfile=config.tokenizerSL
config.tokenizerTL=configYAML["Preprocess"]["tl_tokenizer"]
if config.tokenizerSL=="None": config.tokenizerSL=None
if config.tokenizerTL=="None": config.tokenizerTL=None

if config.tokenizerSL=="Moses":
    config.tokenizerSLType="Moses"
    import mosestokenizer
    config.tokenizerSL = mosestokenizer.MosesTokenizer(config.sllang)
    config.tokenizerSLType="Moses"
elif not config.tokenizerSL==None:
    config.tokenizerSLType="MTUOC"
    import importlib.util
    if not config.tokenizerSL.endswith(".py"): config.tokenizerSL=MTUOCtokenizerSL+".py"
    spec = importlib.util.spec_from_file_location('', config.tokenizerSL)
    tokenizerSLmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tokenizerSLmod)
    config.tokenizerSL=tokenizerSLmod.Tokenizer()
    
else:
    config.tokenizerSL=None
    
if config.tokenizerTL=="Moses":
    import mosestokenizer
    config.tokenizerTL = mosestokenizer.MosesTokenizer(config.tllang)
    config.tokenizerTLType="Moses"
elif not config.tokenizerTL==None:
    import importlib.util
    if not config.tokenizerTL.endswith(".py"): config.tokenizerTL=tokenizerTL+".py"
    spec = importlib.util.spec_from_file_location('', config.tokenizerTL)
    tokenizerTLmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tokenizerTLmod)
    config.tokenizerTL=tokenizerTLmod.Tokenizer()
else:
    config.tokenizerTL=None
    
    

config.tcmodel=configYAML["Preprocess"]["tcmodel"]
config.truecase=configYAML["Preprocess"]["truecase"]

if config.tcmodel=="None": config.tcmodel=None
if config.tcmodel:
    from MTUOC_truecaser import Truecaser
    config.truecaser=Truecaser(tokenizer=tokenizerSLfile,tc_model=config.tcmodel)
else:
    config.truecaser=None

config.unescape_html_input=configYAML["unescape_html_input"]
config.escape_html_input=configYAML["escape_html_input"]

config.checkistranslatable=configYAML["MTUOCServer"]["checkistranslatable"]

config.change_input_files=configYAML["change_input_files"].split(";")
config.changes_input=[]
if not config.change_input_files[0]=="None":
    for ci in config.change_input_files:
        with open(ci) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for row in csvreader:
                config.changes_input.append(row)

config.change_output_files=configYAML["change_output_files"].split(";")
config.changes_output=[]
if not config.change_output_files[0]=="None":
    for co in config.change_output_files:
        with open(co) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for row in csvreader:
                config.changes_output.append(row)

config.change_translation_files=configYAML["change_translation_files"].split(";")
config.changes_translation=[]
if not config.change_translation_files[0]=="None":
    for change_list in config.change_translation_files:
        with open(change_list) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for row in csvreader:
                config.changes_translation.append(row)


config.tagrestorer=TagRestorer()



#sentencepiece
config.sentencepiece=configYAML["Preprocess"]["sentencepiece"]
config.spmodelSL=configYAML["Preprocess"]["sp_model_SL"]
config.spmodelTL=configYAML["Preprocess"]["sp_model_TL"]
config.sp_splitter=configYAML["Preprocess"]["sp_splitter"]

#BPE

#BPE

config.BPE=configYAML["Preprocess"]["BPE"]
config.bpecodes=configYAML["Preprocess"]["bpecodes"]
config.bpe_joiner=configYAML["Preprocess"]["bpe_joiner"]
if config.BPE:
    from subword_nmt import apply_bpe
    config.bpeobject=apply_bpe.BPE(open(config.bpecodes,encoding="utf-8"))
#bos and eos annotate
config.bos_annotate=configYAML["Preprocess"]["bos_annotate"]
config.bos_symbol=configYAML["Preprocess"]["bos_symbol"]
config.eos_annotate=configYAML["Preprocess"]["eos_annotate"]
config.eos_symbol=configYAML["Preprocess"]["eos_symbol"]

config.pre_replace_NUMs=configYAML["Preprocess"]["replaceNUMs"]
config.code_NUMs=configYAML["Preprocess"]["code_NUMs"]
config.pre_split_NUMs=configYAML["Preprocess"]["splitNUMs"]

if config.sentencepiece:
    import sentencepiece as spm
    config.spSL= spm.SentencePieceProcessor(model_file=config.spmodelSL, out_type=str, add_bos=config.bos_annotate, add_eos=config.eos_annotate)
    config.spTL= spm.SentencePieceProcessor(model_file=config.spmodelTL, out_type=str)


if config.MTUOCServer_MTengine in ["Marian","Moses","OpenNMT"]:
    config.startMTEngineV=configYAML["MTEngine"]["startMTEngine"]
    config.startMTEngineCommand=configYAML["MTEngine"]["startCommand"]
    config.MTEngineIP=configYAML["MTEngine"]["IP"]
    config.MTEnginePort=configYAML["MTEngine"]["port"]
    config.min_len_factor=configYAML["MTEngine"]["min_len_factor"]

if config.MTUOCServer_MTengine=="GoogleTranslate":    
    config.Google_sllang=configYAML["GoogleTranslate"]["sllang"]
    config.Google_tllang=configYAML["GoogleTranslate"]["tllang"]
    config.Google_glossary=configYAML["GoogleTranslate"]["glossary"]
    if config.Google_glossary=="None": config.Google_glossary=None
    #state None if no glossary is used, otherwise the name of the glossary
    config.Google_project_id=configYAML["GoogleTranslate"]["project_id"]
    config.Google_location=configYAML["GoogleTranslate"]["location"]
    config.Google_jsonfile=configYAML["GoogleTranslate"]["jsonfile"]
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.Google_jsonfile
    config.client = translateGoogle.TranslationServiceClient()
    config.client = translateGoogle.TranslationServiceClient()
    config.parent = "projects/"+config.Google_project_id+"/locations/"+config.Google_location
    
if config.MTUOCServer_MTengine=="DeepL":
    config.DeepL_API_key=configYAML["DeepL"]["API_key"]
    config.DeepL_sl_lang=configYAML["DeepL"]["sllang"]
    config.DeepL_tl_lang=configYAML["DeepL"]["tllang"]
      #tag_handling: html
      #one of html, xml
    config.DeepL_formality=configYAML["DeepL"]["formality"]
      #one of default, less, more
    config.DeepL_split_sentences=configYAML["DeepL"]["split_sentences"]
      #one of off, on, nonewlines
    config.DeepL_glossary=configYAML["DeepL"]["glossary"]
    if config.DeepL_glossary=="None": config.DeepL_glossary=None
    config.DeepLtranslator = deepl.Translator(config.DeepL_API_key)

if config.MTUOCServer_MTengine=="Lucy":
    ###Lucy imports
    import ast
    import xmltodict
    import requests
    config.Lucy_url=configYAML["Lucy"]["url"]
    config.Lucy_TRANSLATION_DIRECTION=configYAML["Lucy"]["TRANSLATION_DIRECTION"]
    config.Lucy_MARK_UNKNOWNS=configYAML["Lucy"]["MARK_UNKNOWNS"]
    config.Lucy_MARK_ALTERNATIVES=configYAML["Lucy"]["MARK_ALTERNATIVES"]
    config.Lucy_MARK_COMPOUNDS=configYAML["Lucy"]["MARK_COMPOUNDS"]
    config.Lucy_CHARSET=configYAML["Lucy"]["CHARSET"]

config.verbosity_level=int(configYAML["MTUOCServer"]["verbosity_level"])
config.log_file=configYAML["MTUOCServer"]["log_file"]

config.MTUOCServer_ONMT_url_root=configYAML["MTUOCServer"]["ONMT_url_root"]

if config.log_file=="None":
    config.log_file=False
else:
    config.sortidalog=codecs.open(config.log_file,"a",encoding="utf-8")
    config.log_file=True
    
if config.startMTEngineV and not config.MTUOCServer_MTengine in ["GoogleTranslate","DeepL","Lucy"]:
    startMTEngine()
    
if config.MTUOCServer_MTengine=="Marian":
    connect_to_Marian()
elif config.MTUOCServer_MTengine=="Moses":
    config.proxyMoses=connect_to_Moses()

if config.MTUOCServer_type=="MTUOC":
    start_MTUOC_server()
elif config.MTUOCServer_type=="Moses":
    start_Moses_server()
elif config.MTUOCServer_type=="OpenNMT":
    start_OpenNMT_server()
elif config.MTUOCServer_type=="NMTWizard":
    start_NMTWizard_server()
elif config.MTUOCServer_type=="ModernMT":
    start_ModernMT_server()
