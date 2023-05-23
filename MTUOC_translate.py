#    MTUOC_translate
#    Copyright (C) 2023  Antoni Oliver
#    v. 23/05/2023
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

import config
import sys
import re
import string as stringmodule


import srx_segmenter

from MTUOC_misc import printLOG
from MTUOC_GoogleTranslate import Google_translate
from MTUOC_DeepL import DeepL_translate
from MTUOC_Lucy import Lucy_translate
from MTUOC_Marian import translate_segment_Marian
from MTUOC_Moses import translate_segment_Moses

from MTUOC_preprocess import preprocess_segment
from MTUOC_preprocess import postprocess_segment

from MTUOC_preprocess import tokenizationSL
from MTUOC_preprocess import tokenizationTL
from MTUOC_preprocess import detokenizationSL
from MTUOC_preprocess import detokenizationTL

def segmenta(cadena):
    segmenter = srx_segmenter.SrxSegmenter(config.rules[config.SRXlang],cadena)
    segments=segmenter.extract()
    resposta=[]
    return(segments)
    
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
    for EMAIL in EMAILs:
        string=string.replace(EMAIL,code)
    return(string)

def replace_URLs(string,code="@URL@"):
    URLs=findURLs(string)
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

def splitnumbers(segment,joiner=""):
    joiner=joiner+" "
    xifres = re.findall(re_num,segment)
    equil={}
    for xifra in xifres:
        xifrastr=str(xifra)
        xifrasplit=xifra.split()
        xifra2=joiner.join(xifra)
        segment=segment.replace(xifra,xifra2)
        if xifra2.find(" ")>-1:
            equil[xifra2]=xifra
    return(segment,equil)
    
def desplitnumbers(segment,equil):
    for xifra2 in equil:
        segment=segment.replace(xifra2,equil[xifra2])
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
 

def translate_para(paragraph):
    if config.segment_input:
        (segments,separators)=segmenta(paragraph)
        translations=[]
        for segment in segments:
            translation=translate_segment(segment)
            if config.fix_xml:
                translation=config.tagrestorer.fix_xml_tags(translation)
            translations.append(translation)
        resultat=[]
        for i in range(0,len(separators)):
            resultat.append(separators[i])
            try:
                resultat.append(translations[i])
            except:
                pass
        
        
            
        translation="".join(resultat)
        
    else:
        translation=translate_segment(paragraph)
        
    return(translation)
        
        


def restore_tags_translation_candidates(translation_candidates):
    hastags=config.tagrestorer.has_tags(translation_candidates["segmentTAGS"])
    if hastags:
        
        (translation_candidates["segmentTAGS"],equil)=config.tagrestorer.replace_tags(translation_candidates["segmentOrig"])
        printLOG(3,"replace_tags",translation_candidates["segmentTAGS"])
        printLOG(3,"equil",equil)
        (translation_candidates["segmentTAGS"],tagInici,tagFinal)=config.tagrestorer.remove_start_end_tag(translation_candidates["segmentOrig"])
        printLOG(3,"remove_start_end_tag",translation_candidates["segmentTAGS"])
        printLOG(3,"TAG initial:",tagInici)
        printLOG(3,"TAG final:",tagFinal)
        translation_candidates["segmentNOTAGS"]=config.tagrestorer.remove_tags(translation_candidates["segmentTAGS"])
        originaltags=config.tagrestorer.get_tags(translation_candidates["segmentTAGS"])
        segmentNOTAGSTOK=tokenizationSL(translation_candidates["segmentNOTAGS"])
        segmentTAGSTOK=tokenizationSL(translation_candidates["segmentPreTAGS"])
        translation_candidates["translationTAGS"]=[None] * len(translation_candidates["translationNOTAGSPre"])
        for i in range(0,len(translation_candidates["translationNOTAGSPre"])):
            try:
                if hastags and config.tag_restoration:
                    try:
                        alignment=translation_candidates["alignments"][i]
                        translationNOTAGSTOK=tokenizationTL(translation_candidates["translationNOTAGSPre"][i])
                        translation_candidates["translationTAGS"][i]=config.tagrestorer.restore_tags(segmentNOTAGSTOK, segmentTAGSTOK, alignment, translationNOTAGSTOK)
                        '''
                        if tagInici:
                            translation_candidates["translationTAGS"][i]=tagInici+translation_candidates["translationTAGS"][i]
                        if tagFinal:
                            translation_candidates["translationTAGS"][i]=translation_candidates["translationTAGS"][i]+tagFinal
                        printLOG(3,"SELECTED TRANSLATION SIMPLE TAGS",translation_candidates["translationTAGS"][i])
                        for t in equil:
                            translation_candidates["translationTAGS"][i]=translation_candidates["translationTAGS"][i].replace(t,equil[t],1)
                        '''
                    except:
                        printLOG(3,"ERROR restoring tags:",sys.exc_info())
                        translation_candidates["translationTAGS"][i]=translationNOTAGSTOK
                
                else:
                    translation_candidates["translationTAGS"]=translation_candidates["translationNOTAGSPre"]
                    printLOG(3,"translationTAGS:",translation_candidates["translationTAGS"][i])
                    
                    
                
            except:
                pass
    else:
        translation_candidates["segmentNOTAGS"]=translation_candidates["segmentTAGS"]
        translation_candidates["translationTAGS"]=translation_candidates["translationNOTAGSPre"]

    
    
    
    return(translation_candidates)

    
