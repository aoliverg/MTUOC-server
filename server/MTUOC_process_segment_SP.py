import pyonmttok


def to_MT(segment, tokenizerA, tokenizerB):
    segment=segment.strip()
    segmentp=tokenizerA.protect(segment)
    output="<s> "+tokenizerA.unprotect(" ".join(tokenizerB.tokenize(segmentp)[0]))+" </s>"
    return(output)


def from_MT(segment):
    segment=segment.replace("<s>","")
    segment=segment.replace("</s>","")
    segment=segment.replace(" ","")
    segment=segment.replace("▁"," ")
    segment=segment.strip()
    return(segment)
    
    
    
