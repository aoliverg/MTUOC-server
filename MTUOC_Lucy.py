#    MTUOC_Lucy
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
  