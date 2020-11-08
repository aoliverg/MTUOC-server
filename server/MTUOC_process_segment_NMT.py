import importlib
import sys

import MTUOC_truecaser as truecaser
import MTUOC_detruecaser as detruecaser
from MTUOC_BPE import apply_BPE
from MTUOC_BPE import deapply_BPE



def adapt_output(segment, joiner, bos_annotate=True, eos_annotate=True):
    if bos_annotate:
        segment="<s> "+segment
    if eos_annotate:
        segment=segment+" </s>"
    return(segment)


def to_MT(segment, tokenizer, tcmodel, bpeobject, joiner="￭", bos_annotate=True, eos_annotate=True):
    segmenttok=tokenizer.tokenize(segment)
    segmenttrue=truecaser.truecase(tcmodel,tokenizer,segmenttok)
    if bpeobject:
        segmentBPE=apply_BPE(bpeobject,segmenttrue)
    else:
        segmentBPE=segmenttrue
    segmentBPE=adapt_output(segmentBPE, bos_annotate, eos_annotate)
    return(segmentBPE)
    

def from_MT(segment, tokenizer, joiner="￭", bos_annotate=True, eos_annotate=True):
    if bos_annotate: segment=segment.replace("<s>","")
    if eos_annotate: segment=segment.replace("</s>","")
    segmentNOBPE=deapply_BPE(segment,joiner)
    segmenttok = detruecaser.detruecase(segmentNOBPE)
    segment= tokenizer.detokenize(segmenttok)
    segment=segment.strip()
    return(segment)
    
    
    
