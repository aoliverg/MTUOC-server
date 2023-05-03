import config
from MTUOC_misc import printLOG
import regex as rx
import re
import html

def remove_control_characters(cadena):
    return rx.sub(r'\p{C}', '', cadena)
    
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
    for xifra in xifres:
        xifrastr=str(xifra)
        xifrasplit=xifra.split()
        xifra2=joiner.join(xifra)
        segment=segment.replace(xifra,xifra2)
    return(segment)

def preprocess_segment(segment):
    if config.escape_html_input:
        segment=html.escape(segment)
    if config.unescape_html_input:
        segment=html.unescape(segment)
    segment=remove_control_characters(segment) 
    hastags=config.tagrestorer.has_tags(segment)
    originaltags=config.tagrestorer.get_tags(segment)
    printLOG(3,"HAS TAGS",hastags)
    printLOG(3,"TAGS",originaltags)
    #leading and trailing spaces
    config.leading_spaces=len(segment)-len(segment.lstrip())
    config.trailing_spaces=len(segment)-len(segment.rstrip())-1
    segment=segment.lstrip().rstrip()
    if config.pre_replace_NUMs:
        segment=replace_NUMs(segment)
    if config.pre_split_NUMs:
        segment=splitnumbers(segment)
    if config.sentencepiece:
        try:
            segmentPre=" ".join(config.spSL.encode(segment))
        except:
            printLOG(1,"ERROR preprocess segment:",sys.exc_info())
    else:
        segmentPre=segment
    return(segmentPre)
    
def postprocess_segment(segmentPre):
    try:
        if config.sentencepiece:
            segmentPost=config.spTL.decode(segmentPre.split())
    except:
            printLOG(1,"ERROR preprocess segment:",sys.exc_info())
    return(segmentPost)
    
def tokenizationSL(segment):
    if config.tokenize_SL and not config.tokenizerSL==None:
        tokens=config.tokenizerSL.tokenize(segment)
    else:
        tokens=segment   
    return(tokens)
        
def tokenizationTL(segment):
    if config.tokenize_TL and not config.tokenizerTL==None:
        tokens=config.tokenizerTL.tokenize(segment)
    else:
        tokens=segment  
    return(tokens)

def detokenizationSL(tokens):
    if not config.tokenizerSL==None:
        segment=config.tokenizerSL.detokenize(tokens)
    else:
        segment=tokens   
    return(tokens)
        
def detokenizationTL(tokens):
    if not config.tokenizerTL==None:
        segment=config.tokenizerL.detokenize(tokens)
    else:
        segment=tokens   
    return(tokens)