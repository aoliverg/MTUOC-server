import sys
from flask import Flask, jsonify, request, make_response

from MTUOC_misc import get_IP_info
from MTUOC_misc import printLOG
import config

from MTUOC_translate import translate_para

def start_MTUOC_server():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    printLOG(1,config.verbosity_level,"MTUOC server started using MTUOC protocol")
    STATUS_ERROR = "error"
    out={}
    def start(url_root="./translator",
              host="0.0.0.0",
              port=5000,
              debug=True):
        def prefix_route(route_function, prefix='', mask='{0}{1}'):
            def newroute(route, *args, **kwargs):
                return route_function(mask.format(prefix, route), *args, **kwargs)
            return newroute

        app = Flask(__name__)
        app.route = prefix_route(app.route, url_root)

        @app.route('/translate', methods=['POST'])
        def translateMTUOC():
            try:
                body = request.get_json()
                ts=translate_para(body["src"])
                jsonObject = {
                    "id": body["id"],
                    "src": body["src"],
                    
                    "tgt": ts # Call MTUOC
                }
                printLOG(0,config.verbosity_level,jsonObject)
                return jsonify(jsonObject)
            except:
                return make_response("Server Error", 500)
        
        from waitress import serve
        serve(app, host=host, port=port,threads= 1)    
        #app.run(debug=debug, host=host, port=port, use_reloader=False,threaded=True)
    url_root="/"
    ip="0.0.0.0"
    ip=get_IP_info()
    debug="store_true"
    
    print("MTUOC server IP:   ", ip)
    print("MTUOC server port: ", config.MTUOCServer_port)
    print("MTUOC server type:  MTUOC")
    
    start(url_root=url_root, host=ip, port=config.MTUOCServer_port,debug=debug)