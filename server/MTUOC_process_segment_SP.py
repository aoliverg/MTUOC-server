import pyonmttok
import MTUOC_truecaser as truecaser
import MTUOC_detruecaser as detruecaser

def to_MT(segment, tokenizerA, tokenizerB, tcmodel, bos, eos):
    segment=segment.strip()
    if not tcmodel==None:
        segmenttok=tokenizerA.tokenize(segment)
        segmenttrue=truecaser.truecase(tcmodel,tokenizerA,segmenttok)
    else:
        segmenttrue=segment
    segmentp=tokenizerA.protect(segmenttrue)
    output=""
    if not bos=="None":
        output=bos+" "
    output+=tokenizerA.unprotect(" ".join(tokenizerB.tokenize(segmentp)[0]))
    if not eos=="None":
        output+=" "+eos
    return(output)


def from_MT(segment, tokenizer, joiner="▁",bos="None", eos="None"):
    if not bos=="None":
        segment=segment.replace(bos,"")
    if not eos=="None":
        segment=segment.replace(eos,"")
    segment=segment.replace(" ","")
    segment=segment.replace(joiner," ")
    segment=segment.strip()
    segmenttrue=detruecaser.detruecase(segment)
    segmentdetok=tokenizer.detokenize(segmenttrue)
    return(segmentdetok)
    
    
    
