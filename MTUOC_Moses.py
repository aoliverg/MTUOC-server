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
    print("***translate_segment_Moses",segmentPre)
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
        
    
    print("***translation_candidates",translation_candidates)
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