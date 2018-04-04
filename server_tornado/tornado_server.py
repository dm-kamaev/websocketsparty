#-*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
from tornado_logging import log_event, log_msg
import tornado.websocket
from management import Connections
import json

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)

auth_client = {'fdskljfFASFJioASD': "Http1CServer"}


class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        try:
            clients_ws.event_client([clients_ws.clients['AstDom']['Object'], ], json.dumps({'Name': 'Monitor'}), '')
        except:
            pass
        clients_ws.monitor_ast['clients'] = clients_ws.clients
        clients_ws.monitor_ast['no_auth_clients'] = clients_ws.no_auth_clients
        clients_ws.monitor_ast.update(clients_ws.service)
        clients_ws.monitor_ast['groups'] = clients_ws.group
        self.render("monitor.html", **clients_ws.monitor_ast)


class MessageHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        param = self.request.headers.get('Authorization')
        auth = auth_client.get(param)
        if auth:
            try:
                self.set_header("Content-Type", "application/json")
                self.id = 'FromHTTP'
                message = tornado.escape.json_decode(self.request.body)
                clients_ws.send_message(self, message, from_http=True)
                self.finish()
            except Exception as e:
                self.set_status(500)
                self.write('Error %s' % e)
                self.finish()
        else:
            self.set_status(500)
            self.write('auth error')
            self.finish()




class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def open(self, *args):
        self.stream.set_nodelay(True)

    def on_message(self, message):
        clients_ws.routing_message(self, message)

    def on_close(self):
        clients_ws.del_ws(self)

    def check_origin(self, origin):
        return True

clients_ws = Connections()
app = tornado.web.Application([
    (r'/ws', WebSocketHandler),
])

app2 = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/message', MessageHandler),
])

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    app2.listen(8889)
    tornado.ioloop.IOLoop.instance().start()


