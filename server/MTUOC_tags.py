#    MTUOC_tags
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

import os
import lxml
import lxml.etree as ET
import io
import re
import html

def protect_tags(segment):
    protectedsegment=re.sub(r'(<[^>]+>)', r'｟\1｠',segment)
    return(protectedsegment)

def reinsert_wordalign(sourceTAGStok,WordAlignment,targetNOTAGStok,splitter=""):
    (sourceTAGStoktrad,equiltags,equilattr)=translate_tags(sourceTAGStok)
    with open("temp_sourceTAGStok.txt", "w") as text_file:
        print(sourceTAGStoktrad, file=text_file)
    with open("temp_WordAlignment.txt", "w") as text_file:
        print(WordAlignment, file=text_file)
    with open("temp_targetNOTAGStok.txt", "w") as text_file:
        print(targetNOTAGStok, file=text_file)
    command="perl reinsert_worldalign.pm temp_sourceTAGStok.txt temp_WordAlignment.txt < temp_targetNOTAGStok.txt > temp_targetTAGStok.txt"
    os.system(command)
    with open("temp_targetTAGStok.txt","r") as text_file:
        targetTAGStoktrad=text_file.readline().strip()
    if not splitter=="":
        targetTAGStoktrad=targetTAGStoktrad.replace("<g",splitter+"<g").replace("</g>",splitter+"</g>")
        
    
    targetTAGStok=detranslate_tags(targetTAGStoktrad,equiltags,equilattr)
    return(targetTAGStok)
    
def fix_markup_ws(segment,trad):
    tags=re.findall('(<[^>]+>)', segment)
    for tag in tags:
        tag1=tag+" "
        tag2=" "+tag
        if segment.find(tag)>-1 and not segment.find(tag1)>-1 and trad.find(tag1)>-1:
            trad=trad.replace(tag1,tag)
        if segment.find(tag)>-1 and not segment.find(tag2)>-1 and trad.find(tag2)>-1:
            trad=trad.replace(tag2,tag)
    return(trad)
    
def translate_tags(segment):
    segment="<segmentorestore>"+segment+"</segmentorestore>"
    f = io.BytesIO(segment.encode('utf-8'))
    events = ("start", "end")
    context = ET.iterparse(f, events=events,recover=True)
    cont_g=-1
    equiltags={}
    equilattr={}
    for event, elem in context:
        if event=="end" and not elem.tag=="segmentorestore" and not elem.tag=="s":
            cont_g+=1
            elem_tag=elem.tag
            elem_attr=elem.items()
            equiltags[cont_g]=elem_tag
            equilattr[cont_g]=elem_attr
            elem.tag="g"
            elem.set('id',str(cont_g))
            elem.tag="g"
            elem.set('id',str(cont_g))
    root=context.root
    segmentTR=ET.tostring(root).decode("utf-8").replace("<segmentorestore>","").replace("</segmentorestore>","")
    segmentTR=segmentTR.replace("&#9601;","▁")
    segmentTR=segmentTR.replace("▁<g","<g").replace("▁</g>","</g>")
    return(html.unescape(segmentTR),equiltags,equilattr)
    
def detranslate_tags(targetTAGStrad,equiltags,equilattr):
    if len(equiltags)==0:
        return(targetTAGStrad)
    segmentTRmod="<segmentorestore>"+targetTAGStrad+"</segmentorestore>"
    f = io.BytesIO(segmentTRmod.encode('utf-8'))
    events = ("start", "end")
    context = ET.iterparse(f, events=events,recover=True)
    cont_g=-1
    for event, elem in context:
        if event=="end" and elem.tag=="g" and not elem.tag=="segmentorestore":
            cont_g+=1
            elem.tag=equiltags[cont_g]
            elem.attrib.clear()
            for equil in equilattr[cont_g]:
                elem.attrib[equil[0]]=equil[1]
    root=context.root            
    segmentTRREC=ET.tostring(root).decode("utf-8").replace("<segmentorestore>","").replace("</segmentorestore>","")
    segmentTRREC=segmentTRREC.replace("&#9601;","▁")
    return(html.unescape(segmentTRREC))

def remove_tags(segment):
    segmentnotags=re.sub('(<[^>]+>)', "",segment)
    segmentnotags=re.sub('({[0-9]+})', "",segmentnotags)
    return(segmentnotags)
    
def has_tags(segment):
    result=False
    tags=re.findall('(<[^>]+>)', segment)
    if len(tags)>0:
        result=True
    return(result)
    
if __name__ == "__main__":
    for line in sys.stdin:
        line=line.strip()
        reline=remove(line)
        print(reline)


