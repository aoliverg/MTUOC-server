import config
from MTUOC_misc import printLOG

import json
import requests
import ast
import xmltodict

def Lucy_translate(slsegment):
    try:
        slsegment="[@àéèíóòú@]. "+slsegment
        url = config.Lucy_url 
        headers = {'Content-Type': 'application/json'}
        body = {"inputParams": {"param": [{"@name": "TRANSLATION_DIRECTION", "@value": config.Lucy_TRANSLATION_DIRECTION},{"@name": "MARK_UNKNOWNS", "@value": config.Lucy_MARK_UNKNOWNS},{"@name": "MARK_ALTERNATIVES", "@value": config.Lucy_MARK_ALTERNATIVES},{"@name": "MARK_COMPOUNDS", "@value": config.Lucy_MARK_COMPOUNDS}, {"@name": "INPUT", "@value": slsegment},{"@name": "CHARSET","@value":config.Lucy_CHARSET}]}}
        encoded_body = json.dumps(body)
        traduccio_xml=requests.post(url = url, auth=('traductor', 'traductor'), headers=headers, data=encoded_body).text
        response_dict = ast.literal_eval(json.dumps(xmltodict.parse(traduccio_xml)))
        translation=response_dict["task"]["outputParams"]["param"][0]['@value']
        translation=translation.replace("[@àéèíóòú@]. ","")
    except:
        printLOG(1,"ERROR Lucy:",sys.exc_info())
    return(translation)
  