#    MTUOC_Moses
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


import time
import config

from MTUOC_misc import printLOG


def connect_to_Moses():
    import xmlrpc.client
    error=True
    while error:
        try:
            proxyMoses = xmlrpc.client.ServerProxy("http://"+config.MTEngineIP+":"+str(config.MTEnginePort)+"/RPC2")
            error=False
            printLOG(1,"Connection with Moses Server created","")
        except:
            printLOG(1,"Error: waiting for Moses server to start. Retrying in 2 seconds.","")
            time.sleep(2)
            error=True
    return(proxyMoses)
    
def translateAliMoses(aliBRUT):
    newali=[]
    for a in aliBRUT:
        at=str(a['source-word'])+"-"+str(a['target-word'])
        newali.append(at)
    newali=" ".join(newali)

    return(newali)
    
def translate_segment_Moses(segmentPre):
    param = {"text": segmentPre}
    result = config.proxyMoses.translate(param)
    translation_candidates={}
    translation_candidates["translationNOTAGSPre"]=[]
    translation_candidates["alignments"]=[]
    if "nbest" in result:
        print("NBEST")
    else:
        print("UN SOL RESULTAT")
        translationREP=result['text']
        alignmentBRUT=result['word-align']
        alignments=translateAliMoses(alignmentBRUT)
        translation_candidates["translationNOTAGSPre"].append(translationREP)
        translation_candidates["alignments"].append(alignments)
        
    
    return(translation_candidates)
    
'''
translation_candidates["translationNOTAGSPre"]=[]
    translation_candidates["alignments"]=[]
    for tca in tc_aux:
        try:
            segmentaux=tca.split(" ||| ")[1].strip()
            alignmentaux=tca.split(" ||| ")[2].strip()
            translation_candidates["translationNOTAGSPre"].append(segmentaux)
            translation_candidates["alignments"].append(alignmentaux)
        except:
            pass
'''