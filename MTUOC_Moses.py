
from MTUOC_misc import printLOG


def connect_to_Moses():
    import xmlrpc.client
    error=True
    while error:
        try:
            proxyMoses = xmlrpc.client.ServerProxy("http://"+MTEngineIP+":"+str(MTEnginePort)+"/RPC2")
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
    result = proxyMoses.translate(param)
    print(result)
    translationREP=result['text']
    alignmentBRUT=result['word-align']
    alignments=translateAliMoses(alignmentBRUT)
    return(translationREP, alignments) 