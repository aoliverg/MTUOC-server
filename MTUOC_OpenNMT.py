#    MTUOC_OpenNMT
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


import requests
import time
import sys
import config

from MTUOC_misc import printLOG


def connect_to_OpenNMT():
    config.urlOpenNMT = "http://"+config.MTEngineIP+":"+str(config.MTEnginePort)+"/translator/translate"
    config.headersOpenNMT = {'content-type': 'application/json'}
    
    
def translate_segment_OpenNMT(segmentPre):
    translation_candidates={}
    translation_candidates["segmentNOTAGSPre"]=segmentPre
    params = [{ "src" : segmentPre}]
    response = requests.post(config.urlOpenNMT, json=params, headers=config.headersOpenNMT)
    target = response.json()
    selectedtranslationPre=target[0][0]["tgt"]
    if "align" in target[0][0]:
        selectedalignments=target[0][0]["align"][0]
    else:
        selectedalignments=""
    translation_candidates["translationNOTAGSPre"]=[selectedtranslationPre]
    translation_candidates["alignments"]=[selectedalignments]
    return(translation_candidates)