def translate_segment(segment):
    printLOG(3,"translate_segment",segment)
    if config.MTUOCServer_MTengine=="GoogleTranslate":
        translation=Google_translate(segment)
        return(translation)
    elif config.MTUOCServer_MTengine=="DeepL":
        translation=DeepL_translate(segment)
        return(translation)
    elif config.MTUOCServer_MTengine=="Lucy":
        translation=Lucy_translate(segment)
        return(translation)
    segmentOrig=segment
    if not config.change_input_files[0]=="None":
        printLOG(3,"CHANGES INPUT:")
        printLOG(3,"ORIGINAL:",segmentOrig)
        for change in config.changes_input:
            tofind=change[0]
            tochange=change[1]
            regexp="\\b"+tofind+"\\b"
            trobat=re.findall(regexp,segment)
            if trobat:    
                segment=re.sub(regexp, tochange, segment)
                printLOG(3,tofind,tochange)
        printLOG(3,"CHANGED:",segment)
    hastags=config.tagrestorer.has_tags(segment)
    originaltags=config.tagrestorer.get_tags(segment)
    printLOG(3,"hastags",hastags)
    printLOG(3,"originaltags",originaltags)
    #truecasing
    totruecase=False
    toupperfinal=False
    if not config.truecase==None and config.truecase=="all": totruecase=True
    segmentnotags=config.tagrestorer.remove_tags(segment)
    if not config.truecase==None and config.truecase in ["upper","all"] and segmentnotags.isupper() and not segment=="@URL@" and not segment=="@EMAIL@": 
        totruecase=True
        toupperfinal=True
        
    if totruecase:        
        segment=config.truecaser.truecase(segment)
    if config.tokenize_SL:
        segment=config.tokenizerSL.tokenize(segment)
    if hastags:
        segmentTAGS=segment
        
        (segmentTAGS,equil)=config.tagrestorer.replace_tags(segmentTAGS)
        printLOG(3,"segmentTAGS:",segmentTAGS)
        printLOG(3,"equil:",equil)
        printLOG(3,"segmentTAGS:",segmentTAGS)
        (segmentTAGS,tagInici,tagFinal)=config.tagrestorer.remove_start_end_tag(segmentTAGS)
        printLOG(3,"TAG initial:",tagInici)
        printLOG(3,"TAG final:",tagFinal)
        
        
        segmentNOTAGS=config.tagrestorer.remove_tags(segment)
    else:
        segmentTAGS=segment
        segmentNOTAGS=segment
    
    if len(segmentNOTAGS)<config.min_chars_segment:
        return(segment)
        
    if config.checkistranslatable:
        segmentNOTAGS=replace_URLs(segmentNOTAGS,config.code_URLs)
        segmentNOTAGS=replace_EMAILs(segmentNOTAGS,config.code_EMAILs)
        tokens=tokenizationSL(segmentNOTAGS)
        printLOG(3,"Check is translatable:",is_translatable(tokens))
        if not is_translatable(tokens):                
            return(segment)
    
    if config.MTUOCServer_EMAILs:
        segmentTAGS=replace_EMAILs(segmentTAGS)
        segmentNOTAGS=replace_EMAILs(segmentNOTAGS)
        printLOG(3,"Replace EMAILs:",segmentTAGS)
    if config.MTUOCServer_URLs:
        segmentTAGS=replace_URLs(segmentTAGS)
        segmentNOTAGS=replace_URLs(segmentNOTAGS)
        printLOG(3,"Replace URLs:",segmentTAGS)
        
    if config.pre_replace_NUMs:
        segmentTAGS=replace_NUMs(segmentTAGS,code=config.code_NUMs)
        segmentNOTAGS=replace_NUMs(segmentNOTAGS,code=config.code_NUMs)
        printLOG(3,"Replace NUMs:",segmentTAGS)
    if config.pre_split_NUMs:
        (segmentTAGS,equilSplitNum)=splitnumbers(segmentTAGS) 
        (segmentNOTAGS,equilSplitNum2)=splitnumbers(segmentNOTAGS)  
        printLOG(3,"Split NUMs:",segmentTAGS)        
    
    
    #leading and trailing spaces
    leading_spaces=len(segment)-len(segment.lstrip())
    trailing_spaces=len(segment)-len(segment.rstrip())-1
    segmentPre=preprocess_segment(segmentNOTAGS)  
    printLOG(3,"segmentPre:",segmentPre) 
    segmentPreTAGS=preprocess_segment(segmentTAGS)     
    printLOG(3,"segmentPreTAGS:",segmentPreTAGS) 
    if config.MTUOCServer_MTengine=="Marian":
        translation_candidates=translate_segment_Marian(segmentPre)
    elif config.MTUOCServer_MTengine=="Moses":
        translation_candidates=translate_segment_Moses(segmentPre)
        
    translation_candidates["segment"]=segment
    translation_candidates["segmentOrig"]=segmentOrig
    translation_candidates["segmentTAGS"]=segmentTAGS
    translation_candidates["segmentPre"]=segmentPre
    translation_candidates["segmentPreTAGS"]=segmentPreTAGS
    translation_candidates["segmentNOTAGS"]=segmentNOTAGS
    if hastags:
        translation_candidates=restore_tags_translation_candidates(translation_candidates)  
        
    else:
        translation_candidates["translationTAGS"]=translation_candidates["translationNOTAGSPre"]
       
    for i in range(0,len(translation_candidates["translationNOTAGSPre"])):
        translation_candidates["translationTAGS"][i]=postprocess_segment(translation_candidates["translationTAGS"][i])
        
        if hastags:
            if tagInici:
                translation_candidates["translationTAGS"][i]=tagInici+translation_candidates["translationTAGS"][i]
            if tagFinal:
                translation_candidates["translationTAGS"][i]=translation_candidates["translationTAGS"][i]+tagFinal
            for t in equil:
                translation_candidates["translationTAGS"][i]=translation_candidates["translationTAGS"][i].replace(t,equil[t],1)
            if not config.truecaser==None and is_first_letter_upper(segmentOrig):    
                translation_candidates["translationTAGS"][i]=upper_case_first_letter(translation_candidates["translationTAGS"][i])
        if toupperfinal: 
            translation_candidates["translationTAGS"][i]=translation_candidates["translationTAGS"][i].upper()
            ###LOWERCASE UPPERCASED TAGS
            hastagstranslation=config.tagrestorer.has_tags(translation_candidates["translationTAGS"][i])
            if hastagstranslation:
                translationtags=config.tagrestorer.get_tags(translation_candidates["translationTAGS"][i])
                for tt in translationtags:
                    if not tt in originaltags and tt.lower() in originaltags:
                        translation_candidates["translationTAGS"][i]=translation_candidates["translationTAGS"][i].replace(tt,tt.lower())
        
        if config.MTUOCServer_EMAILs:
            translation_candidates["translationTAGS"][i]=restore_EMAILs(segmentOrig,translation_candidates["translationTAGS"][i],code=config.code_EMAILs)
        if config.MTUOCServer_URLs:
            translation_candidates["translationTAGS"][i]=restore_URLs(segmentOrig,translation_candidates["translationTAGS"][i],code=config.code_URLs)
        '''    
        #config.pre_replace_NUMs
        if config.pre_replace_NUMs:
            translation_candidates["translationTAGS"][i]=restore_NUMs(segmentOrig,translation_candidates["translationTAGS"][i],code=config.code_NUMs)
        #config.pre_split_NUMs
        if config.pre_split_NUMs:
            translation_candidates["translationTAGS"][i]=desplitnumbers(translation_candidates["translationTAGS"][i],equilSplitNum)
        #detruecase
        if totruecase:
            translation_candidates["translationTAGS"][i]=translation_candidates["translationTAGS"][i][0].upper()+translation_candidates["translationTAGS"][i][1:]
        #detokenize
        if config.tokenizeSL and not config.tokenizerTL==None:
            translation_candidates["translationTAGS"][i]=config.tokenizerTL.detokenize(translation_candidates["translationTAGS"][i])
            
        '''
        
                
        translation_candidates["translationTAGS"][i]=config.tagrestorer.repairSpacesTags(translation_candidates["segmentOrig"],translation_candidates["translationTAGS"][i]) 
        printLOG(3,"SELECTED TRANSLATION REAL TAGS",translation_candidates["translationTAGS"][i])
    best_translation=select_best_candidate(translation_candidates,config.translation_selection_strategy)
    translation=best_translation
    
    if not config.change_output_files[0]=="None":
        printLOG(3,"CHANGES OUTPUT:")
        printLOG(3,"ORIGINAL:",translation)
        for change in config.changes_output:
            tofind=change[0]
            tochange=change[1]
            regexp="\\b"+tofind+"\\b"
            trobat=re.findall(regexp,translation)
            if trobat: 
                translation=re.sub(regexp, tochange, translation)
                printLOG(3,tofind,tochange)
        printLOG(3,"CHANGED:",translation)
    
    if not config.change_translation_files[0]=="None":
        printLOG(3,"CHANGES TRANSLATION:")
        printLOG(3,"ORIGINAL SOURCE:",segmentOrig)
        printLOG(3,"ORIGINAL TARGET:",translation)
        for change in config.changes_translation:
            tofindSOURCE=change[0]
            tofindTARGET=change[1]
            tochange=change[2]
            regexpSOURCE="\\b"+tofindSOURCE+"\\b"
            regexpTARGET="\\b"+tofindTARGET+"\\b"
            trobatSOURCE=re.findall(regexpSOURCE,segmentOrig)
            trobatTARGET=re.findall(regexpTARGET,translation)
            if trobatSOURCE and trobatTARGET: 
                translation=re.sub(regexpTARGET, tochange, translation)
                printLOG(3,tofindTARGET,tochange)
        printLOG(3,"CHANGED TARGET:",translation)
    return(translation)

def is_translatable(tokens):
    tokens=tokens.split(" ")
    translatable=False
    for token in tokens:
        if token.isalpha():
            translatable=True
            break
    return(translatable)        

def select_best_candidate(translation_candidates,strategy):
    '''To implement several strategies to select the best candidate. Now it r,eturns the first one.'''
    if strategy=="First":
        best_translation=translation_candidates["translationTAGS"][0]
    return(best_translation)

    

  
