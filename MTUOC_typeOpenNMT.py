import sys
from flask import Flask, jsonify, request

from MTUOC_misc import get_IP_info
from MTUOC_misc import printLOG
import config

from MTUOC_translate import translate_para

def start_OpenNMT_server():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    printLOG(1,"MTUOC server started as OpenNMT server")
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
        def translateONMT():
            inputs = request.get_json(force=True)
            inputs0=inputs[0]
            out = {}
            try:
                out = [[]]
                ss=inputs0['src']
                ts=translate_para(ss)
                response = {"src": ss, "tgt": ts,
                                "n_best": 0, "pred_score": 0}
                    
                out[0].append(response)
            except:
                out['error'] = "Error"
                out['status'] = STATUS_ERROR

            return jsonify(out)
            
        
        from waitress import serve
        serve(app, host=host, port=port,threads= 1)    
        #app.run(debug=debug, host=host, port=port, use_reloader=False,threaded=True)
    url_root=config.MTUOCServer_ONMT_url_root
    ip="0.0.0.0"
    ip=get_IP_info()
    debug="store_true"
    
    print("MTUOC server IP:   ", ip)
    print("MTUOC server port: ", MTUOCServer_port)
    print("MTUOC server type:  OpenNMT")
    
    start(url_root=url_root, host=ip, port=MTUOCServer_port,debug=debug)