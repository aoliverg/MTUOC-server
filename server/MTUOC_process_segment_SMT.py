import importlib
import sys


import MTUOC_truecaser as truecaser
import MTUOC_detruecaser as detruecaser
from MTUOC_replacenumbers import replace
from MTUOC_restorenumbers import restore

def adapt_output(segment, joiner, bos_annotate=True, eos_annotate=True):
    if bos_annotate:
        segment="<s> "+segment
    if eos_annotate:
        segment=segment+" </s>"
    return(segment)

def to_MT(segment, tokenizer, tcmodel):
    segmenttok=tokenizer.tokenize(segment)
    segmenttrue=truecaser.truecase(tcmodel,tokenizer,segmenttok)
    segmentreplacenum=replace(segmenttrue)
    return(segmentreplacenum)
    
def from_MT(segment, source, tokenizer):
    segmenttrue = restore(segment,source)
    segmenttok = detruecaser.detruecase(segmenttrue)
    segment= tokenizer.detokenize(segmenttok)
    segment=segment.strip()
    return(segment)
    
    
    
