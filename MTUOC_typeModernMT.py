import sys
from flask import Flask, jsonify, request

from MTUOC_misc import get_IP_info
from MTUOC_misc import printLOG
import config

from MTUOC_translate import translate_para

def start_ModernMT_server():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    printLOG(1,"MTUOC server started as ModernMT server")
    def start(
              url_root="",
              host="",
              port=config.MTUOCServer_port,
              debug=True):
        def prefix_route(route_function, prefix='', mask='{0}{1}'):
            def newroute(route, *args, **kwargs):
                return route_function(mask.format(prefix, route), *args, **kwargs)
            return newroute
        app = Flask(__name__)
        app.route = prefix_route(app.route, url_root)
        @app.route('/translate', methods=['GET'])
        def translateModernMT():
            out = {}
            try:
                out['data']={}
                segment=request.args['q']
                translation=translate_para(segment)
                out['data']['translation']=translation
            except:
                out['status'] = STATUS_ERROR
            return jsonify(out)
        #ip=get_IP_info()
        #app.run(debug=True, host=ip, port=MTUOCServer_port, use_reloader=False, threaded=True)
    #start()
        from waitress import serve
        serve(app, host=host, port=port,threads= 8)    
        #app.run(debug=debug, host=host, port=port, use_reloader=False,threaded=True)
    url_root="/"
    ip="0.0.0.0"
    ip=get_IP_info()
    debug="store_true"
    
    print("MTUOC server IP:   ", ip)
    print("MTUOC server port: ", config.MTUOCServer_port)
    print("MTUOC server type:  ModernMT")
    
    start(url_root=url_root, host=ip, port=config.MTUOCServer_port,debug=debug)
